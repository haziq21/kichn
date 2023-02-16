"""
Provides classes that model application-specific entities and page GUIs.

Authored by Lohith Tanuku.
"""

from dataclasses import dataclass
from datetime import date

#### ENTITY MODELS ####


@dataclass
class Kitchen:
    name: str
    id: str


@dataclass
class User:
    email: str
    username: str


@dataclass
class Product:
    name: str
    category: str
    id: str


@dataclass
class GroceryProduct(Product):
    amount: int


@dataclass
class InventoryProduct(GroceryProduct):
    expiries: dict[date, int]
    non_expirables: int


#### PAGE MODELS ####


@dataclass
class KitchenListPage:
    """Page model for `/kitchens`."""

    user: User
    kitchens: list[Kitchen]


@dataclass
class GenericKitchenPage:
    """
    Serves as a base class for all the page models
    that represent a route under `kitchens/{kitchen_id}/`.
    """

    user: User
    kitchen: Kitchen


@dataclass
class SortedInventoryPage(GenericKitchenPage):
    products: list[InventoryProduct]


@dataclass
class InventoryPage(GenericKitchenPage):
    """Page model for `/kitchens/{kitchen_id}/inventory`."""

    products: dict[str, list[InventoryProduct]]


@dataclass
class GroceryPage(GenericKitchenPage):
    """Page model for `/kitchens/{kitchen_id}/grocery`."""

    products: dict[str, list[GroceryProduct]]


@dataclass
class GroceryProductPage(GenericKitchenPage):
    """Page model for the page on `/kitchens/{kitchen_id}/grocery/{product_id}`."""

    product: GroceryProduct


@dataclass
class InventoryProductPage(GenericKitchenPage):
    """Page model for the page on `/kitchens/{kitchen_id}/inventory/{product_id}`."""

    product: InventoryProduct


@dataclass
class AdminSettingsPage(GenericKitchenPage):
    """
    Page model for the page on `/kitchens/{kitchen_id}/settings`.
    This page is only seen by admins of the kitchen.
    """

    members: list[User]
