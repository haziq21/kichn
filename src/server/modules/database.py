"""
Interfaces with the Redis database, abstracting away its architectural details.

Authored by Haziq Hairil.
"""

import redis
import argon2
import string
import random
import time
from datetime import date
from pathlib import Path
from typing import Optional
from .search import SearchClient
from .models import (
    User,
    Kitchen,
    Product,
    InventoryProduct,
    GroceryProduct,
    KitchensPage,
    InventoryPage,
    InventoryProductPage,
    GroceryPage,
    GroceryProductPage,
    SharingSettingsPage,
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

    def user_owns_kitchen(self, email: str, kitchen_id: str) -> bool:
        # Get the index of the kitchen_id in the user's list of owned kitchens
        index: int = self._rj.arrindex(
            f"user:{email}",
            "$.owned-kitchens",
            kitchen_id,
        )[0]
        # The index would be -1 if the kitchen_id isn't in the list
        return index != -1

    #### AUTHENTICATION TOKENS ####

    def generate_auth_token(self, email: str) -> str:
        """Creates and returns an authentication token for the user."""
        auth_token = _gen_random_id()
        # Store the auth token in the database
        self._r.hset("auth-tokens", auth_token, email)

        return auth_token

    def delete_auth_token(self, auth_token: str):
        """Removes the authentication token from the database."""
        self._r.hdel("auth-tokens", auth_token)

    def get_auth_token_owner(self, auth_token: str) -> Optional[str]:
        """
        Returns the email address of the user who owns the specified
        authentication token, or `None` if the token is invalid.
        """
        # Email address of the token's owner
        email_bytes = self._r.hget("auth-tokens", auth_token)

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
                "nonAdmins": [],
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

    def share_kitchen(self, kitchen_id: str, email: str):
        """Adds the user as a member of the kitchen."""
        # Add the kitchen to the user's list of kitchens that have been shared with the user
        self._rj.arrappend(f"user:{email}", "$.shared-kitchens", kitchen_id)

        # Add the user to the kitchen's list of non-admin members
        self._rj.arrappend("kitchens", f"$.{kitchen_id}.nonAdmins", email)

    #### PRODUCT LIST MANAGEMENT ####

    def _product(self, kitchen_id: str, product_id: str) -> Product:
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

    def _inv_product(self, kitchen_id: str, product_id: str) -> InventoryProduct:
        """Returns the specified `InventoryProduct`."""
        # Get the raw expiry data from the database
        expiry_data_matches = self._rj.get(
            "kitchens",
            f"$.{kitchen_id}.inventory.{product_id}",
        )
        raw_expiry_data: dict[str, int]

        if expiry_data_matches:
            raw_expiry_data = expiry_data_matches[0]
        else:
            # If there is no database entry for this product in the
            # inventory list, we assign raw_expiry_data to an empty dict
            raw_expiry_data = {}

        # Maps expiry dates to the amount of the product expiring on the date
        expiries: dict[date, int] = {
            # Cast the expiry timestamp from a str
            # (in unix timestamp format) into a date
            date.fromtimestamp(float(exp)): amt
            # Iterate through the key-value pairs of the expiry data
            for exp, amt in raw_expiry_data.items()
            # Skip non-expirables (indicated with a -1 expiry date)
            if exp != "-1"
        }

        # Insert products in the order we want to iterate over them
        # (in order of their expiry date). This works in Python 3.7+
        # because dictionaries iterate in insertion order.
        expiries = {exp: expiries[exp] for exp in sorted(expiries.keys())}

        # Get the amount of non-expirables
        non_expiries: int = raw_expiry_data.get("-1", 0)

        # Get the product's name and category
        p = self._product(kitchen_id, product_id)

        # Calculate the total amount of this product in the inventory list
        amount = sum(
            # Get the amounts of all instances (all expiry dates) of this product
            self._rj.get(
                "kitchens",
                f"$.{kitchen_id}.inventory.{product_id}.*",
            )
        )

        return InventoryProduct(
            id=p.id,
            name=p.name,
            category=p.category,
            amount=amount,
            expiries=expiries,
            non_expirables=non_expiries,
        )

    def _groc_product(self, kitchen_id: str, product_id: str) -> GroceryProduct:
        """Returns the specified `GroceryProduct`."""
        amount_matches = self._rj.get(
            "kitchens",
            f"$.{kitchen_id}.grocery.{product_id}",
        )
        # Get the amount of the product in the grocery list
        amount: int = amount_matches[0] if amount_matches else 0

        # Get the other product information
        p = self._product(kitchen_id, product_id)

        # Add the grocery item to its corresponding list
        return GroceryProduct(
            id=p.id,
            name=p.name,
            category=p.category,
            amount=amount,
        )

    def _set_inv_product_count(
        self,
        kitchen_id: str,
        product_id: str,
        expiry: Optional[date],
        amount: int,
    ):
        """Updates the inventory list to have `amount` of the product."""
        if expiry:
            expiry_timestamp = int(time.mktime(expiry.timetuple()))
        else:
            # Store non-expirables as products with a -1 expiry date
            expiry_timestamp = -1

        # Delete the product from the inventory
        # list if we're setting the amount <= 0
        if amount <= 0:
            self._rj.delete(
                "kitchens",
                f"$.{kitchen_id}.inventory.{product_id}.{expiry_timestamp}",
            )
            # Remove the product from the search index too
            self._search.delete_inventory_product(kitchen_id, product_id)
            return

        # Get the inventory product's data
        product = self._inv_product(kitchen_id, product_id)

        # Check if the product is not already in the inventory list
        if product.amount == 0:
            # Create an empty entry for the product in the inventory list
            self._rj.set(
                "kitchens",
                f"$.{kitchen_id}.inventory.{product_id}",
                {},
            )

            # Add the product to the corresponding search index
            self._search.index_inventory_products(
                kitchen_id,
                {product.id: product.name},
            )

        # Set the amount
        self._rj.set(
            "kitchens",
            f"$.{kitchen_id}.inventory.{product.id}.{expiry_timestamp}",
            amount,
        )

    def set_groc_product_count(self, kitchen_id: str, product_id: str, amount: int):
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

        product = self._groc_product(kitchen_id, product_id)

        # Add the product to the corresponding search index
        # if the product was not already in the grocery list
        if product.amount == 0:
            self._search.index_grocery_products(
                kitchen_id,
                {product.id: product.name},
            )

        # Write the data to the database
        self._rj.set(
            "kitchens",
            f"$.{kitchen_id}.grocery.{product.id}",
            amount,
        )

    def buy_product(
        self,
        kitchen_id: str,
        product_id: str,
        expiry: Optional[tuple[int, int, int]],
        amount: int,
    ):
        """
        Moves the product from the kitchen's grocery list to its inventory list.
        `expiry` is a tuple in the form of `(year, month, date)`.
        """

        # Convert the (year, month, date) tuple to a date object
        expiry_date = date(*expiry) if expiry else None

        # Get the grocery product's data
        groc_product = self._groc_product(kitchen_id, product_id)

        # Remove the product from the grocery list
        self.set_groc_product_count(
            kitchen_id,
            product_id,
            groc_product.amount - amount,
        )

        # Get the inventory product's data
        inv_product = self._inv_product(kitchen_id, product_id)

        if expiry_date is None:
            # TODO: Set this to inv_product.non_expirables
            inital_inv_amt = 0
        else:
            inital_inv_amt = inv_product.expiries.get(expiry_date, 0)

        # Add it to the inventory list
        self._set_inv_product_count(
            kitchen_id,
            product_id,
            expiry_date,
            inital_inv_amt + amount,
        )

    #### PAGE MODEL GETTERS ####

    def _user(self, email: str) -> User:
        """Gets the `User` with the specified email address."""
        username = self._rj.get(f"user:{email}", "$.name")[0]
        return User(email=email, username=username)

    def _kitchen(self, kitchen_id: str) -> Kitchen:
        """Gets the `Kitchen` with the specified ID."""
        kitchen_name = self._rj.get("kitchens", f"$.{kitchen_id}.name")[0]
        return Kitchen(
            id=kitchen_id,
            name=kitchen_name,
        )

    def get_kitchens_page_data(self, email: str) -> KitchensPage:
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
                    id=k_id,
                    name=kitchen_name,
                )
            )

        return KitchensPage(
            kitchens=kitchens,
            user=self._user(email),
        )

    def get_inventory_page_data(
        self,
        email: str,
        kitchen_id: str,
        search_query="",
    ) -> InventoryPage:
        """Returns the data necessary to render the inventory list page."""
        # Get the IDs of all the products on the
        # inventory page that match the search query
        product_ids = self._search.search_inventory_products(kitchen_id, search_query)
        # Maps product category names to products in that category
        products: dict[str, list[InventoryProduct]] = {}

        for p_id in product_ids:
            # Get the inventory product's data
            p = self._inv_product(kitchen_id, p_id)

            # Create an empty list in `products`
            # if the key doesn't already exist
            if p.category not in products:
                products[p.category] = []

            # Add the inventory item to its corresponding list
            products[p.category].append(p)

        # Insert product categories in the order we want
        # them to be iterated in. This works in Python 3.7+
        # because dictionaries iterate in insertion order.
        products = {
            # Within each category, sort the products in alphabetical order
            cat: sorted(
                products[cat],
                key=lambda x: x.name,
            )
            # Iterate through the product categories in alphabetical order
            for cat in sorted(products.keys())
        }

        return InventoryPage(
            products=products,
            user=self._user(email),
            kitchen=self._kitchen(kitchen_id),
        )

    def get_inventory_product_page_data(
        self,
        email: str,
        kitchen_id: str,
        product_id: str,
    ) -> InventoryProductPage:
        """Returns the data required to render the inventory product page."""
        return InventoryProductPage(
            user=self._user(email),
            kitchen=self._kitchen(kitchen_id),
            product=self._inv_product(kitchen_id, product_id),
        )

    def get_grocery_page_data(
        self,
        email: str,
        kitchen_id: str,
        search_query="",
    ) -> GroceryPage:
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
            # Get the grocery product's data
            product = self._groc_product(kitchen_id, p_id)

            # Overwrite the product category if the product isn't in the grocery list
            if product.amount == 0:
                product.category = "Unowned products"

            # Create an empty list in `grocery_products`
            # if the key doesn't already exist
            if product.category not in grocery_products:
                grocery_products[product.category] = []

            # Add the grocery item to its corresponding list
            grocery_products[product.category].append(product)

        # Sort the product categories alphabetically, except
        # for "Unowned products", which goes at the end
        sorted_product_categories = sorted(
            grocery_products.keys() - {"Unowned products"}
        )

        if "Unowned products" in grocery_products:
            sorted_product_categories.append("Unowned products")

        # Insert product categories in the order we want
        # them to be iterated in. This works in Python 3.7+
        # because dictionaries iterate in insertion order.
        grocery_products = {
            # Within the category, sort the products alphabetically
            cat: sorted(
                grocery_products[cat],
                key=lambda p: p.name,
            )
            for cat in sorted_product_categories
        }

        return GroceryPage(
            products=grocery_products,
            user=self._user(email),
            kitchen=self._kitchen(kitchen_id),
        )

    def get_grocery_product_page_data(
        self,
        email: str,
        kitchen_id: str,
        product_id: str,
    ) -> GroceryProductPage:
        """Returns the data required to render the grocery product page."""
        return GroceryProductPage(
            product=self._groc_product(kitchen_id, product_id),
            user=self._user(email),
            kitchen=self._kitchen(kitchen_id),
        )

    def get_sharing_settings_page_data(
        self,
        email: str,
        kitchen_id: str,
    ) -> SharingSettingsPage:
        # Get the emails of all the non-admin members of the kitchen
        member_emails: list[str] = self._rj.get(
            f"kitchens",
            f"$.{kitchen_id}.nonAdmins",
        )[0]

        return SharingSettingsPage(
            user=self._user(email),
            kitchen=self._kitchen(kitchen_id),
            members=[self._user(e) for e in member_emails],
        )
