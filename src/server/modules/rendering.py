"""
Provides an interface for rendering HTML.

Authored by Haziq Hairil.
"""

import jinja2
from .models import (
    KitchensPageData,
    InventoryPageData,
    InventoryProductPage,
    GroceryPageData,
    GroceryProductPageData,
)


class Renderer:
    """Renders Jinja templates from page data objects."""

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
        """Render the Jinja template at the specified filepath."""
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

    def kitchens_page(self, page_data: KitchensPageData) -> str:
        """Returns the HTML of the kitchen list page."""
        return self._render("kitchens.html", data=page_data)

    #### INVENTORY LIST ####

    def inventory_page(self, page_data: InventoryPageData) -> str:
        """Returns the HTML of the inventory page."""
        return self._render("inventory/index.html", data=page_data)

    def inventory_product_page(self, page_data: InventoryProductPage) -> str:
        """Returns the HTML of an inventory product's page."""
        return self._render("inventory/product.html", data=page_data)

    #### GROCERY LIST ####

    def grocery_page(self, page_data: GroceryPageData) -> str:
        """Returns the HTML of the grocery page."""
        return self._render("grocery/index.html", data=page_data)

    def grocery_partial(self, page_data: GroceryPageData) -> str:
        """Returns the HTML partial of the grocery list."""
        return self._render("grocery/list.partial.html", data=page_data)

    def grocery_product_page(self, page_data: GroceryProductPageData) -> str:
        """Returns the HTML of a grocery product's page."""
        return self._render("grocery/product.html", data=page_data)

    def grocery_product_amount_partial(self, page_data: GroceryProductPageData) -> str:
        """Returns the HTML partial of a grocery product's amount adjuster"""
        return self._render("grocery/amount.partial.html", data=page_data)
