"""
This module exposes high-level functions to interface 
with the Meilisearch full-text search engine.
"""

import meilisearch
import meilisearch.errors


class SearchClient:
    """Handles communication with the Meilisearch server."""

    def __init__(self):
        self._client = meilisearch.Client("http://localhost:7700")

    #### HELPER FUNCTIONS ####

    def _add_products_to_index(self, index_name: str, product_names: dict[str, str]):
        """
        Adds the given products to the specified search index.
        `product_names` maps product IDs to product names.
        """
        documents = []

        for product_id in product_names:
            doc = {
                "id": product_id,
                "name": product_names[product_id],
            }
            documents.append(doc)

        if documents:
            self._client.index(index_name).add_documents(documents)

    #### PRODUCT INDEXING ####

    def index_default_products(self, product_names: dict[str, str]):
        """
        Indexes the given products as default products.
        `product_names` maps product IDs to product names.
        """
        self._add_products_to_index("default", product_names)

    def index_inventory_products(self, kitchen_id: str, product_names: dict[str, str]):
        """
        Indexes the given products as items of the kitchen's inventory.
        `product_names` maps product IDs to product names.
        """
        self._add_products_to_index(kitchen_id + "-inventory", product_names)

    def index_grocery_products(self, kitchen_id: str, product_names: dict[str, str]):
        """
        Indexes the given products as items of the kitchen's grocery list.
        `product_names` maps product IDs to product names.
        """
        self._add_products_to_index(kitchen_id + "-grocery", product_names)

    def index_custom_products(self, kitchen_id: str, product_names: dict[str, str]):
        """
        Indexes the given products as custom products of the kitchen.
        `product_names` maps product IDs to product names.
        """
        self._add_products_to_index(kitchen_id + "-custom", product_names)

    #### PRODUCT SEARCHING ####

    def search_default_products(self, query: str) -> list[str]:
        """Returns the IDs of default products that match the search query."""
        search_result = self._client.index("default").search(query)
        return [i["id"] for i in search_result["hits"]]

    def search_inventory_products(self, kitchen_id: str, query: str) -> list[str]:
        """
        Returns the IDs of products that are in the specified
        inventory list which match the search query.
        """
        search_result = self._client.index(kitchen_id + "-inventory").search(query)
        return [i["id"] for i in search_result["hits"]]

    def search_grocery_products(self, kitchen_id: str, query: str) -> list[str]:
        """
        Returns the IDs of products that are in the specified
        grocery list which match the search query.
        """
        search_result = self._client.index(kitchen_id + "-grocery").search(query)
        return [i["id"] for i in search_result["hits"]]

    def search_custom_products(self, kitchen_id: str, query: str) -> list[str]:
        """
        Returns the IDs of custom products from the
        specified kitchen which match the search query.
        """
        search_result = self._client.index(kitchen_id + "-custom").search(query)
        return [i["id"] for i in search_result["hits"]]

    def _search_index(self, index_name: str, query: str) -> list[str]:
        """
        Returns the IDs of products from the
        specified index that match the search query.
        """
        search_result = self._client.index(index_name).search(query)
        return [i["id"] for i in search_result["hits"]]

    #### PRODUCT DELETION ####

    def delete_inventory_product(self, kitchen_id: str, product_id: str):
        """Removes the specified product from the kitchen's inventory index."""
        self._client.index(kitchen_id + "-inventory").delete_document(product_id)

    def delete_grocery_product(self, kitchen_id: str, product_id: str):
        """Removes the specified product from the kitchen's grocery index."""
        self._client.index(kitchen_id + "-grocery").delete_document(product_id)

    def delete_custom_product(self, kitchen_id: str, product_id: str):
        """Removes the specified product from the kitchen's custom product index."""
        self._client.index(kitchen_id + "-custom").delete_document(product_id)

    #### RENAMING CUSTOM PRODUCTS ####

    def _product_is_in_index(self, index_name: str, product_id: str) -> bool:
        """Returns whether the specified product is in the specified search index."""
        # TODO: `try` to get the product document with .get_document() and return `True`.
        # TODO: Catch the meilisearch.errors.MeiliSearchApiError exception.
        # TODO: If the error code is "document_not_found", return `False`.
        # TODO: If the error code is anything else, something went wrong - re-raise
        # TODO: the exception so we can debug it: `raise e`

        return False

    def rename_custom_product(self, kitchen_id: str, product_id: str, new_name: str):
        """
        Updates the search indexes in the kitchen to use the new
        product name. This will create a new custom product if it
        doesn't already exist in the kitchen's custom product index.
        """
        # TODO: Run self.index_custom_products() with the new product
        # name (and same id). This will overwrite the old document.

        # TODO: Use self._product_is_in_index() to check if the product is in
        # the kitchen's inventory index. If it is, use self.index_inventory_products()
        # to overwrite it.

        # TODO: Use self._product_is_in_index() to check if the product is in
        # the kitchen's grocery index. If it is, use self.index_grocery_products()
        # to overwrite it.
