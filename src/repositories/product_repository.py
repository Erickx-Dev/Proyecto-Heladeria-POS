"""
Repositorio de Acceso a Datos: ProductRepository.

Encapsula todas las sentencias SQL y operaciones de persistencia
relacionadas con los productos comerciales terminados en SQLite3.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import DEFAULT_DB_PATH, get_db_cursor, get_db_transaction
from src.core.exceptions import EntidadDuplicadaError
from src.domain.product import Producto, ProductoCompuesto, ProductoSimple


class ProductRepository:
    """
    Repositorio especializado para el catálogo de productos comerciales (POS).
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH

    def crear(self, producto: Producto) -> Producto:
        """
        Inserta un nuevo producto en la tabla Producto.

        Args:
            producto: Instancia de Producto, ProductoSimple o ProductoCompuesto.

        Returns:
            Producto: Instancia con su id_producto asignado.

        Raises:
            EntidadDuplicadaError: Si el código ya está en uso.
        """
        sql = """
            INSERT INTO Producto (codigo, nombre, precio_venta, id_categoria, estado)
            VALUES (?, ?, ?, ?, ?);
        """
        try:
            with get_db_transaction(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        producto.codigo,
                        producto.nombre,
                        producto.precio_venta,
                        producto.id_categoria,
                        producto.estado,
                    ),
                )
                producto.id_producto = cursor.lastrowid
                return producto
        except sqlite3.IntegrityError as err:
            if "UNIQUE constraint failed" in str(err) or "codigo" in str(err):
                raise EntidadDuplicadaError(
                    f"Ya existe un producto con el código '{producto.codigo}'."
                ) from err
            raise

    def _mapear_fila(self, row: sqlite3.Row) -> Producto:
        """Convierte una fila de base de datos a una instancia de Producto."""
        return Producto(
            id_producto=row["id_producto"],
            codigo=row["codigo"],
            nombre=row["nombre"],
            precio_venta=row["precio_venta"],
            id_categoria=row["id_categoria"],
            estado=row["estado"],
        )

    def obtener_por_id(self, id_producto: int) -> Optional[Producto]:
        """Recupera un producto por su id primario."""
        sql = """
            SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado
            FROM Producto
            WHERE id_producto = ?;
        """
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql, (id_producto,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._mapear_fila(row)

    def obtener_por_codigo(self, codigo: str) -> Optional[Producto]:
        """Recupera un producto por su código de venta único."""
        sql = """
            SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado
            FROM Producto
            WHERE upper(codigo) = upper(?);
        """
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql, (codigo.strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            return self._mapear_fila(row)

    def listar_todos(self, solo_activos: bool = False) -> List[Producto]:
        """
        Retorna la lista de todos los productos ordenados por categoría y nombre.

        Args:
            solo_activos: Si es True, filtra únicamente productos con estado = 1.
        """
        if solo_activos:
            sql = """
                SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado
                FROM Producto
                WHERE estado = 1
                ORDER BY id_categoria ASC, nombre ASC;
            """
        else:
            sql = """
                SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado
                FROM Producto
                ORDER BY id_categoria ASC, nombre ASC;
            """
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._mapear_fila(r) for r in rows]

    def listar_por_categoria(self, id_categoria: int, solo_activos: bool = False) -> List[Producto]:
        """
        Retorna los productos pertenecientes a una categoría específica.
        """
        if solo_activos:
            sql = """
                SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado
                FROM Producto
                WHERE id_categoria = ? AND estado = 1
                ORDER BY nombre ASC;
            """
        else:
            sql = """
                SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado
                FROM Producto
                WHERE id_categoria = ?
                ORDER BY nombre ASC;
            """
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql, (id_categoria,))
            rows = cursor.fetchall()
            return [self._mapear_fila(r) for r in rows]

    def actualizar(self, producto: Producto) -> bool:
        """
        Actualiza los datos comerciales de un producto.
        """
        if not producto.id_producto:
            raise ValueError("No se puede actualizar un producto sin id_producto.")

        sql = """
            UPDATE Producto
            SET codigo = ?, nombre = ?, precio_venta = ?, id_categoria = ?, estado = ?
            WHERE id_producto = ?;
        """
        try:
            with get_db_transaction(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        producto.codigo,
                        producto.nombre,
                        producto.precio_venta,
                        producto.id_categoria,
                        producto.estado,
                        producto.id_producto,
                    ),
                )
                return cursor.rowcount > 0
        except sqlite3.IntegrityError as err:
            if "UNIQUE constraint failed" in str(err) or "codigo" in str(err):
                raise EntidadDuplicadaError(
                    f"Ya existe otro producto con el código '{producto.codigo}'."
                ) from err
            raise

    def actualizar_precio(self, id_producto: int, nuevo_precio: float) -> bool:
        """
        Actualiza el precio de venta de un producto.
        """
        if nuevo_precio < 0.0:
            raise ValueError("El nuevo precio no puede ser negativo.")

        sql = "UPDATE Producto SET precio_venta = ? WHERE id_producto = ?;"
        with get_db_transaction(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (round(float(nuevo_precio), 2), id_producto))
            return cursor.rowcount > 0

    def cambiar_estado(self, id_producto: int, nuevo_estado: int) -> bool:
        """
        Cambia el estado de activación/suspensión de un producto.
        """
        if nuevo_estado not in (0, 1):
            raise ValueError("El nuevo estado debe ser 0 o 1.")

        sql = "UPDATE Producto SET estado = ? WHERE id_producto = ?;"
        with get_db_transaction(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (nuevo_estado, id_producto))
            return cursor.rowcount > 0

    def eliminar(self, id_producto: int) -> bool:
        """
        Elimina un producto del catálogo (si no tiene ventas asociadas por FK).
        """
        sql = "DELETE FROM Producto WHERE id_producto = ?;"
        with get_db_transaction(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_producto,))
            return cursor.rowcount > 0
