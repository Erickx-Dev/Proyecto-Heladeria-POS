from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.exceptions import DescripcionGastoVaciaError, MontoInvalidoError


@dataclass
class Gasto:

    id_gasto: Optional[int] = None
    id_caja: int = 0
    fecha_hora: str = ""
    monto: float = 0.0
    descripcion: str = ""
    id_usuario: int = 0

    def validar(self) -> None:
        if self.monto <= 0.0:
            raise MontoInvalidoError(
                "El monto del gasto debe ser estrictamente mayor a cero."
            )

        if not self.descripcion or not self.descripcion.strip():
            raise DescripcionGastoVaciaError()
