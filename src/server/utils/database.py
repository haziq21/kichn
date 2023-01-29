"""
This module exposes high-level functions to interface with the
Redis database while abstracting away its architectural details.

Authored by Haziq Hairil.
"""

import redis
import argon2
import string
import random
from pathlib import Path
from typing import Optional
from .search import SearchClient
from .classes import (
    Kitchen,
    User,
    Product,
    InventoryProduct,
    GroceryProduct,
    InventoryList,
    KitchensPageData,
    InventoryPageData,
    GroceryPageData,
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

    def __init__(self, static_asset_dir: str, generated_content_dir: str):
        """
        - `static_asset_dir` - The filepath of the directory containing static assets.
        - `generated_content_dir` - The filepath of the directory containing product images.
        """
        self._static_asset_dir = Path(static_asset_dir)
        self._generated_content_dir = Path(generated_content_dir)

        self._r = redis.Redis()
        self._ph = argon2.PasswordHasher()
        self._search = SearchClient()

        # Maps default products' IDs to their names
        default_products = {}

        # Fill `default_products`
        for product_id in self.get_default_product_ids():
            product_name = self._r.hget("product:" + product_id, "name")
            assert product_name is not None

            default_products[product_id] = product_name.decode()

        # Add the default products to the search index
        self._search.index_default_products(default_products)

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
        filepath = self._generated_content_dir

        if self._r.exists(f"product:{product_id}:name"):
            # If the product is a default product then it
            # should be in the default-images folder
            filepath /= "default-images"
        elif self._r.hexists(f"kitchen:{kitchen_id}:x-products", product_id):
            # If the product is a custom product then it should be in
            # the kitchen-{kitchen_id} folder (e.g. kitchen-abc123)
            filepath /= f"kitchen-{kitchen_id}"
        else:
            # The product doesn't exist
            return None

        return (filepath / f"{product_id}.jpg").read_bytes()

    #### DEFAULT PRODUCTS ####

    def create_default_product(
        self,
        name: str,
        category: str,
        barcodes: list[int],
        image: bytes,
    ) -> str:
        """
        Creates a new default product in the database.
        Returns the generated ID of the product.
        """
        product_id = _gen_random_id()

        # Write the product data to the database
        self._r.hset(
            f"product:{product_id}",
            mapping={"name": name, "category": category},
        )
        self._r.sadd("default-products", product_id)

        # TODO: What if the barcode already exists in the database?
        if barcodes:
            self._r.hset("barcodes", mapping={str(b): product_id for b in barcodes})

        # Add this product to the search index
        self._search.index_default_products({product_id: name})

        # Write the product image to disk
        img_filepath = (
            self._generated_content_dir / "default-images" / f"{product_id}.jpg"
        )
        img_filepath.write_bytes(image)

        return product_id

    def drop_default_products(self):
        """
        Drops all default products from the database.
        For testing purposes only.
        """
        # Generate the Redis keys of all the default products
        default_product_keys = [
            "product:" + p_id for p_id in self.get_default_product_ids()
        ]
        self._r.delete("default-products", *default_product_keys)

    def get_default_product_ids(self) -> set[str]:
        """Returns the IDs of all the default products."""
        keys = self._r.smembers("default-products")
        return {x.decode() for x in keys}

    #### USER ACCOUNT MANAGEMENT ####

    def login_is_valid(self, email: str, password: str) -> bool:
        """
        Returns `True` if the user exists in the database
        and the password matches. Returns `False` otherwise.
        """
        hashed_pw = self._r.get(f"user:{email}:auth")

        if hashed_pw is None:
            # User does not exist
            return False

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
        if self._r.get(f"user:{email}:auth") is not None:
            # User already exists
            return False

        # Write the user's account data to the database
        self._r.set(f"user:{email}:name", name)
        self._r.set(f"user:{email}:auth", self._ph.hash(password))

        return True

    def get_user(self, email: str) -> User:
        """Returns the `User` with the specified email address."""
        username = self._r.get(f"user:{email}:name")
        assert username is not None

        return User(email=email, username=username.decode())

    def user_has_access_to_kitchen(self, email: str, kitchen_id: str) -> bool:
        """Returns whether the user has access to the specified kitchen."""
        # Whether the kitchen is owned by the user
        is_owned = self._r.sismember(f"user:{email}:owned-kitchens", kitchen_id)
        # Whether the kitchen has been shared to the user
        is_shared = self._r.sismember(f"user:{email}:shared-kitchens", kitchen_id)

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
        self._r.set(f"kitchen:{kitchen_id}:name", kitchen_name)
        self._r.sadd(f"user:{email}:owned-kitchens", kitchen_id)

        return kitchen_id

    def rename_kitchen(self, kitchen_id: str, new_name: str):
        """Sets the name of the kitchen to `new_name`."""
        self._r.set(f"kitchen:{kitchen_id}:name", new_name)

    def delete_kitchen(self, kitchen_id: str):
        """Deletes the kitchen from the database."""
        # TODO: Remember to delete the kitchen ID from users' owned-kitchens and shared-kitchens
        # Get all the Redis keys belonging to the specified kitchen
        kitchen_keys = self._r.keys(f"kitchen:{kitchen_id}:*")  # TODO: Don't use KEYS
        # Delete the keys
        self._r.delete(*kitchen_keys)

    #### KITCHEN PRODUCTS ####

    def _get_product_from_kitchen(self, kitchen_id: str, product_id: str) -> Product:
        """
        Checks if the specified product is in the kitchen's custom
        product list. Returns the product from the custom product
        list if it is, and from the default product list otherwise.
        """
        product_name = self._r.hget(f"product:{product_id}", "name")

        # Check the custom product list if this product isn't a default product
        if product_name is None:
            product_name = self._r.hget(f"kitchen:{kitchen_id}:x-products", product_id)
            assert product_name is not None

            return Product(
                id=product_id,
                name=product_name.decode(),
                category="Custom product",
            )

        product_category = self._r.hget(f"product:{product_id}", "category")
        assert product_category is not None

        return Product(
            id=product_id,
            name=product_name.decode(),
            category=product_category.decode(),
        )

    def get_inventory_list(self, kitchen_id: str) -> InventoryList:
        """Returns the `InventoryList` of the specified kitchen."""
        product_ids = self._r.smembers(f"kitchen:{kitchen_id}:inventory-products")
        # inv_products: list[InventoryProduct] = []

        # for p_id in product_ids:
        #     p = self._get_product_from_kitchen(kitchen_id, p_id.decode())
        #     inv_products.append(
        #         InventoryProduct(
        #             id=p.id,
        #             name=p.name,
        #             category=p.category,
        #         )
        #     )

        kitchen_name = self._r.get(f"kitchen:{kitchen_id}:name")
        assert kitchen_name is not None

        # TODO: Complete this

        return InventoryList(
            kitchen_id=kitchen_id,
            kitchen_name=kitchen_name.decode(),
            products=[],
        )

    #### LIST MANAGEMENT ####

    def set_grocery_product(self, kitchen_id: str, product_id: str, amount: int):
        """Updates the grocery list to have `amount` of the specified product."""
        redis_key = f"kitchen:{kitchen_id}:grocery"

        if amount:
            # Check how many of this product is already in the grocery list
            curr_amount_bytes = self._r.hget(redis_key, product_id)

            # Add the product to the corresponding search index
            # if the product was not already in the grocery list
            if curr_amount_bytes is None:
                product = self._get_product_from_kitchen(kitchen_id, product_id)
                self._search.index_grocery_products(
                    kitchen_id,
                    {product_id: product.name},
                )

            # Write the data to Redis
            self._r.hset(redis_key, product_id, amount)
        else:
            # Delete the product from the grocery list
            # if we're setting the amount to 0
            self._r.hdel(redis_key, product_id)
            self._search.delete_grocery_product(kitchen_id, product_id)

    #### PAGE DATA METHODS ####

    def get_kitchens_page_data(self, email: str) -> KitchensPageData:
        """Returns the data necessary to render the kitchen list page."""
        # Get the IDs of all the kitchens that the user is in
        kitchen_ids = self._r.sunion(
            f"user:{email}:owned-kitchens",
            f"user:{email}:shared-kitchens",
        )
        kitchens: list[Kitchen] = []

        # Create a `Kitchen` for every ID in `kitchen_ids`
        for k_id_bytes in kitchen_ids:
            # To make the type checker happy...
            assert isinstance(k_id_bytes, bytes)

            # Decode the kitchen ID from bytes into a string
            k_id = k_id_bytes.decode()

            # Get the name of the kitchen
            kitchen_name_bytes = self._r.get(f"kitchen:{k_id}:name")
            assert kitchen_name_bytes is not None

            kitchens.append(
                Kitchen(
                    kitchen_id=k_id,
                    kitchen_name=kitchen_name_bytes.decode(),
                )
            )

        # Get the user's username
        username_bytes = self._r.get(f"user:{email}:name")
        assert username_bytes is not None

        return KitchensPageData(
            email=email,
            username=username_bytes.decode(),
            kitchens=kitchens,
        )

    def get_inventory_page_data(self, email: str, kitchen_id: str, search_query="") -> InventoryPageData:
        """Returns the data necessary to render the inventory list page."""
        # Get the IDs of all the products on the
        # inventory page that match the search query
        # product_ids = self._search.search_inventory_products(kitchen_id, search_query)
        product_ids: list[str] = []

        # product_ids_bytes = self._r.smembers(f"kitchen:{kitchen_id}:inventory-products")
        products: list[InventoryProduct] = []

        for p_id in product_ids:
            # Get the product's ID, name and category
            p = self._get_product_from_kitchen(kitchen_id, p_id)

            # This dict maps expiry dates to the
            # number of products expiring on that date
            expiry_data = self._r.hgetall(
                f"kitchen:{kitchen_id}:inventory-expiry:{p.id}"
            )

            # The earliest expiry date in `expiry_data`
            # TODO: Use -1 dates in Redis to represent non-expirables
            earliest_expiry_date = 0
            # The number of products expiring on that earliest expiry date
            earliest_expiry_amount = 0
            total_amount = 0

            # Traverse through the expiry data to find the earliest expiry date
            # and the corresponding number of products expiring on that date
            for date_bytes in expiry_data:
                date = int(date_bytes.decode())
                amount = int(expiry_data[date_bytes].decode())
                total_amount += amount

                if earliest_expiry_date == 0 or date < earliest_expiry_date:
                    earliest_expiry_date = date
                    earliest_expiry_amount = amount

            products.append(
                InventoryProduct(
                    id=p.id,
                    name=p.name,
                    category=p.category,
                    amount=total_amount,
                    closest_expiry_date=earliest_expiry_date,
                    amount_expiring=earliest_expiry_amount,
                )
            )

        kitchen_name_bytes = self._r.get(f"kitchen:{kitchen_id}:name")
        assert kitchen_name_bytes is not None

        username_bytes = self._r.get(f"user:{email}:name")
        assert username_bytes is not None

        # TODO: Un-mock this
        return InventoryPageData(
            kitchen_name=kitchen_name_bytes.decode(),
            kitchen_id=kitchen_id,
            email=email,
            username=username_bytes.decode(),
            products={},
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

        product_ids = self._search.search_grocery_products(kitchen_id, search_query)

        # Include default products if the user searched for something
        if search_query:
            default_products = self._search.search_default_products(search_query)
            product_ids.extend(set(default_products) - set(product_ids))

        # Loop through the grocery list products to fill up `grocery_products`
        for p_id in product_ids:
            amount_bytes = self._r.hget(f"kitchen:{kitchen_id}:grocery", p_id) or b"0"
            # Redis stores integers as strings, so we decode
            # the bytes into strings before casting to int
            amount = int(amount_bytes)

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

        # Within each product category, sort the products alphabetically
        # TODO: Do we need this? Is the order non-deterministic otherwise?
        # for products in grocery_products.values():
        #     products.sort(key=lambda p: p.name)

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
            sorted_grocery_products[cat] = grocery_products[cat]

        # Get the kitchen's name
        kitchen_name_bytes = self._r.get(f"kitchen:{kitchen_id}:name")
        assert kitchen_name_bytes is not None

        # Get the user's username
        username_bytes = self._r.get(f"user:{email}:name")
        assert username_bytes is not None

        return GroceryPageData(
            email=email,
            username=username_bytes.decode(),
            kitchen_id=kitchen_id,
            kitchen_name=kitchen_name_bytes.decode(),
            products=sorted_grocery_products,
        )
