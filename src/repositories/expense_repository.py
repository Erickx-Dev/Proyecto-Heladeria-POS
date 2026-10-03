from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.domain.expense import Gasto


class ExpenseRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _fila_a_gasto(self, fila: sqlite3.Row) -> Gasto:
        """Convierte un sqlite3.Row a la entidad de dominio Gasto."""
        return Gasto(
            id_gasto=fila["id_gasto"],
            id_caja=fila["id_caja"],
            fecha_hora=fila["fecha_hora"],
            monto=fila["monto"],
            descripcion=fila["descripcion"],
            id_usuario=fila["id_usuario"],
        )

    def registrar_gasto(self, gasto: Gasto) -> int:
        """Inserta un nuevo gasto y retorna el id_gasto generado."""
        gasto.validar()
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO Gasto (id_caja, fecha_hora, monto, descripcion, id_usuario) "
                "VALUES (?, ?, ?, ?, ?);",
                (gasto.id_caja, gasto.fecha_hora, gasto.monto,
                 gasto.descripcion, gasto.id_usuario),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def listar_gastos_por_caja(self, id_caja: int) -> List[Gasto]:
        """Lista todos los gastos registrados para un turno de caja específico."""
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_gasto, id_caja, fecha_hora, monto, descripcion, id_usuario "
                "FROM Gasto WHERE id_caja = ? ORDER BY id_gasto;",
                (id_caja,),
            )
            return [self._fila_a_gasto(fila) for fila in cursor.fetchall()]

    def calcular_total_gastos(self, id_caja: int) -> float:
        """Calcula la suma total de gastos para un turno de caja."""
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT COALESCE(SUM(monto), 0.0) FROM Gasto WHERE id_caja = ?;",
                (id_caja,),
            )
            fila = cursor.fetchone()
            return float(fila[0])
