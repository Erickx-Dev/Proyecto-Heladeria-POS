"""
Módulo Core del Sistema.

Contiene utilidades transversales, seguridad criptográfica y excepciones.
"""

from .exceptions import (
    CatalogoError,
    CategoriaNoEncontradaError,
    EntidadDuplicadaError,
    HeladeriaPOSException,
    InsumoNoEncontradoError,
    ProductoNoEncontradoError,
    ReglaNegocioError,
)

__all__ = [
    "HeladeriaPOSException",
    "CatalogoError",
    "CategoriaNoEncontradaError",
    "ProductoNoEncontradoError",
    "InsumoNoEncontradoError",
    "EntidadDuplicadaError",
    "ReglaNegocioError",
]
