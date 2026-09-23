from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.exceptions import ValidacionError


@dataclass
class Producto:

    id_producto: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    precio_venta: float = 0.0
    id_categoria: int = 0
    estado: int = 1

    def es_activo(self) -> bool:
        return self.estado == 1

    def validar(self) -> None:
        if not self.codigo or not self.codigo.strip():
            raise ValidacionError("El código del producto no puede estar vacío.")

        if not self.nombre or not self.nombre.strip():
            raise ValidacionError("El nombre del producto no puede estar vacío.")

        if self.precio_venta < 0.0:
            raise ValidacionError("El precio de venta no puede ser negativo.")

        if self.id_categoria <= 0:
            raise ValidacionError("El id_categoria debe ser un identificador válido.")

        if self.estado not in (0, 1):
            raise ValidacionError("El estado debe ser 1 (Activo) o 0 (Inactivo).")
