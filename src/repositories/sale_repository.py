from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.core.exceptions import StockInsuficienteError, ValidacionError
from src.domain.audit import AuditoriaLog
from src.domain.sale import DetalleVenta, Venta
from src.repositories.audit_repository import AuditRepository


class SaleRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    @staticmethod
    def _fila_a_venta(fila: sqlite3.Row) -> Venta:
        return Venta(
            id_venta=fila["id_venta"],
            id_caja=fila["id_caja"],
            fecha_hora=fila["fecha_hora"],
            total=fila["total"],
            metodo_pago=fila["metodo_pago"],
            dinero_recibido=fila["dinero_recibido"],
            cambio=fila["cambio"],
        )

    @staticmethod
    def _fila_a_detalle(fila: sqlite3.Row) -> DetalleVenta:
        return DetalleVenta(
            id_detalle=fila["id_detalle"],
            id_venta=fila["id_venta"],
            id_producto=fila["id_producto"],
            cantidad=fila["cantidad"],
            precio_unitario=fila["precio_unitario"],
            subtotal=fila["subtotal"],
        )

    def registrar_venta(self, venta: Venta, id_usuario: Optional[int] = None) -> int:
        """
        Persiste la venta de forma atómica (todo o nada):
        cabecera, detalles, descuento de insumos por receta y auditoría.
        Cualquier fallo provoca rollback completo.
        """
        venta.validar()
        if not venta.detalles:
            raise ValidacionError("La venta debe contener al menos un producto.")

        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO Venta (id_caja, fecha_hora, total, metodo_pago, dinero_recibido, cambio) "
                "VALUES (?, ?, ?, ?, ?, ?);",
                (
                    venta.id_caja,
                    venta.fecha_hora,
                    venta.total,
                    venta.metodo_pago,
                    venta.dinero_recibido,
                    venta.cambio,
                ),
            )
            id_venta: int = cursor.lastrowid

            for detalle in venta.detalles:
                detalle.validar()
                conn.execute(
                    "INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario, subtotal) "
                    "VALUES (?, ?, ?, ?, ?);",
                    (
                        id_venta,
                        detalle.id_producto,
                        detalle.cantidad,
                        detalle.precio_unitario,
                        detalle.subtotal,
                    ),
                )
                self._descontar_insumos_por_receta(conn, detalle)

            AuditRepository.insertar_en_conexion(
                conn,
                AuditoriaLog(
                    id_usuario=id_usuario,
                    accion="VENTA_REGISTRADA",
                    modulo="POS",
                    fecha_hora=venta.fecha_hora,
                    detalles=(
                        f"Venta id={id_venta} caja={venta.id_caja} "
                        f"total=${venta.total:,.2f} metodo={venta.metodo_pago} "
                        f"items={len(venta.detalles)}."
                    ),
                ),
            )
            return id_venta

    @staticmethod
    def _descontar_insumos_por_receta(conn: sqlite3.Connection, detalle: DetalleVenta) -> None:
        recetas = conn.execute(
            "SELECT id_insumo, cantidad_necesaria FROM Receta WHERE id_producto = ?;",
            (detalle.id_producto,),
        ).fetchall()

        for receta in recetas:
            requerido: float = round(float(receta["cantidad_necesaria"]) * detalle.cantidad, 4)
            fila = conn.execute(
                "SELECT nombre, stock_actual FROM Insumo WHERE id_insumo = ?;",
                (receta["id_insumo"],),
            ).fetchone()
            if fila is None:
                raise ValidacionError(f"No existe el insumo con id {receta['id_insumo']}.")

            stock_actual: float = float(fila["stock_actual"])
            if requerido > stock_actual:
                raise StockInsuficienteError(
                    f"Stock insuficiente para {fila['nombre']}. "
                    f"Disponible: {stock_actual}, Requerido: {requerido}."
                )

            conn.execute(
                "UPDATE Insumo SET stock_actual = ? WHERE id_insumo = ?;",
                (round(stock_actual - requerido, 4), receta["id_insumo"]),
            )

    def obtener_venta_por_id(self, id_venta: int) -> Optional[Venta]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_venta, id_caja, fecha_hora, total, metodo_pago, dinero_recibido, cambio "
                "FROM Venta WHERE id_venta = ?;",
                (id_venta,),
            )
            fila = cursor.fetchone()
            if fila is None:
                return None
            venta: Venta = self._fila_a_venta(fila)

            cursor.execute(
                "SELECT id_detalle, id_venta, id_producto, cantidad, precio_unitario, subtotal "
                "FROM DetalleVenta WHERE id_venta = ? ORDER BY id_detalle;",
                (id_venta,),
            )
            venta.detalles = [self._fila_a_detalle(f) for f in cursor.fetchall()]
            return venta

    def listar_ventas_por_caja(self, id_caja: int) -> List[Venta]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_venta, id_caja, fecha_hora, total, metodo_pago, dinero_recibido, cambio "
                "FROM Venta WHERE id_caja = ? ORDER BY id_venta;",
                (id_caja,),
            )
            return [self._fila_a_venta(fila) for fila in cursor.fetchall()]
