from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.core.exceptions import ValidacionError
from src.domain.category import Categoria


class CategoryRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _fila_a_categoria(self, fila: sqlite3.Row) -> Categoria:
        return Categoria(
            id_categoria=fila["id_categoria"],
            nombre_categoria=fila["nombre_categoria"],
            descripcion=fila["descripcion"],
        )

    def crear_categoria(self, categoria: Categoria) -> int:
        categoria.validar()
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO Categoria (nombre_categoria, descripcion) VALUES (?, ?);",
                (categoria.nombre_categoria.strip(), categoria.descripcion),
            )
            return cursor.lastrowid

    def obtener_por_id(self, id_categoria: int) -> Optional[Categoria]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_categoria, nombre_categoria, descripcion FROM Categoria WHERE id_categoria = ?;",
                (id_categoria,),
            )
            fila = cursor.fetchone()
            return self._fila_a_categoria(fila) if fila else None

    def obtener_por_nombre(self, nombre_categoria: str) -> Optional[Categoria]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_categoria, nombre_categoria, descripcion FROM Categoria WHERE LOWER(nombre_categoria) = LOWER(?);",
                (nombre_categoria.strip(),),
            )
            fila = cursor.fetchone()
            return self._fila_a_categoria(fila) if fila else None

    def actualizar_categoria(self, categoria: Categoria) -> bool:
        if not categoria.id_categoria:
            raise ValidacionError("Se requiere id_categoria para actualizar.")
        categoria.validar()
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE Categoria SET nombre_categoria = ?, descripcion = ? WHERE id_categoria = ?;",
                (categoria.nombre_categoria.strip(), categoria.descripcion, categoria.id_categoria),
            )
            return cursor.rowcount > 0

    def eliminar_categoria(self, id_categoria: int) -> bool:
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM Categoria WHERE id_categoria = ?;",
                (id_categoria,),
            )
            return cursor.rowcount > 0

    def listar_categorias(self) -> List[Categoria]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_categoria, nombre_categoria, descripcion FROM Categoria ORDER BY nombre_categoria;",
            )
            return [self._fila_a_categoria(fila) for fila in cursor.fetchall()]
