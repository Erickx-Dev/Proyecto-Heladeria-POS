from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.domain.inventory import Insumo
from src.domain.waste import Merma


class InventoryRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path = db_path

    def obtener_insumo_por_id(
        self, id_insumo: int, conn: Optional[sqlite3.Connection] = None
    ) -> Optional[Insumo]:
        sql = "SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo FROM Insumo WHERE id_insumo = ?;"
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql, (id_insumo,))
            fila = cursor.fetchone()
        else:
            with get_db_cursor(self._db_path) as cursor:
                cursor.execute(sql, (id_insumo,))
                fila = cursor.fetchone()

        if fila is None:
            return None
        return Insumo(
            id_insumo=fila["id_insumo"],
            nombre=fila["nombre"],
            unidad_medida=fila["unidad_medida"],
            stock_actual=float(fila["stock_actual"]),
            stock_minimo=float(fila["stock_minimo"]),
        )

    def obtener_insumo_por_nombre(self, nombre: str) -> Optional[Insumo]:
        sql = "SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo FROM Insumo WHERE trim(lower(nombre)) = trim(lower(?));"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql, (nombre,))
            fila = cursor.fetchone()
            if fila is None:
                return None
            return Insumo(
                id_insumo=fila["id_insumo"],
                nombre=fila["nombre"],
                unidad_medida=fila["unidad_medida"],
                stock_actual=float(fila["stock_actual"]),
                stock_minimo=float(fila["stock_minimo"]),
            )

    def listar_insumos(self) -> List[Insumo]:
        sql = "SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo FROM Insumo ORDER BY nombre ASC;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                Insumo(
                    id_insumo=fila["id_insumo"],
                    nombre=fila["nombre"],
                    unidad_medida=fila["unidad_medida"],
                    stock_actual=float(fila["stock_actual"]),
                    stock_minimo=float(fila["stock_minimo"]),
                )
                for fila in filas
            ]

    def crear_insumo(self, insumo: Insumo) -> int:
        sql = "INSERT INTO Insumo (nombre, unidad_medida, stock_actual, stock_minimo) VALUES (?, ?, ?, ?);"
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                sql,
                (
                    insumo.nombre,
                    insumo.unidad_medida,
                    insumo.stock_actual,
                    insumo.stock_minimo,
                ),
            )
            return cursor.lastrowid

    def actualizar_insumo(self, insumo: Insumo) -> bool:
        sql = "UPDATE Insumo SET nombre = ?, unidad_medida = ?, stock_actual = ?, stock_minimo = ? WHERE id_insumo = ?;"
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                sql,
                (
                    insumo.nombre,
                    insumo.unidad_medida,
                    insumo.stock_actual,
                    insumo.stock_minimo,
                    insumo.id_insumo,
                ),
            )
            return cursor.rowcount > 0

    def descontar_stock(
        self,
        id_insumo: int,
        cantidad: float,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        sql = "UPDATE Insumo SET stock_actual = round(stock_actual - ?, 4) WHERE id_insumo = ? AND stock_actual >= ?;"
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql, (cantidad, id_insumo, cantidad))
            return cursor.rowcount > 0
        with get_db_transaction(self._db_path) as transaction_conn:
            cursor = transaction_conn.cursor()
            cursor.execute(sql, (cantidad, id_insumo, cantidad))
            return cursor.rowcount > 0

    def incrementar_stock(
        self,
        id_insumo: int,
        cantidad: float,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        sql = "UPDATE Insumo SET stock_actual = round(stock_actual + ?, 4) WHERE id_insumo = ?;"
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql, (cantidad, id_insumo))
            return cursor.rowcount > 0
        with get_db_transaction(self._db_path) as transaction_conn:
            cursor = transaction_conn.cursor()
            cursor.execute(sql, (cantidad, id_insumo))
            return cursor.rowcount > 0

    def registrar_merma(
        self,
        merma: Merma,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        sql = "INSERT INTO Merma (id_insumo, cantidad, motivo, fecha_hora, id_usuario) VALUES (?, ?, ?, ?, ?);"
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(
                sql,
                (
                    merma.id_insumo,
                    merma.cantidad,
                    merma.motivo,
                    merma.fecha_hora,
                    merma.id_usuario,
                ),
            )
            return cursor.lastrowid
        with get_db_transaction(self._db_path) as transaction_conn:
            cursor = transaction_conn.cursor()
            cursor.execute(
                sql,
                (
                    merma.id_insumo,
                    merma.cantidad,
                    merma.motivo,
                    merma.fecha_hora,
                    merma.id_usuario,
                ),
            )
            return cursor.lastrowid

    def listar_mermas(self) -> List[Merma]:
        sql = "SELECT id_merma, id_insumo, cantidad, motivo, fecha_hora, id_usuario FROM Merma ORDER BY fecha_hora DESC;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                Merma(
                    id_merma=fila["id_merma"],
                    id_insumo=fila["id_insumo"],
                    cantidad=float(fila["cantidad"]),
                    motivo=fila["motivo"],
                    fecha_hora=fila["fecha_hora"],
                    id_usuario=fila["id_usuario"],
                )
                for fila in filas
            ]

    def registrar_auditoria(
        self,
        id_usuario: Optional[int],
        accion: str,
        modulo: str,
        detalles: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        fecha_hora = datetime.now().isoformat(sep=" ", timespec="seconds")
        sql = "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) VALUES (?, ?, ?, ?, ?);"
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql, (id_usuario, accion, modulo, fecha_hora, detalles))
            return cursor.lastrowid
        with get_db_transaction(self._db_path) as transaction_conn:
            cursor = transaction_conn.cursor()
            cursor.execute(sql, (id_usuario, accion, modulo, fecha_hora, detalles))
            return cursor.lastrowid
