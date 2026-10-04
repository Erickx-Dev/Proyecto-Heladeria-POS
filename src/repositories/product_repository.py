from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.core.exceptions import ValidacionError
from src.domain.product import Producto


class ProductRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _fila_a_producto(self, fila: sqlite3.Row) -> Producto:
        return Producto(
            id_producto=fila["id_producto"],
            codigo=fila["codigo"],
            nombre=fila["nombre"],
            precio_venta=fila["precio_venta"],
            id_categoria=fila["id_categoria"],
            estado=fila["estado"],
        )

    def crear_producto(self, producto: Producto) -> int:
        producto.validar()
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO Producto (codigo, nombre, precio_venta, id_categoria, estado) VALUES (?, ?, ?, ?, ?);",
                (producto.codigo.strip(), producto.nombre.strip(), producto.precio_venta, producto.id_categoria, producto.estado),
            )
            return cursor.lastrowid

    def obtener_por_id(self, id_producto: int) -> Optional[Producto]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado FROM Producto WHERE id_producto = ?;",
                (id_producto,),
            )
            fila = cursor.fetchone()
            return self._fila_a_producto(fila) if fila else None

    def obtener_por_codigo(self, codigo: str) -> Optional[Producto]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado FROM Producto WHERE UPPER(codigo) = UPPER(?);",
                (codigo.strip(),),
            )
            fila = cursor.fetchone()
            return self._fila_a_producto(fila) if fila else None

    def actualizar_producto(self, producto: Producto) -> bool:
        if not producto.id_producto:
            raise ValidacionError("Se requiere id_producto para actualizar.")
        producto.validar()
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE Producto SET codigo = ?, nombre = ?, precio_venta = ?, id_categoria = ?, estado = ? WHERE id_producto = ?;",
                (producto.codigo.strip(), producto.nombre.strip(), producto.precio_venta, producto.id_categoria, producto.estado, producto.id_producto),
            )
            return cursor.rowcount > 0

    def cambiar_estado(self, id_producto: int, nuevo_estado: int) -> bool:
        if nuevo_estado not in (0, 1):
            raise ValidacionError("El estado debe ser 1 (Activo) o 0 (Inactivo).")
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE Producto SET estado = ? WHERE id_producto = ?;",
                (nuevo_estado, id_producto),
            )
            return cursor.rowcount > 0

    def listar_productos(
        self,
        solo_activos: bool = False,
        id_categoria: Optional[int] = None,
    ) -> List[Producto]:
        query = "SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado FROM Producto WHERE 1=1"
        params: List[Union[int, str]] = []

        if solo_activos:
            query += " AND estado = 1"
        if id_categoria is not None:
            query += " AND id_categoria = ?"
            params.append(id_categoria)

        query += " ORDER BY nombre;"

        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(query, tuple(params))
            return [self._fila_a_producto(fila) for fila in cursor.fetchall()]
