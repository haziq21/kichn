"""
Provides an interface for rendering HTML.

Authored by Haziq Hairil.
"""

import jinja2
from typing import Optional
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

    def _render(self, filepath: str, session_token="", full_doc=False, **kwargs) -> str:
        """
        Returns the rendered Jinja template from the specified filepath.
        Returns a HTML partial of the page body if `full_doc=False`, and
        the full HTML document otherwise. Passes additional keyword arguments
        as Jinja variables.

        If `full_doc=True`, `session_token` must be specified (because
        the session token is included in the full HTML document).
        """
        # Use either the full HTML wrapper or the partial one, depending on full_doc
        wrapper = self._env.get_template(
            "_wrapper_full.html" if full_doc else "_wrapper_partial.html"
        )
        return self._env.get_template(filepath).render(
            wrapper=wrapper,
            session_token=session_token,
            **kwargs,
        )

    #### AUTHENTICATION ####

    def login_page(self, session_token: str, full_doc: bool) -> str:
        """
        Returns the HTML for the login page. Gets the full HTML
        document if `full_doc=True`, and the body HTML otherwise.
        """
        return self._render("auth/login.html", session_token, full_doc)

    def login_failed_partial(self) -> str:
        """Returns the HTML partial for when a login request fails."""
        return "Incorrect password or email address."

    def signup_page(self, session_token: str, full_doc: bool) -> str:
        """
        Returns the HTML for the signup page. Gets the full HTML
        document if `full_doc=True`, and the body HTML otherwise.
        """
        return self._render("auth/signup.html", session_token, full_doc)

    def signup_failed_partial(self) -> str:
        """Returns the HTML fragment for when a signup request fails."""
        return "An account with this email address already exists."

    #### KITCHENS LIST ####

    def kitchens_page(
        self,
        page_data: KitchenListPage,
        session_token: str,
        full_doc: bool,
    ) -> str:
        """
        Returns the HTML for the kitchen list page. Gets the full HTML
        document if `full_doc=True`, and the body HTML otherwise.
        """
        return self._render(
            "kitchens.html",
            session_token,
            full_doc,
            data=page_data,
        )

    #### INVENTORY LIST ####

    def inventory_page(
        self,
        page_data: InventoryPage,
        session_token: str,
        full_doc: bool,
    ) -> str:
        """
        Returns the HTML of the inventory page,
        with the inventory list sorted by category.
        """
        return self._render(
            "/kitchen/inventory/index.html",
            session_token,
            full_doc,
            data=page_data,
            page_type="inventory",
        )

    def inventory_partial(self, page_data: InventoryPage) -> str:
        """Returns the HTML partial of the inventory list, sorted by category."""
        return self._render(
            "kitchen/inventory/list.partial.html",
            data=page_data,
            page_type="inventory",
        )

    def sorted_inventory_page(
        self,
        page_data: SortedInventoryPage,
        session_token: str,
        full_doc: bool,
    ) -> str:
        """
        Returns the HTML of the inventory page, with
        the inventory list being sorted by expiry date.
        """
        return self._render(
            "kitchen/inventory/index_sorted.html",
            session_token,
            full_doc,
            data=page_data,
            page_type="inventory",
        )

    def sorted_inventory_partial(self, page_data: SortedInventoryPage) -> str:
        """Returns the HTML partial of the inventory list, sorted by expiry date."""
        return self._render(
            "kitchen/inventory/sorted_list.partial.html",
            data=page_data,
            page_type="inventory",
        )

    def inventory_product_page(
        self,
        page_data: InventoryProductPage,
        session_token: str,
        full_doc: bool,
    ) -> str:
        """Returns the HTML of an inventory product's page."""
        return self._render(
            "kitchen/inventory/product.html",
            session_token,
            full_doc,
            data=page_data,
            page_type="inventory",
        )

    def inventory_product_partial(self, page_data: InventoryProductPage) -> str:
        """Returns the HTML partial of an inventory product's amount selector."""
        return self._render(
            "kitchen/inventory/product.partial.html",
            data=page_data,
            page_type="inventory",
        )

    def inventory_product_confirmation_partial(
        self,
        page_data: InventoryProductPage,
    ) -> str:
        """Returns the HTML partial of the "Move to grocery list?" UI."""
        return self._render(
            "kitchen/inventory/move_to_grocery.partial.html",
            data=page_data,
            page_type="inventory",
        )

    #### GROCERY LIST ####

    def grocery_page(
        self,
        page_data: GroceryPage,
        session_token: str,
        full_doc: bool,
    ) -> str:
        """Returns the HTML of the grocery page."""
        return self._render(
            "kitchen/grocery/index.html",
            session_token,
            full_doc,
            data=page_data,
            page_type="grocery",
        )

    def grocery_partial(self, page_data: GroceryPage) -> str:
        """Returns the HTML partial of the grocery list."""
        return self._render(
            "kitchen/grocery/list.partial.html",
            data=page_data,
            page_type="grocery",
        )

    def grocery_product_page(
        self,
        page_data: GroceryProductPage,
        session_token: str,
        full_doc: bool,
    ) -> str:
        """Returns the HTML of a grocery product's page."""
        return self._render(
            "kitchen/grocery/product.html",
            session_token,
            full_doc,
            data=page_data,
            page_type="grocery",
        )

    def grocery_product_amount_partial(self, page_data: GroceryProductPage) -> str:
        """Returns the HTML partial of a grocery product's amount adjuster"""
        return self._render(
            "kitchen/grocery/amount.partial.html",
            data=page_data,
            page_type="grocery",
        )

    def barcode_scanner_page(
        self,
        page_data: GenericKitchenPage,
        session_token: str,
        full_doc: bool,
    ) -> str:
        """Returns the HTML of the barcode scanner page."""
        return self._render(
            "kitchen/grocery/scan.html",
            session_token,
            full_doc,
            data=page_data,
            page_type="grocery",
        )

    def barcode_found_partial(self, page_data: GroceryProductPage) -> str:
        """
        Returns the HTML partial that redirects the
        user to the barcode's corresponding product page.
        """
        return self._render(
            "kitchen/grocery/barcode_found.partial.html",
            data=page_data,
        )

    #### KITCHEN SETTINGS ####

    def admin_settings_page(
        self,
        page_data: AdminSettingsPage,
        session_token: str,
        full_doc: bool,
    ) -> str:
        """Returns the HTML of the kitchen settings page for kitchen admins."""
        return self._render(
            "kitchen/settings/admin.html",
            session_token,
            full_doc,
            data=page_data,
            page_type="settings",
        )

    def members_list_partial(
        self,
        page_data: AdminSettingsPage,
        failed_share_email: Optional[str] = None,
    ) -> str:
        """
        Returns the HTML partial of the kitchen members list.
        `failed_share_email` is used to display the sharing error message.
        """
        return self._render(
            "kitchen/settings/admin.partial.html",
            data=page_data,
            failed_share=failed_share_email,
        )

    def nonadmin_settings_page(
        self,
        page_data: GenericKitchenPage,
        session_token: str,
        full_doc: bool,
    ) -> str:
        """Returns the HTML of the kitchen settings page for kitchen admins."""
        return self._render(
            "kitchen/settings/nonadmin.html",
            session_token,
            full_doc,
            data=page_data,
            page_type="settings",
        )
