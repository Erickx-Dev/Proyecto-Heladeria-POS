"""
Paquete de Repositorios de Acceso a Datos.

Contiene los repositorios que interactúan directamente con SQLite3.
"""

from .category_repository import CategoryRepository
from .product_repository import ProductRepository
from .supply_repository import SupplyRepository

__all__ = [
    "CategoryRepository",
    "ProductRepository",
    "SupplyRepository",
]
