"""
This module provides functions to render Jinja templates.

Authored by Haziq Hairil.
"""

import jinja2
from .classes import Kitchen, User


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
        layout = self._env.get_template(
            "_layout.html" if full_doc else "_blank_layout.html"
        )

        return self._env.get_template("kitchens.html").render(
            layout=layout,
            kitchens=kitchens,
            user=user,
        )
