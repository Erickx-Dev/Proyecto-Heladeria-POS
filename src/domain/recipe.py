from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.exceptions import ValidacionError


@dataclass
class Receta:

    id_receta: Optional[int] = None
    id_producto: int = 0
    id_insumo: int = 0
    cantidad_necesaria: float = 0.0

    def validar(self) -> None:
        if not isinstance(self.id_producto, int) or self.id_producto <= 0:
            raise ValidacionError("El id_producto debe ser un entero positivo.")

        if not isinstance(self.id_insumo, int) or self.id_insumo <= 0:
            raise ValidacionError("El id_insumo debe ser un entero positivo.")

        if not isinstance(self.cantidad_necesaria, (int, float)) or self.cantidad_necesaria <= 0.0:
            raise ValidacionError("La cantidad_necesaria debe ser un valor numérico mayor a cero.")
