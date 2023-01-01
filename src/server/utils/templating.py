"""
This module provides functions to render Jinja templates.

Authored by Haziq Hairil.
"""

import jinja2


class Templator:
    def __init__(self, dir: str):
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(dir),
            autoescape=jinja2.select_autoescape(),
        )

    def login(self) -> str:
        return ""

    def login_failed(self) -> str:
        return ""

    def signup(self) -> str:
        return ""

    def signup_failed(self) -> str:
        return ""
