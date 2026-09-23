"""
Repositorio de Acceso a Datos: SupplyRepository.

Encapsula todas las sentencias SQL y operaciones de persistencia
relacionadas con los insumos y materias primas de bodega en SQLite3.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import DEFAULT_DB_PATH, get_db_cursor, get_db_transaction
from src.domain.supply import Insumo


class SupplyRepository:
    """
    Repositorio especializado para el inventario de materias primas y suministros de bodega.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH

    def crear(self, insumo: Insumo) -> Insumo:
        """
        Registra una nueva materia prima o insumo en el catálogo de bodega.

        Args:
            insumo: Entidad Insumo a persistir.

        Returns:
            Insumo: Instancia con su id_insumo asignado.
        """
        sql = """
            INSERT INTO Insumo (nombre, unidad_medida, stock_actual, stock_minimo)
            VALUES (?, ?, ?, ?);
        """
        with get_db_transaction(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                sql,
                (insumo.nombre, insumo.unidad_medida, insumo.stock_actual, insumo.stock_minimo),
            )
            insumo.id_insumo = cursor.lastrowid
            return insumo

    def obtener_por_id(self, id_insumo: int) -> Optional[Insumo]:
        """Recupera un insumo por su identificador primario."""
        sql = """
            SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo
            FROM Insumo
            WHERE id_insumo = ?;
        """
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql, (id_insumo,))
            row = cursor.fetchone()
            if not row:
                return None
            return Insumo(
                id_insumo=row["id_insumo"],
                nombre=row["nombre"],
                unidad_medida=row["unidad_medida"],
                stock_actual=row["stock_actual"],
                stock_minimo=row["stock_minimo"],
            )

    def obtener_por_nombre(self, nombre: str) -> Optional[Insumo]:
        """Recupera un insumo por coincidencia exacta de nombre."""
        sql = """
            SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo
            FROM Insumo
            WHERE lower(nombre) = lower(?);
        """
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql, (nombre.strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            return Insumo(
                id_insumo=row["id_insumo"],
                nombre=row["nombre"],
                unidad_medida=row["unidad_medida"],
                stock_actual=row["stock_actual"],
                stock_minimo=row["stock_minimo"],
            )

    def listar_todos(self) -> List[Insumo]:
        """Retorna todos los insumos ordenados alfabéticamente."""
        sql = """
            SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo
            FROM Insumo
            ORDER BY nombre ASC;
        """
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [
                Insumo(
                    id_insumo=r["id_insumo"],
                    nombre=r["nombre"],
                    unidad_medida=r["unidad_medida"],
                    stock_actual=r["stock_actual"],
                    stock_minimo=r["stock_minimo"],
                )
                for r in rows
            ]

    def listar_con_alerta_stock(self) -> List[Insumo]:
        """
        Retorna la lista de insumos cuyo stock_actual sea menor o igual a su stock_minimo.
        """
        sql = """
            SELECT id_insumo, nombre, unidad_medida, stock_actual, stock_minimo
            FROM Insumo
            WHERE stock_actual <= stock_minimo
            ORDER BY stock_actual ASC;
        """
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [
                Insumo(
                    id_insumo=r["id_insumo"],
                    nombre=r["nombre"],
                    unidad_medida=r["unidad_medida"],
                    stock_actual=r["stock_actual"],
                    stock_minimo=r["stock_minimo"],
                )
                for r in rows
            ]

    def actualizar(self, insumo: Insumo) -> bool:
        """
        Actualiza los datos descriptivos y umbrales de un insumo.
        """
        if not insumo.id_insumo:
            raise ValueError("No se puede actualizar un insumo sin id_insumo.")

        sql = """
            UPDATE Insumo
            SET nombre = ?, unidad_medida = ?, stock_actual = ?, stock_minimo = ?
            WHERE id_insumo = ?;
        """
        with get_db_transaction(self.db_path) as conn:
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

    def actualizar_stock(self, id_insumo: int, nuevo_stock: float) -> bool:
        """
        Actualiza directamente la cantidad disponible de un insumo.
        """
        if nuevo_stock < 0:
            raise ValueError("El nuevo stock no puede ser negativo.")

        sql = "UPDATE Insumo SET stock_actual = ? WHERE id_insumo = ?;"
        with get_db_transaction(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (nuevo_stock, id_insumo))
            return cursor.rowcount > 0

    def eliminar(self, id_insumo: int) -> bool:
        """
        Elimina un insumo del catálogo.
        """
        sql = "DELETE FROM Insumo WHERE id_insumo = ?;"
        with get_db_transaction(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_insumo,))
            return cursor.rowcount > 0
