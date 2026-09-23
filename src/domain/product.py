from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Categoria:
    id_categoria: Optional[int]
    nombre_categoria: str
    descripcion: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.nombre_categoria or not self.nombre_categoria.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío.")


@dataclass
class Producto:
    id_producto: Optional[int]
    codigo: str
    nombre: str
    precio_venta: float
    id_categoria: int
    estado: int = 1

    def __post_init__(self) -> None:
        if not self.codigo or not self.codigo.strip():
            raise ValueError("El código del producto no puede estar vacío.")
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío.")
        if self.precio_venta < 0.0:
            raise ValueError("El precio de venta no puede ser negativo.")
        if self.estado not in (0, 1):
            raise ValueError("El estado del producto debe ser 0 (inactivo) o 1 (activo).")
        if self.id_categoria <= 0:
            raise ValueError("El ID de categoría debe ser un entero positivo.")

    def esta_activo(self) -> bool:
        return self.estado == 1
