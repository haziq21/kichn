"""
This module provides functions to render Jinja templates.

Authored by Haziq Hairil.
"""

import jinja2
from .classes import Kitchen, User, InventoryList


class Templator:
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

    def _get_layout_template(self, full_doc: bool) -> jinja2.Template:
        """
        Returns the `Template` for the full HTML document if
        `full_doc` is `True`, and an empty `Template` otherwise.
        """
        return self._env.get_template(
            "_layout.html" if full_doc else "_blank_layout.html"
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

    def kitchens(self, kitchens: list[Kitchen], user: User, full_doc=True) -> str:
        """
        Returns the body of the kitchens page if `full_doc`
        is `False`, and the full HTML document otherwise.
        """
        return self._env.get_template("kitchens.html").render(
            layout=self._get_layout_template(full_doc),
            kitchens=kitchens,
            user=user,
        )

    def inventory(
        self,
        inventory_list: InventoryList,
        user: User,
        full_doc=True,
    ) -> str:
        """
        Returns the body of the inventory page if `full_doc`
        is `False`, and the full HTML document otherwise.
        """
        return self._env.get_template("inventory.html").render(
            layout=self._get_layout_template(full_doc),
            user=user,
            inventory=inventory_list,
        )
