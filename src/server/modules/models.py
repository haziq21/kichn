"""
Provides classes that model application-specific entities and page GUIs.

Authored by Lohith Tanuku.
"""

from dataclasses import dataclass

#### ENTITY CLASSES ####


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
    closest_expiry_date: int
    amount_expiring: int


#### PAGE CLASSES ####


@dataclass
class SortedInventoryPageData(User, Kitchen):
    products: list[InventoryProduct]


@dataclass
class InventoryPageData(User, Kitchen):
    products: dict[str, list[InventoryProduct]]


@dataclass
class GroceryPageData(User, Kitchen):
    products: dict[str, list[GroceryProduct]]


@dataclass
class KitchensPageData(User):
    kitchens: list[Kitchen]


@dataclass
class CustomPageData(User):
    products: list[Product]


@dataclass
class GroceryProductPageData(User, Kitchen):
    product: GroceryProduct
    has_expiry_date: bool
