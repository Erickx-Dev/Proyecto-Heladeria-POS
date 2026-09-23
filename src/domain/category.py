from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Categoria:
    nombre_categoria: str
    id_categoria: Optional[int] = None
    descripcion: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.nombre_categoria or not self.nombre_categoria.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío ni contener solo espacios.")
        self.nombre_categoria = self.nombre_categoria.strip()
        if self.descripcion is not None:
            self.descripcion = self.descripcion.strip()
