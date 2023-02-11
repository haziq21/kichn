"""
Provides an interface for rendering HTML.

Authored by Haziq Hairil.
"""

import jinja2
from .models import (
    InventoryPageData,
    KitchensPageData,
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

    #### AUTHENTICATION ####

    def login(self) -> str:
        """Returns the full HTML document for the login page."""
        return self._env.get_template("login.html").render()

    def login_failed(self) -> str:
        """Returns the HTML fragment for when a login request fails."""
        return "Incorrect password or email address."

    def signup(self) -> str:
        """Returns the full HTML document for the signup page."""
        return self._env.get_template("signup.html").render()

    def signup_failed(self) -> str:
        """Returns the HTML fragment for when a signup request fails."""
        return "An account with this email address already exists."

    #### KITCHENS ####

    def kitchens_page(self, page_data: KitchensPageData) -> str:
        """Returns the HTML of the kitchen list page."""
        return self._env.get_template("kitchens.html").render(data=page_data)

    def inventory_page(self, page_data: InventoryPageData) -> str:
        """Returns the HTML of the inventory page."""
        return self._env.get_template("inventory/index.html").render(data=page_data)

    def grocery_page(self, page_data: GroceryPageData) -> str:
        """Returns the HTML of the grocery page."""
        return self._env.get_template("grocery/index.html").render(
            data=page_data,
        )

    def grocery_partial(self, page_data: GroceryPageData) -> str:
        """Returns the HTML partial of the grocery list."""
        return self._env.get_template("grocery/list.partial.html").render(
            data=page_data,
        )

    def grocery_product_page(self, page_data: GroceryProductPageData) -> str:
        """Returns the HTML of a grocery product's page."""
        return self._env.get_template("grocery/product.html").render(data=page_data)

    def grocery_product_amount_partial(self, page_data: GroceryProductPageData) -> str:
        """Returns the HTML partial of a grocery product's amount adjuster"""
        return self._env.get_template("grocery/amount.partial.html").render(
            data=page_data
        )