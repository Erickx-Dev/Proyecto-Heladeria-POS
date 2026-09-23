from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.domain.sale import DetalleVenta, Venta


class SaleRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path = db_path

    def registrar_venta_transaccional(
        self, venta: Venta, conn: Optional[sqlite3.Connection] = None
    ) -> int:
        sql_venta = (
            "INSERT INTO Venta (id_caja, fecha_hora, total, metodo_pago, dinero_recibido, cambio) "
            "VALUES (?, ?, ?, ?, ?, ?);"
        )
        sql_detalle = (
            "INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario, subtotal) "
            "VALUES (?, ?, ?, ?, ?);"
        )

        def ejecutar_insercion(c: sqlite3.Cursor) -> int:
            c.execute(
                sql_venta,
                (
                    venta.id_caja,
                    venta.fecha_hora,
                    venta.total,
                    venta.metodo_pago,
                    venta.dinero_recibido,
                    venta.cambio,
                ),
            )
            id_venta = c.lastrowid
            for det in venta.detalles:
                c.execute(
                    sql_detalle,
                    (
                        id_venta,
                        det.id_producto,
                        det.cantidad,
                        det.precio_unitario,
                        det.subtotal,
                    ),
                )
                det.id_detalle = c.lastrowid
                det.id_venta = id_venta
            return id_venta

        if conn is not None:
            return ejecutar_insercion(conn.cursor())

        with get_db_transaction(self._db_path) as transaction_conn:
            cursor = transaction_conn.cursor()
            id_generado = ejecutar_insercion(cursor)
            return id_generado

    def obtener_venta_por_id(self, id_venta: int) -> Optional[Venta]:
        sql_venta = (
            "SELECT id_venta, id_caja, fecha_hora, total, metodo_pago, dinero_recibido, cambio "
            "FROM Venta WHERE id_venta = ?;"
        )
        sql_detalles = (
            "SELECT d.id_detalle, d.id_venta, d.id_producto, d.cantidad, d.precio_unitario, d.subtotal, "
            "p.nombre AS nombre_producto "
            "FROM DetalleVenta d "
            "INNER JOIN Producto p ON d.id_producto = p.id_producto "
            "WHERE d.id_venta = ? ORDER BY d.id_detalle ASC;"
        )
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql_venta, (id_venta,))
            fila_venta = cursor.fetchone()
            if fila_venta is None:
                return None

            cursor.execute(sql_detalles, (id_venta,))
            filas_detalles = cursor.fetchall()
            detalles = [
                DetalleVenta(
                    id_detalle=f["id_detalle"],
                    id_venta=f["id_venta"],
                    id_producto=f["id_producto"],
                    cantidad=int(f["cantidad"]),
                    precio_unitario=float(f["precio_unitario"]),
                    subtotal=float(f["subtotal"]),
                    nombre_producto=f["nombre_producto"],
                )
                for f in filas_detalles
            ]

            return Venta(
                id_venta=fila_venta["id_venta"],
                id_caja=fila_venta["id_caja"],
                fecha_hora=fila_venta["fecha_hora"],
                total=float(fila_venta["total"]),
                metodo_pago=fila_venta["metodo_pago"],
                dinero_recibido=float(fila_venta["dinero_recibido"]),
                cambio=float(fila_venta["cambio"]),
                detalles=detalles,
            )

    def listar_ventas_por_caja(self, id_caja: int) -> List[Venta]:
        sql = (
            "SELECT id_venta, id_caja, fecha_hora, total, metodo_pago, dinero_recibido, cambio "
            "FROM Venta WHERE id_caja = ? ORDER BY id_venta ASC;"
        )
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql, (id_caja,))
            filas = cursor.fetchall()
            ventas: List[Venta] = []
            for f in filas:
                venta = self.obtener_venta_por_id(f["id_venta"])
                if venta is not None:
                    ventas.append(venta)
            return ventas

    def obtener_total_ventas_caja(self, id_caja: int) -> float:
        sql = "SELECT coalesce(sum(total), 0.0) AS total_ventas FROM Venta WHERE id_caja = ?;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql, (id_caja,))
            fila = cursor.fetchone()
            return float(fila["total_ventas"]) if fila else 0.0

    def obtener_siguiente_consecutivo(self) -> int:
        sql = "SELECT coalesce(max(id_venta), 0) + 1 AS siguiente FROM Venta;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql)
            fila = cursor.fetchone()
            return int(fila["siguiente"]) if fila else 1
