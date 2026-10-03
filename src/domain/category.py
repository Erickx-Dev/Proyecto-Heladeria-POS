from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.exceptions import ValidacionError


@dataclass
class Categoria:

    id_categoria: Optional[int] = None
    nombre_categoria: str = ""
    descripcion: Optional[str] = None

    def validar(self) -> None:
        if not self.nombre_categoria or not self.nombre_categoria.strip():
            raise ValidacionError("El nombre de la categoría no puede estar vacío.")
