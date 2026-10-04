from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.core.exceptions import StockInsuficienteError, ValidacionError
from src.domain.supply import Insumo


class SupplyRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _fila_a_insumo(self, fila: sqlite3.Row) -> Insumo:
        return Insumo(
            id_insumo=fila["id_insumo"],
            nombre=fila["nombre"],
            unidad_medida=fila["unidad_medida"],
            stock_actual=fila["stock_actual"],
            stock_minimo=fila["stock_minimo"],
        )

    def crear_insumo(self, insumo: Insumo) -> int:
        insumo.validar()
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO Insumo (nombre, unidad_medida, stock_actual, stock_minimo) VALUES (?, ?, ?, ?);",
                (insumo.nombre.strip(), insumo.unidad_medida.strip(), insumo.stock_actual, insumo.stock_minimo),
            )
            return cursor.lastrowid

    def obtener_por_id(self, id_insumo: int) -> Optional[Insumo]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo FROM Insumo WHERE id_insumo = ?;",
                (id_insumo,),
            )
            fila = cursor.fetchone()
            return self._fila_a_insumo(fila) if fila else None

    def obtener_por_nombre(self, nombre: str) -> Optional[Insumo]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo FROM Insumo WHERE LOWER(nombre) = LOWER(?);",
                (nombre.strip(),),
            )
            fila = cursor.fetchone()
            return self._fila_a_insumo(fila) if fila else None

    def actualizar_insumo(self, insumo: Insumo) -> bool:
        if not insumo.id_insumo:
            raise ValidacionError("Se requiere id_insumo para actualizar.")
        insumo.validar()
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE Insumo SET nombre = ?, unidad_medida = ?, stock_actual = ?, stock_minimo = ? WHERE id_insumo = ?;",
                (insumo.nombre.strip(), insumo.unidad_medida.strip(), insumo.stock_actual, insumo.stock_minimo, insumo.id_insumo),
            )
            return cursor.rowcount > 0

    def descontar_stock(self, id_insumo: int, cantidad: float) -> bool:
        if cantidad <= 0.0:
            raise ValidacionError("La cantidad a descontar debe ser mayor a cero.")

        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT stock_actual, nombre FROM Insumo WHERE id_insumo = ?;",
                (id_insumo,),
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValidacionError(f"No existe el insumo con id {id_insumo}.")

            stock_actual = float(fila["stock_actual"])
            if cantidad > stock_actual:
                raise StockInsuficienteError(
                    f"Stock insuficiente para {fila['nombre']}. Disponible: {stock_actual}, Solicitado: {cantidad}."
                )

            nuevo_stock = round(stock_actual - cantidad, 4)
            cursor = conn.execute(
                "UPDATE Insumo SET stock_actual = ? WHERE id_insumo = ?;",
                (nuevo_stock, id_insumo),
            )
            return cursor.rowcount > 0

    def aumentar_stock(self, id_insumo: int, cantidad: float) -> bool:
        if cantidad <= 0.0:
            raise ValidacionError("La cantidad a reabastecer debe ser mayor a cero.")

        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE Insumo SET stock_actual = round(stock_actual + ?, 4) WHERE id_insumo = ?;",
                (cantidad, id_insumo),
            )
            if cursor.rowcount == 0:
                raise ValidacionError(f"No existe el insumo con id {id_insumo}.")
            return True

    def listar_insumos(self) -> List[Insumo]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo FROM Insumo ORDER BY nombre;",
            )
            return [self._fila_a_insumo(fila) for fila in cursor.fetchall()]

    def obtener_insumos_en_alerta(self) -> List[Insumo]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo FROM Insumo WHERE stock_actual <= stock_minimo ORDER BY stock_actual ASC;",
            )
            return [self._fila_a_insumo(fila) for fila in cursor.fetchall()]
