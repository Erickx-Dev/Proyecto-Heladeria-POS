from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.core.exceptions import ValidacionError
from src.domain.recipe import Receta


class RecipeRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _fila_a_receta(self, fila: sqlite3.Row) -> Receta:
        return Receta(
            id_receta=fila["id_receta"],
            id_producto=fila["id_producto"],
            id_insumo=fila["id_insumo"],
            cantidad_necesaria=fila["cantidad_necesaria"],
        )

    def asociar_insumo_a_producto(
        self,
        id_producto: int,
        id_insumo: int,
        cantidad_necesaria: float,
    ) -> int:
        receta = Receta(
            id_producto=id_producto,
            id_insumo=id_insumo,
            cantidad_necesaria=cantidad_necesaria,
        )
        receta.validar()

        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT id_receta FROM Receta WHERE id_producto = ? AND id_insumo = ?;",
                (id_producto, id_insumo),
            )
            existente = cursor.fetchone()
            if existente:
                conn.execute(
                    "UPDATE Receta SET cantidad_necesaria = ? WHERE id_receta = ?;",
                    (cantidad_necesaria, existente["id_receta"]),
                )
                return existente["id_receta"]

            cursor = conn.execute(
                "INSERT INTO Receta (id_producto, id_insumo, cantidad_necesaria) VALUES (?, ?, ?);",
                (id_producto, id_insumo, cantidad_necesaria),
            )
            return cursor.lastrowid

    def obtener_receta_por_producto(self, id_producto: int) -> List[Receta]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_receta, id_producto, id_insumo, cantidad_necesaria FROM Receta WHERE id_producto = ? ORDER BY id_receta;",
                (id_producto,),
            )
            return [self._fila_a_receta(fila) for fila in cursor.fetchall()]

    def obtener_receta_por_id(self, id_receta: int) -> Optional[Receta]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_receta, id_producto, id_insumo, cantidad_necesaria FROM Receta WHERE id_receta = ?;",
                (id_receta,),
            )
            fila = cursor.fetchone()
            return self._fila_a_receta(fila) if fila else None

    def eliminar_insumo_de_receta(self, id_receta: int) -> bool:
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM Receta WHERE id_receta = ?;",
                (id_receta,),
            )
            return cursor.rowcount > 0

    def eliminar_receta_por_producto(self, id_producto: int) -> bool:
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM Receta WHERE id_producto = ?;",
                (id_producto,),
            )
            return cursor.rowcount > 0
