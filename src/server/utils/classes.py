"""
This module provides dataclasses to work with application-specific data.
"""

from dataclasses import dataclass

@dataclass
class Kitchen:
    name: str 
    emails: list[str] 

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