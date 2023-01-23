"""
This module provides dataclasses to work with application-specific data.

Authored by Lohith Tanuku
"""

from dataclasses import dataclass


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
    barcode: int
    amount: int
    category: str
    id: str


@dataclass
class InventoryProduct(Product):
    closest_expiry_date: int
    amount_expiring: int


@dataclass
class InventoryList:
    products: list[InventoryProduct]
    kitchen_name: str
    kitchen_id: str


@dataclass
class GroceryList:
    products: list[Product]
    kitchen_name: str
    kitchen_id: str
