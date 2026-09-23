from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.exceptions import MontoInvalidoError, ValidacionError


@dataclass
class Gasto:

    id_gasto: Optional[int] = None
    id_caja: int = 0
    fecha_hora: str = ""
    monto: float = 0.0
    descripcion: str = ""
    id_usuario: int = 0

    def validar(self) -> None:
        if self.id_caja <= 0:
            raise ValidacionError("El id_caja debe ser un identificador válido.")

        if self.monto <= 0.0:
            raise MontoInvalidoError("El monto del gasto debe ser estrictamente mayor a cero.")

        if not self.descripcion or not self.descripcion.strip():
            raise ValidacionError("La descripción del gasto no puede estar vacía.")

        if self.id_usuario <= 0:
            raise ValidacionError("El id_usuario debe ser un identificador válido.")
