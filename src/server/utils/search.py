"""
This module exposes high-level functions to interface 
with the Meilisearch full-text search engine.
"""

import meilisearch


class SearchClient:
    """Handles communication with the Meilisearch server."""

    def __init__(self):
        self._client = meilisearch.Client("http://localhost:7700")

    def index_default_products(self, product_names: dict[str, str]):
        documents = []

        for product_id in product_names:
            doc = {
                "id": product_id,
                "name": product_names[product_id],
            }
            documents.append(doc)

        self._client.index("default").add_documents(documents)

    def index_inventory_products(self, kitchen_id: str, product_names: dict[str, str]):

        self._client.index(kitchen_id + "-inventory").add_documents(documents)
        """
        Indexes the given products as items of the kitchen's inventory.
        `product_names` maps product IDs to product names.
        """
        # TODO: For each entry in `product_names`, create
        # a dict with the keys `id` and `name`. E.g.:
        # {
        #     "id": product_id,
        #     "name": product_name
        # }
        #
        # One such dict corresponds to one meilisearch document.
        # Add these documents to the `kID-inventory` index, where
        # `kID` is `kitchen_id`. E.g., if `kitchen_id` were "abc123",
        # the meilisearch index uid would be "abc123-inventory".

    def index_grocery_products(self, kitchen_id: str, product_names: dict[str, str]):
        """
        Indexes the given products as items of the kitchen's grocery list.
        `product_names` maps product IDs to product names.
        """
        # TODO: For each entry in `product_names`, create
        # a dict with the keys `id` and `name`. E.g.:
        # {
        #     "id": product_id,
        #     "name": product_name
        # }
        #
        # One such dict corresponds to one meilisearch document.
        # Add these documents to the `kID-grocery` index, where
        # `kID` is `kitchen_id`. E.g., if `kitchen_id` were "abc123",
        # the meilisearch index uid would be "abc123-grocery".

    def search_default_products(self, query: str) -> list[str]:
        """
        Returns the IDs of default products that match the search query.
        """
        return []

    def search_inventory_products(self, kitchen_id: str, query: str) -> list[str]:
        """
        Returns the IDs of products that are in the specified
        inventory list which match the search query.
        """
        return []

    def search_grocery_products(self, kitchen_id: str, query: str) -> list[str]:
        """
        Returns the IDs of products that are in the specified
        grocery list which match the search query.
        """
        return []
