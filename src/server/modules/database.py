"""
Interfaces with the Redis database, abstracting away its architectural details.

Authored by Haziq Hairil.
"""

import redis
import argon2
import string
import random
import dataclasses  # TODO: Remove this
import time
from datetime import date
from pathlib import Path
from typing import Optional
from .search import SearchClient
from .models import (
    Kitchen,
    User,
    Product,
    InventoryProduct,
    GroceryProduct,
    KitchensPageData,
    InventoryPageData,
    GroceryPageData,
    GroceryProductPageData,
)


def _gen_random_id(k=6) -> str:
    """
    Returns a randomly-generated string of k letters and digits.
    """
    sample_chars = string.ascii_letters + string.digits
    return "".join(random.choices(sample_chars, k=k))


class DatabaseClient:
    """
    Interfaces with the Redis database and, via
    `SearchClient`, the Meilisearch search engine.
    """

    def __init__(self, static_asset_dir: str, content_dir: str):
        """
        - `static_asset_dir` - The filepath of the directory containing static assets.
        - `content_dir` - The filepath of the directory containing runtime-generated data.
        """
        self._static_asset_dir = Path(static_asset_dir)
        self._content_dir = Path(content_dir)

        # Start the Redis client
        self._r = redis.Redis()
        self._rj = self._r.json()

        # Start the Meilisearch client
        self._search = SearchClient()

        # Password hasher to store passwords securely
        self._ph = argon2.PasswordHasher()

        # Write empty objects to Redis if they don't already exist
        self._rj.set("products", "$", {}, nx=True)
        self._rj.set("kitchens", "$", {}, nx=True)

    #### FILE ASSETS ####

    def get_static_asset(self, filepath: str, use_cache=True) -> Optional[bytes]:
        """
        Returns the contents of the specified file, or `None` if the file
        doesn't exist (and isn't cached). `filepath` is relative to the
        static asset directory specified during initialisation. This will
        read from disk if `use_cache` is `False`.
        """
        # Check the cache
        cache_key = "static:" + filepath
        cache = self._r.get(cache_key)

        # Return the cached data if we can
        if use_cache and cache is not None:
            return cache

        full_path = self._static_asset_dir / filepath

        # Return None if the file doesn't exist
        if not full_path.exists():
            return None

        # Read from disk and update the cache
        contents = full_path.read_bytes()
        self._r.set(cache_key, contents)

        return contents

    def get_product_image(self, kitchen_id: str, product_id: str) -> Optional[bytes]:
        """
        Returns the image of the specified product,
        or `None` if the image doesn't exist.
        """
        path_default = self._content_dir / f"default-images/{product_id}.jpg"
        path_custom = self._content_dir / f"kitchen-{kitchen_id}/{product_id}.jpg"

        if path_default.exists():
            # Return the image if it's in the default images folder
            return path_default.read_bytes()
        elif path_custom.exists():
            # Return the image if it's in the kitchen's image folder
            return path_custom.read_bytes()

        # The product doesn't exist
        return None

    #### DEFAULT PRODUCTS ####

    def create_default_product(
        self,
        name: str,
        category: str,
        barcodes: list[int],
        image: Optional[bytes] = None,
    ) -> str:
        """
        Creates a new default product in the database.
        Returns the generated ID of the product.
        """
        product_id = _gen_random_id()

        # Write the product data to the database
        self._rj.set(
            "products",
            f"$.{product_id}",
            {"name": name, "category": category},
        )

        # TODO: What if the barcode already exists in the database?
        if barcodes:
            self._r.hset("barcodes", mapping={str(b): product_id for b in barcodes})

        # Add this product to the search index
        self._search.index_default_products({product_id: name})

        # Write the product image to disk if there is one
        if image is not None:
            image_dir = self._content_dir / "default-images"
            # Create the default-images directory if it doesn't already exist
            image_dir.mkdir(exist_ok=True)
            # Write the image
            (image_dir / f"{product_id}.jpg").write_bytes(image)

        return product_id

    def drop_default_products(self):
        """
        Drops all default products from the database.
        For testing purposes only.
        """
        self._rj.clear("products")

    #### USER ACCOUNT MANAGEMENT ####

    def login_is_valid(self, email: str, password: str) -> bool:
        """
        Returns `True` if the user exists in the database
        and the password matches. Returns `False` otherwise.
        """
        if not self._r.exists(f"user:{email}"):
            # User does not exist
            return False

        # Get the hashed password
        hashed_pw = self._rj.get(f"user:{email}", "$.auth")[0]

        try:
            # User exists and password is correct
            return self._ph.verify(hashed_pw, password)
        except argon2.exceptions.VerifyMismatchError:
            # Password is incorrect
            return False

    def create_user(self, name: str, email: str, password: str) -> bool:
        """
        Creates a user in the database. Returns `False` if the user's email
        already exists in the database, and `True` otherwise. A return value
        of `True` can be taken to mean that the operation was successful.
        """
        if self._r.exists(f"user:{email}"):
            # User already exists
            return False

        # Write the user's account data to the database
        self._rj.set(
            f"user:{email}",
            "$",
            {
                "name": name,
                "auth": self._ph.hash(password),
                "owned-kitchens": [],
                "shared-kitchens": [],
            },
        )

        return True

    def get_user(self, email: str) -> User:
        """Returns the `User` with the specified email address."""
        username = self._rj.get(f"user:{email}", "$.name")[0]

        return User(email=email, username=username)

    def user_has_access_to_kitchen(self, email: str, kitchen_id: str) -> bool:
        """Returns whether the user has access to the specified kitchen."""
        # Whether the kitchen is owned by the user
        is_owned = (
            self._rj.arrindex(
                f"user:{email}",
                "$.owned-kitchens",
                kitchen_id,
            )
            # If the kitchen ID is present in the user's list
            # of owned kitchens, then the index shouldn't be -1
            != -1
        )

        # Whether the kitchen has been shared to the user
        is_shared = (
            self._rj.arrindex(
                f"user:{email}",
                "$.shared-kitchens",
                kitchen_id,
            )
            # If the kitchen ID is present in the user's list
            # of shared kitchens, then the index shouldn't be -1
            != -1
        )

        return is_owned or is_shared

    #### SESSION MANAGEMENT ####

    def create_session(self, email: str) -> str:
        """Creates and returns a session token for the specified user."""
        session_token = _gen_random_id()
        # Store the session in the database
        self._r.hset("sessions", session_token, email)

        return session_token

    def delete_session(self, session_token: str):
        """Removes the session token from the database."""
        self._r.hdel("sessions", session_token)

    def get_session_owner(self, session_token: str) -> Optional[str]:
        """
        Returns the email address of the user who owns the specified
        session token, or `None` if the session token is invalid.
        """
        # Email address of the session's owner
        email_bytes = self._r.hget("sessions", session_token)

        if email_bytes is None:
            # The session token doesn't exist (it is invalid)
            return None

        return email_bytes.decode()

    #### KITCHEN HANDLING ####

    def create_kitchen(self, email: str, kitchen_name: str) -> str:
        """
        Creates a new kitchen and assigns the indicated
        user as the owner. Returns the kitchen's ID.
        """
        kitchen_id = _gen_random_id()

        # Write the kitchen data to the database
        self._rj.set(
            "kitchens",
            f"$.{kitchen_id}",
            {
                "name": kitchen_name,
                "grocery": {},
                "inventory": {},
                "customProducts": {},
            },
        )
        self._rj.arrappend(f"user:{email}", "$.owned-kitchens", kitchen_id)

        return kitchen_id

    def rename_kitchen(self, kitchen_id: str, new_name: str):
        """Sets the name of the kitchen to `new_name`."""
        self._rj.set("kitchens", f"$.{kitchen_id}.name", new_name)

    def delete_kitchen(self, kitchen_id: str):
        """Deletes the kitchen from the database."""
        # TODO: Remember to delete the kitchen ID from users' owned-kitchens and shared-kitchens
        self._rj.delete("kitchens", f"$.{kitchen_id}")

    #### PRODUCT & LIST MANAGEMENT ####

    def _get_product_from_kitchen(self, kitchen_id: str, product_id: str) -> Product:
        """
        Checks if the specified product is in the kitchen's custom
        product list. Returns the product from the custom product
        list if it is, and from the default product list otherwise.
        """
        product_name_matches = self._rj.get("products", f"$.{product_id}.name")

        # Check the custom product list if this product isn't a default product
        if len(product_name_matches) == 0:
            product_name = self._rj.get(
                "kitchens",
                f"$.{kitchen_id}.customProducts.{product_id}",
            )[0]

            return Product(
                id=product_id,
                name=product_name,
                category="Custom product",
            )

        product_category = self._rj.get("products", f"$.{product_id}.category")[0]

        return Product(
            id=product_id,
            name=product_name_matches[0],
            category=product_category,
        )

    def _get_inventory_product(
        self,
        kitchen_id: str,
        product_id: str,
        expiry: int,
    ):
        """
        Returns the amount of the product present in the kitchen's inventory
        list, for instances where the product's expiry date is `expiry`.
        """
        amount_matches = self._rj.get(
            "kitchens",
            f"$.{kitchen_id}.inventory.{product_id}.{expiry}",
        )
        return amount_matches[0] if amount_matches else 0

    def _get_total_inventory_product(self, kitchen_id: str, product_id: str) -> int:
        """
        Returns the amount of the product present in the kitchen's inventory
        list, regardless of expiry date.
        """
        amount_matches = self._rj.get(
            "kitchens", f"$.{kitchen_id}.inventory.{product_id}.*"
        )
        return sum(amount_matches)

    def _set_inventory_product(
        self,
        kitchen_id: str,
        product_id: str,
        expiry: int,
        amount: int,
    ):
        """Updates the inventory list to have `amount` of the product."""
        # Delete the product from the inventory
        # list if we're setting the amount <= 0
        if amount <= 0:
            self._rj.delete(
                "kitchens",
                f"$.{kitchen_id}.inventory.{product_id}.{expiry}",
            )
            # Remove the product from the search index too
            self._search.delete_inventory_product(kitchen_id, product_id)
            return

        # Get the amount of this product already in the inventory list
        curr_total_amount = self._get_total_inventory_product(kitchen_id, product_id)

        # Check if the product is not already in the inventory list
        if curr_total_amount == 0:
            # Get the product data
            product = self._get_product_from_kitchen(kitchen_id, product_id)

            # Create an empty entry for the product in the inventory list
            self._rj.set(
                "kitchens",
                f"$.{kitchen_id}.inventory.{product_id}",
                {},
            )

            # Add the product to the corresponding search index
            self._search.index_inventory_products(
                kitchen_id,
                {product_id: product.name},
            )

        # Set the amount
        self._rj.set(
            "kitchens",
            f"$.{kitchen_id}.inventory.{product_id}.{expiry}",
            amount,
        )

    def get_grocery_product_amount(self, kitchen_id: str, product_id: str) -> int:
        """
        Returns the amount of the product
        present in the kitchen's grocery list.
        """
        amount_matches = self._rj.get(
            "kitchens",
            f"$.{kitchen_id}.grocery.{product_id}",
        )

        # If the grocery product entry doesn't exist
        # in the database then there must be 0 products
        return amount_matches[0] if amount_matches else 0

    def set_grocery_product(self, kitchen_id: str, product_id: str, amount: int):
        """
        Updates the grocery list to have `amount` of the specified
        product. If `amount` is negative, it will be treated as 0.
        """
        # Delete the product from the grocery
        # list if we're setting the amount <= 0
        if amount <= 0:
            self._rj.delete("kitchens", f"$.{kitchen_id}.grocery.{product_id}")
            # Remove the product from the search index too
            self._search.delete_grocery_product(kitchen_id, product_id)
            return

        # Check how many of this product is already in the grocery list
        curr_amount = self.get_grocery_product_amount(kitchen_id, product_id)

        # Add the product to the corresponding search index
        # if the product was not already in the grocery list
        if curr_amount == 0:
            product = self._get_product_from_kitchen(kitchen_id, product_id)
            self._search.index_grocery_products(
                kitchen_id,
                {product_id: product.name},
            )

        # Write the data to Redis
        self._rj.set(
            "kitchens",
            f"$.{kitchen_id}.grocery.{product_id}",
            amount,
        )

    def buy_product(
        self,
        kitchen_id: str,
        product_id: str,
        expiry: tuple[int, int, int],
        amount: int,
    ):
        """
        Moves the product from the kitchen's grocery list to its inventory list.
        `expiry` is a tuple in the form of `(yyyy, mm, dd)`.
        """

        # Convert the (yyyy, mm, dd) tuple to a unix timestamp
        expiry_unix_timestamp = int(time.mktime(date(*expiry).timetuple()))

        # Capture the inital state of the grocery and inventory lists
        initial_groc_amt = self.get_grocery_product_amount(kitchen_id, product_id)
        inital_inv_amt = self._get_inventory_product(
            kitchen_id,
            product_id,
            expiry_unix_timestamp,
        )

        # Remove the product from the grocery list
        self.set_grocery_product(
            kitchen_id,
            product_id,
            initial_groc_amt - amount,
        )

        # Add it to the inventory list
        self._set_inventory_product(
            kitchen_id,
            product_id,
            expiry_unix_timestamp,
            inital_inv_amt + amount,
        )

    #### PAGE DATA METHODS ####

    def _get_user_data_as_dict(self, email: str) -> dict:
        """
        Returns a dictionary version of the `User` with the
        specified `email`, to be unpacked into another dataclass.
        """
        # Construct the `User` object
        username = self._rj.get(f"user:{email}", "$.name")[0]
        user = User(email=email, username=username)

        return dataclasses.asdict(user)

    def _get_kitchen_data_as_dict(self, kitchen_id: str) -> dict:
        """
        Returns a dictionary version of the `Kitchen` with the
        specified `kitchen_id`, to be unpacked into another dataclass.
        """
        # Construct the `Kitchen` object
        kitchen_name = self._rj.get("kitchens", f"$.{kitchen_id}.name")[0]
        kitchen = Kitchen(
            kitchen_id=kitchen_id,
            kitchen_name=kitchen_name,
        )

        return dataclasses.asdict(kitchen)

    def get_kitchens_page_data(self, email: str) -> KitchensPageData:
        """Returns the data necessary to render the kitchen list page."""
        # Get the IDs of all the kitchens that the user is in

        owned_kitchen_ids = self._rj.get(f"user:{email}", "$.owned-kitchens")[0]
        shared_kitchen_ids = self._rj.get(f"user:{email}", "$.shared-kitchens")[0]
        kitchen_ids: list[str] = owned_kitchen_ids + shared_kitchen_ids
        kitchens: list[Kitchen] = []

        # Create a `Kitchen` for every ID in `kitchen_ids`
        for k_id in kitchen_ids:
            # Get the name of the kitchen
            kitchen_name = self._rj.get("kitchens", f"$.{k_id}.name")[0]

            kitchens.append(
                Kitchen(
                    kitchen_id=k_id,
                    kitchen_name=kitchen_name,
                )
            )

        return KitchensPageData(
            kitchens=kitchens,
            **self._get_user_data_as_dict(email),
        )

    def get_inventory_page_data(
        self,
        email: str,
        kitchen_id: str,
        search_query="",
    ) -> InventoryPageData:
        """Returns the data necessary to render the inventory list page."""
        # Get the IDs of all the products on the
        # inventory page that match the search query
        product_ids = self._search.search_inventory_products(kitchen_id, search_query)
        products: dict[str, list[InventoryProduct]] = {}

        for p_id in product_ids:
            # Get the product's name and category
            p = self._get_product_from_kitchen(kitchen_id, p_id)

            # Calculate the total amount of this product in the inventory list
            total_amount = sum(
                self._rj.get(
                    "kitchens",
                    f"$.{kitchen_id}.inventory.{p_id}.*",
                )
            )

            # Get the expiry date of the product that's expiring the soonest
            earliest_expiry_date = min(
                int(x)
                # Iterate over all the expiry dates
                for x in self._rj.objkeys(
                    "kitchens",
                    f"$.{kitchen_id}.inventory.{p_id}",
                )[0]
            )

            # Get the amount of the product that's expiring the soonest
            earliest_expiry_amount = self._rj.get(
                "kitchens",
                f"$.{kitchen_id}.inventory.{p_id}.{earliest_expiry_date}",
            )[0]

            # Create an empty list in `products`
            # if the key doesn't already exist
            if p.category not in products:
                products[p.category] = []

            # Add the inventory item to its corresponding list
            products[p.category].append(
                InventoryProduct(
                    id=p.id,
                    name=p.name,
                    category=p.category,
                    amount=total_amount,
                    closest_expiry_date=earliest_expiry_date,
                    amount_expiring=earliest_expiry_amount,
                )
            )

        sorted_products: dict[str, list[InventoryProduct]] = {}

        # Insert product categories in the order we want
        # them to be iterated in. This works in Python 3.7+
        # because dictionaries iterate in insertion order.
        for cat in sorted(products.keys()):
            sorted_products[cat] = sorted(
                products[cat],
                # Within the category, sort the products alphabetically
                key=lambda x: x.name,
            )

        return InventoryPageData(
            products=sorted_products,
            **self._get_user_data_as_dict(email),
            **self._get_kitchen_data_as_dict(kitchen_id),
        )

    def get_grocery_page_data(
        self,
        email: str,
        kitchen_id: str,
        search_query="",
    ) -> GroceryPageData:
        """Returns the data required to render the grocery list page."""

        # Maps category names to lists of grocery items
        grocery_products: dict[str, list[GroceryProduct]] = {}

        # Get the IDs of grocery items that match the search query
        product_ids = self._search.search_grocery_products(kitchen_id, search_query)

        # Include default products if the user searched for something
        if search_query:
            default_products = self._search.search_default_products(search_query)
            product_ids.extend(set(default_products) - set(product_ids))

        # Loop through the grocery list products to fill up `grocery_products`
        for p_id in product_ids:
            amount_matches = self._rj.get("kitchens", f"$.{kitchen_id}.grocery.{p_id}")
            amount = amount_matches[0] if amount_matches else 0
            product = self._get_product_from_kitchen(kitchen_id, p_id)

            # Overwrite the product category if the product isn't in the grocery list
            if amount == 0:
                product.category = "Unowned products"

            # Create an empty list in `grocery_products`
            # if the key doesn't already exist
            if product.category not in grocery_products:
                grocery_products[product.category] = []

            # Add the grocery item to its corresponding list
            grocery_products[product.category].append(
                GroceryProduct(
                    id=product.id,
                    name=product.name,
                    category=product.category,
                    amount=amount,
                )
            )

        # Sort the product categories alphabetically, except
        # for "Unowned products", which goes at the end
        sorted_product_categories = sorted(
            grocery_products.keys() - {"Unowned products"}
        )

        if "Unowned products" in grocery_products:
            sorted_product_categories.append("Unowned products")

        sorted_grocery_products = {}

        # Insert product categories in the order we want
        # them to be iterated in. This works in Python 3.7+
        # because dictionaries iterate in insertion order.
        for cat in sorted_product_categories:
            sorted_grocery_products[cat] = sorted(
                grocery_products[cat],
                # Within the category, sort the products alphabetically
                key=lambda p: p.name,
            )

        return GroceryPageData(
            products=sorted_grocery_products,
            **self._get_user_data_as_dict(email),
            **self._get_kitchen_data_as_dict(kitchen_id),
        )

    def get_grocery_product_page_data(
        self,
        email: str,
        kitchen_id: str,
        product_id: str,
    ) -> GroceryProductPageData:
        """Returns the data required to render the grocery product page."""
        # Get the grocery product's information
        p = self._get_product_from_kitchen(kitchen_id, product_id)
        amount = self.get_grocery_product_amount(kitchen_id, product_id)

        # Construct the `GroceryProduct`
        grocery_product = GroceryProduct(
            name=p.name,
            category=p.category,
            id=p.id,
            amount=amount,
        )

        return GroceryProductPageData(
            product=grocery_product,
            has_expiry_date=False,
            buy_amount=max(1, amount),
            **self._get_kitchen_data_as_dict(kitchen_id),
            **self._get_user_data_as_dict(email),
        )
