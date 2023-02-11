"""
Provides classes that model application-specific entities and page GUIs.

Authored by Lohith Tanuku.
"""

from dataclasses import dataclass
from datetime import date

#### ENTITY MODELS ####


@dataclass
class Kitchen:
    kitchen_name: str
    kitchen_id: str


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
class SortedInventoryPageData(User, Kitchen):
    products: list[InventoryProduct]


@dataclass
class InventoryPageData(User, Kitchen):
    """Page model for '/kitchens/{kitchen_id}/inventory'"""

    products: dict[str, list[InventoryProduct]]


@dataclass
class GroceryPageData(User, Kitchen):
    """Page model for '/kitchens/{kitchen_id}/grocery'"""

    products: dict[str, list[GroceryProduct]]


@dataclass
class KitchensPageData(User):
    """Page model for '/kitchens'"""

    kitchens: list[Kitchen]


@dataclass
class CustomPageData(User):
    products: list[Product]


@dataclass
class GroceryProductPageData(User, Kitchen):
    """Data model for the page on '/kitchens/{kitchen_id}/grocery/{product_id}'"""

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
