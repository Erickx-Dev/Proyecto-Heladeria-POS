from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.domain.cash_register import ESTADO_ABIERTA, ESTADO_CERRADA, TurnoCaja
from src.domain.expense import Gasto


class CashRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def crear_caja(self, caja: TurnoCaja) -> int:
        with get_db_transaction(db_path=self._db_path) as conn:
            cursor: sqlite3.Cursor = conn.execute(
                """
                INSERT INTO Caja (id_usuario, fecha_apertura, monto_inicial, estado)
                VALUES (?, ?, ?, ?)
                """,
                (
                    caja.id_usuario,
                    caja.fecha_apertura,
                    caja.monto_inicial,
                    caja.estado,
                ),
            )
            id_generado: int = cursor.lastrowid
            return id_generado

    def obtener_caja_por_id(self, id_caja: int) -> Optional[TurnoCaja]:
        with get_db_cursor(db_path=self._db_path) as cursor:
            cursor.execute(
                """
                SELECT id_caja, id_usuario, fecha_apertura, monto_inicial,
                       fecha_cierre, monto_final_real, diferencia, estado
                FROM Caja
                WHERE id_caja = ?
                """,
                (id_caja,),
            )
            fila: Optional[sqlite3.Row] = cursor.fetchone()
            if fila is None:
                return None
            return self._fila_a_turno_caja(fila)

    def obtener_caja_activa(
        self, id_usuario: Optional[int] = None
    ) -> Optional[TurnoCaja]:
        with get_db_cursor(db_path=self._db_path) as cursor:
            if id_usuario is not None:
                cursor.execute(
                    """
                    SELECT id_caja, id_usuario, fecha_apertura, monto_inicial,
                           fecha_cierre, monto_final_real, diferencia, estado
                    FROM Caja
                    WHERE estado = ? AND id_usuario = ?
                    ORDER BY id_caja DESC
                    LIMIT 1
                    """,
                    (ESTADO_ABIERTA, id_usuario),
                )
            else:
                cursor.execute(
                    """
                    SELECT id_caja, id_usuario, fecha_apertura, monto_inicial,
                           fecha_cierre, monto_final_real, diferencia, estado
                    FROM Caja
                    WHERE estado = ?
                    ORDER BY id_caja DESC
                    LIMIT 1
                    """,
                    (ESTADO_ABIERTA,),
                )
            fila: Optional[sqlite3.Row] = cursor.fetchone()
            if fila is None:
                return None
            return self._fila_a_turno_caja(fila)

    def actualizar_cierre_caja(
        self,
        id_caja: int,
        fecha_cierre: str,
        monto_final_real: float,
        diferencia: float,
    ) -> None:
        with get_db_transaction(db_path=self._db_path) as conn:
            conn.execute(
                """
                UPDATE Caja
                SET fecha_cierre = ?,
                    monto_final_real = ?,
                    diferencia = ?,
                    estado = ?
                WHERE id_caja = ?
                """,
                (fecha_cierre, monto_final_real, diferencia, ESTADO_CERRADA, id_caja),
            )

    def registrar_gasto(self, gasto: Gasto) -> int:
        with get_db_transaction(db_path=self._db_path) as conn:
            cursor: sqlite3.Cursor = conn.execute(
                """
                INSERT INTO Gasto (id_caja, fecha_hora, monto, descripcion, id_usuario)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    gasto.id_caja,
                    gasto.fecha_hora,
                    gasto.monto,
                    gasto.descripcion,
                    gasto.id_usuario,
                ),
            )
            id_generado: int = cursor.lastrowid
            return id_generado

    def obtener_gastos_por_caja(self, id_caja: int) -> List[Gasto]:
        with get_db_cursor(db_path=self._db_path) as cursor:
            cursor.execute(
                """
                SELECT id_gasto, id_caja, fecha_hora, monto, descripcion, id_usuario
                FROM Gasto
                WHERE id_caja = ?
                ORDER BY id_gasto ASC
                """,
                (id_caja,),
            )
            filas: List[sqlite3.Row] = cursor.fetchall()
            return [self._fila_a_gasto(fila) for fila in filas]

    def obtener_total_gastos_por_caja(self, id_caja: int) -> float:
        with get_db_cursor(db_path=self._db_path) as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(monto), 0.0) AS total_gastos
                FROM Gasto
                WHERE id_caja = ?
                """,
                (id_caja,),
            )
            resultado: sqlite3.Row = cursor.fetchone()
            return float(resultado["total_gastos"])

    def obtener_total_ventas_efectivo(self, id_caja: int) -> float:
        with get_db_cursor(db_path=self._db_path) as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(total), 0.0) AS total_ventas
                FROM Venta
                WHERE id_caja = ? AND metodo_pago = 'EFECTIVO'
                """,
                (id_caja,),
            )
            resultado: sqlite3.Row = cursor.fetchone()
            return float(resultado["total_ventas"])

    def registrar_auditoria(
        self,
        id_usuario: int,
        accion: str,
        modulo: str,
        detalles: Optional[str] = None,
    ) -> None:
        fecha_hora: str = datetime.now().isoformat(sep=" ", timespec="seconds")
        with get_db_transaction(db_path=self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles)
                VALUES (?, ?, ?, ?, ?)
                """,
                (id_usuario, accion, modulo, fecha_hora, detalles),
            )

    @staticmethod
    def _fila_a_turno_caja(fila: sqlite3.Row) -> TurnoCaja:
        return TurnoCaja(
            id_caja=fila["id_caja"],
            id_usuario=fila["id_usuario"],
            fecha_apertura=fila["fecha_apertura"],
            monto_inicial=float(fila["monto_inicial"]),
            fecha_cierre=fila["fecha_cierre"],
            monto_final_real=(
                float(fila["monto_final_real"])
                if fila["monto_final_real"] is not None
                else None
            ),
            diferencia=(
                float(fila["diferencia"])
                if fila["diferencia"] is not None
                else None
            ),
            estado=fila["estado"],
        )

    @staticmethod
    def _fila_a_gasto(fila: sqlite3.Row) -> Gasto:
        return Gasto(
            id_gasto=fila["id_gasto"],
            id_caja=fila["id_caja"],
            fecha_hora=fila["fecha_hora"],
            monto=float(fila["monto"]),
            descripcion=fila["descripcion"],
            id_usuario=fila["id_usuario"],
        )
