from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.domain.loss import Merma


class LossRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _fila_a_merma(self, fila: sqlite3.Row) -> Merma:
        return Merma(
            id_merma=fila["id_merma"],
            id_insumo=fila["id_insumo"],
            cantidad=fila["cantidad"],
            motivo=fila["motivo"],
            fecha_hora=fila["fecha_hora"],
            id_usuario=fila["id_usuario"],
        )

    def registrar_merma(self, merma: Merma) -> int:
        merma.validar()
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO Merma (id_insumo, cantidad, motivo, fecha_hora, id_usuario) VALUES (?, ?, ?, ?, ?);",
                (merma.id_insumo, merma.cantidad, merma.motivo.strip(), merma.fecha_hora, merma.id_usuario),
            )
            return cursor.lastrowid

    def obtener_por_id(self, id_merma: int) -> Optional[Merma]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_merma, id_insumo, cantidad, motivo, fecha_hora, id_usuario FROM Merma WHERE id_merma = ?;",
                (id_merma,),
            )
            fila = cursor.fetchone()
            return self._fila_a_merma(fila) if fila else None

    def listar_mermas(self, id_insumo: Optional[int] = None) -> List[Merma]:
        query = "SELECT id_merma, id_insumo, cantidad, motivo, fecha_hora, id_usuario FROM Merma WHERE 1=1"
        params: List[int] = []

        if id_insumo is not None:
            query += " AND id_insumo = ?"
            params.append(id_insumo)

        query += " ORDER BY fecha_hora DESC, id_merma DESC;"

        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(query, tuple(params))
            return [self._fila_a_merma(fila) for fila in cursor.fetchall()]
