from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.exceptions import MermaInvalidaError


@dataclass
class Merma:
    id_insumo: int
    cantidad: float
    motivo: str
    fecha_hora: str
    id_usuario: int
    id_merma: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        if self.id_insumo <= 0:
            raise MermaInvalidaError("El ID del insumo debe ser mayor a cero.")
        if self.id_usuario <= 0:
            raise MermaInvalidaError("El ID del usuario responsable debe ser mayor a cero.")
        if self.cantidad <= 0.0:
            raise MermaInvalidaError("La cantidad mermada debe ser mayor a cero.")
        if not self.motivo or not self.motivo.strip():
            raise MermaInvalidaError("El motivo o justificación de la merma no puede estar vacío.")
        if not self.fecha_hora or not self.fecha_hora.strip():
            raise MermaInvalidaError("La fecha y hora del registro no pueden estar vacías.")
