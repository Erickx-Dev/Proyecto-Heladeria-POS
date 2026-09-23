from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.exceptions import ValidacionError


@dataclass
class Merma:

    id_merma: Optional[int] = None
    id_insumo: int = 0
    cantidad: float = 0.0
    motivo: str = ""
    fecha_hora: str = ""
    id_usuario: int = 0

    def validar(self) -> None:
        if self.id_insumo <= 0:
            raise ValidacionError("El id_insumo debe ser un identificador válido.")

        if self.cantidad <= 0.0:
            raise ValidacionError("La cantidad de merma debe ser mayor a cero.")

        if not self.motivo or not self.motivo.strip():
            raise ValidacionError("El motivo de la merma no puede estar vacío.")

        if self.id_usuario <= 0:
            raise ValidacionError("El id_usuario debe ser un identificador válido.")
