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
class SortedInventoryPage:
    user: User
    kitchen: Kitchen
    products: list[InventoryProduct]


@dataclass
class InventoryPage:
    """Page model for '/kitchens/{kitchen_id}/inventory'"""

    user: User
    kitchen: Kitchen
    products: dict[str, list[InventoryProduct]]


@dataclass
class GroceryPage:
    """Page model for '/kitchens/{kitchen_id}/grocery'"""

    user: User
    kitchen: Kitchen
    products: dict[str, list[GroceryProduct]]


@dataclass
class KitchensPage:
    """Page model for '/kitchens'"""

    user: User
    kitchens: list[Kitchen]


@dataclass
class CustomPage:
    user: User
    products: list[Product]


@dataclass
class GroceryProductPage:
    """Data model for the page on '/kitchens/{kitchen_id}/grocery/{product_id}'"""

    user: User
    kitchen: Kitchen
    product: GroceryProduct


@dataclass
class InventoryProductPage:
    user: User
    kitchen: Kitchen
    product: InventoryProduct


@dataclass
class SharingSettingsPage:
    user: User
    kitchen: Kitchen
    members: list[User]
