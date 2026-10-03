from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.exceptions import ValidacionError


@dataclass
class AuditoriaLog:

    id_log: Optional[int] = None
    id_usuario: Optional[int] = None
    accion: str = ""
    modulo: str = ""
    fecha_hora: str = ""
    detalles: Optional[str] = None

    def validar(self) -> None:
        if not self.accion or not self.accion.strip():
            raise ValidacionError("La acción de auditoría no puede estar vacía.")

        if not self.modulo or not self.modulo.strip():
            raise ValidacionError("El módulo de auditoría no puede estar vacío.")
