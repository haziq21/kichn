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
class Product:
    name: str
    barcode: int
    amount: int
    category: str
    id: str


@dataclass
class User:
    email: str
    username: str
