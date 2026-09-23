"""
Excepciones de Dominio y Negocio del Sistema.

Define los errores personalizados para la lógica comercial, catálogo,
inventario y operaciones transaccionales.
"""

from __future__ import annotations


class HeladeriaPOSException(Exception):
    """Excepción base para todos los errores de la aplicación."""
    pass


class CatalogoError(HeladeriaPOSException):
    """Excepción base para errores en el catálogo de productos y categorías."""
    pass


class CategoriaNoEncontradaError(CatalogoError):
    """Lanzada cuando no se localiza una categoría solicitada."""
    pass


class ProductoNoEncontradoError(CatalogoError):
    """Lanzada cuando no se localiza un producto solicitado."""
    pass


class InsumoNoEncontradoError(HeladeriaPOSException):
    """Lanzada cuando no se localiza un insumo o materia prima."""
    pass


class EntidadDuplicadaError(CatalogoError):
    """Lanzada cuando se intenta registrar un registro con clave o código único ya existente."""
    pass


class ReglaNegocioError(HeladeriaPOSException):
    """Lanzada ante violaciones de validaciones o restricciones lógicas de negocio."""
    pass
