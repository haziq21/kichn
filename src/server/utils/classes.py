"""
This module provides dataclasses to work with application-specific data.

Authored by Lohith Tanuku
"""

from dataclasses import dataclass


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


@dataclass
class InventoryList:
    products: list[InventoryProduct]
    kitchen_name: str
    kitchen_id: str


@dataclass
class GroceryList:
    products: list[GroceryProduct]
    kitchen_name: str
    kitchen_id: str


@dataclass
class InventoryPageData(User, Kitchen):
    products: list[InventoryProduct]


@dataclass
class GroceryPageData(User, Kitchen):
    products: list[GroceryProduct]


@dataclass
class KitchensPageData(User):
    kitchens: list[Kitchen]


@dataclass
class CustomPageData(User):
    products: list[Product]
