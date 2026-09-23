"""
Paquete de Dominio del Sistema.

Exporta las entidades puras de negocio modeladas con dataclasses.
"""

from .category import Categoria
from .product import Producto, ProductoCompuesto, ProductoSimple
from .supply import Insumo

__all__ = [
    "Categoria",
    "Insumo",
    "Producto",
    "ProductoSimple",
    "ProductoCompuesto",
]
