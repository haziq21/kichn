"""
Provides an interface for rendering HTML.

Authored by Haziq Hairil.
"""

import jinja2
from .models import (
    GenericKitchenPage,
    KitchenListPage,
    InventoryPage,
    SortedInventoryPage,
    InventoryProductPage,
    GroceryPage,
    GroceryProductPage,
    AdminSettingsPage,
)


class Renderer:
    """Renders Jinja templates from page models."""

    def __init__(self, templates_dir: str):
        """
        `templates_dir` is the file path to the directory
        that contains the Jinja HTML templates.
        """
        # Initialise the Jijna environment
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=jinja2.select_autoescape(),
        )

    def _render(self, filepath: str, **kwargs) -> str:
        """
        Returns the rendered Jinja template from the specified filepath.
        Passes keyword arguments as Jinja variables.
        """
        return self._env.get_template(filepath).render(**kwargs)

    #### AUTHENTICATION ####

    def login(self) -> str:
        """Returns the full HTML document for the login page."""
        return self._render("login.html")

    def login_failed(self) -> str:
        """Returns the HTML fragment for when a login request fails."""
        return "Incorrect password or email address."

    def signup(self) -> str:
        """Returns the full HTML document for the signup page."""
        return self._render("signup.html")

    def signup_failed(self) -> str:
        """Returns the HTML fragment for when a signup request fails."""
        return "An account with this email address already exists."

    #### KITCHENS LIST ####

    def kitchens_page(self, page_data: KitchenListPage) -> str:
        """Returns the HTML of the kitchen list page."""
        return self._render("kitchens.html", data=page_data)

    #### INVENTORY LIST ####

    def inventory_page(self, page_data: InventoryPage) -> str:
        """
        Returns the HTML of the inventory page,
        with the inventory list sorted by category.
        """
        return self._render(
            "inventory/index.html",
            data=page_data,
            page_type="inventory",
        )

    def inventory_partial(self, page_data: InventoryProductPage) -> str:
        """Returns the HTML partial of the inventory list, sorted by category."""
        return self._render(
            "inventory/list.partial.html",
            data=page_data,
            page_type="inventory",
        )

    def sorted_inventory_page(self, page_data: SortedInventoryPage) -> str:
        """
        Returns the HTML of the inventory page, with
        the inventory list being sorted by expiry date.
        """
        return self._render(
            "inventory/index_sorted.html",
            data=page_data,
            page_type="inventory",
        )

    def sorted_inventory_partial(self, page_data: SortedInventoryPage) -> str:
        """Returns the HTML partial of the inventory list, sorted by expiry date."""
        return self._render(
            "inventory/index_sorted.html",
            data=page_data,
            page_type="inventory",
        )

    def inventory_product_page(self, page_data: InventoryProductPage) -> str:
        """Returns the HTML of an inventory product's page."""
        return self._render(
            "inventory/product.html",
            data=page_data,
            page_type="inventory",
        )

    def inventory_product_confirmation_partial(
        self,
        page_data: InventoryProductPage,
    ) -> str:
        """Returns the HTML partial of the "Move to grocery list?" UI."""
        return self._render(
            "inventory/move_to_grocery.partial.html",
            data=page_data,
            page_type="inventory",
        )

    #### GROCERY LIST ####

    def grocery_page(self, page_data: GroceryPage) -> str:
        """Returns the HTML of the grocery page."""
        return self._render(
            "grocery/index.html",
            data=page_data,
            page_type="grocery",
        )

    def grocery_partial(self, page_data: GroceryPage) -> str:
        """Returns the HTML partial of the grocery list."""
        return self._render(
            "grocery/list.partial.html",
            data=page_data,
            page_type="grocery",
        )

    def grocery_product_page(self, page_data: GroceryProductPage) -> str:
        """Returns the HTML of a grocery product's page."""
        return self._render(
            "grocery/product.html",
            data=page_data,
            page_type="grocery",
        )

    def grocery_product_amount_partial(self, page_data: GroceryProductPage) -> str:
        """Returns the HTML partial of a grocery product's amount adjuster"""
        return self._render(
            "grocery/amount.partial.html",
            data=page_data,
            page_type="grocery",
        )

    def barcode_scanner_page(self, page_data: GenericKitchenPage) -> str:
        """Returns the HTML of the barcode scanner page."""
        return self._render(
            "grocery/scan.html",
            data=page_data,
            page_type="grocery",
        )

    #### KITCHEN SETTINGS ####

    def admin_settings(self, page_data: AdminSettingsPage) -> str:
        """Returns the HTML of the kitchen settings page for kitchen admins."""
        return self._render(
            "settings/admin.html",
            data=page_data,
            page_type="settings",
        )

    def nonadmin_settings(self, page_data: GenericKitchenPage) -> str:
        """Returns the HTML of the kitchen settings page for kitchen admins."""
        return self._render(
            "settings/nonadmin.html",
            data=page_data,
            page_type="settings",
        )
