from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.domain.cash_register import TurnoCaja


class CashRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _fila_a_turno_caja(self, fila: sqlite3.Row) -> TurnoCaja:
        return TurnoCaja(
            id_caja=fila["id_caja"],
            id_usuario=fila["id_usuario"],
            fecha_apertura=fila["fecha_apertura"],
            monto_inicial=fila["monto_inicial"],
            fecha_cierre=fila["fecha_cierre"],
            monto_final_real=fila["monto_final_real"],
            diferencia=fila["diferencia"],
            estado=fila["estado"],
        )

    def abrir_caja(self, id_usuario: int, monto_inicial: float, fecha_hora: str) -> int:
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO Caja (id_usuario, fecha_apertura, monto_inicial, estado) "
                "VALUES (?, ?, ?, 'ABIERTA');",
                (id_usuario, fecha_hora, monto_inicial),
            )
            return cursor.lastrowid

    def obtener_caja_activa(self) -> Optional[TurnoCaja]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_caja, id_usuario, fecha_apertura, monto_inicial, "
                "fecha_cierre, monto_final_real, diferencia, estado "
                "FROM Caja WHERE estado = 'ABIERTA' LIMIT 1;",
            )
            fila = cursor.fetchone()
            return self._fila_a_turno_caja(fila) if fila else None

    def cerrar_caja(
        self, id_caja: int, monto_final_real: float, diferencia: float, fecha_hora: str,
    ) -> bool:
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE Caja SET monto_final_real = ?, diferencia = ?, "
                "fecha_cierre = ?, estado = 'CERRADA' WHERE id_caja = ?;",
                (monto_final_real, diferencia, fecha_hora, id_caja),
            )
            return cursor.rowcount > 0

    def obtener_caja_por_id(self, id_caja: int) -> Optional[TurnoCaja]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_caja, id_usuario, fecha_apertura, monto_inicial, "
                "fecha_cierre, monto_final_real, diferencia, estado "
                "FROM Caja WHERE id_caja = ?;",
                (id_caja,),
            )
            fila = cursor.fetchone()
            return self._fila_a_turno_caja(fila) if fila else None

    def obtener_total_ventas_efectivo(self, id_caja: int) -> float:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT COALESCE(SUM(total), 0.0) FROM Venta "
                "WHERE id_caja = ? AND metodo_pago = 'EFECTIVO';",
                (id_caja,),
            )
            fila = cursor.fetchone()
            return float(fila[0])
