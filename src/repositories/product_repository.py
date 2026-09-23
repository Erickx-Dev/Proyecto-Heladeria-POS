from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.domain.product import Categoria, Producto


class ProductRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path = db_path

    def listar_categorias(self) -> List[Categoria]:
        sql = "SELECT id_categoria, nombre_categoria, descripcion FROM Categoria ORDER BY id_categoria ASC;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                Categoria(
                    id_categoria=fila["id_categoria"],
                    nombre_categoria=fila["nombre_categoria"],
                    descripcion=fila["descripcion"],
                )
                for fila in filas
            ]

    def obtener_categoria_por_id(self, id_categoria: int) -> Optional[Categoria]:
        sql = "SELECT id_categoria, nombre_categoria, descripcion FROM Categoria WHERE id_categoria = ?;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql, (id_categoria,))
            fila = cursor.fetchone()
            if fila is None:
                return None
            return Categoria(
                id_categoria=fila["id_categoria"],
                nombre_categoria=fila["nombre_categoria"],
                descripcion=fila["descripcion"],
            )

    def crear_categoria(self, categoria: Categoria) -> int:
        sql = "INSERT INTO Categoria (nombre_categoria, descripcion) VALUES (?, ?);"
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (categoria.nombre_categoria, categoria.descripcion))
            return cursor.lastrowid

    def listar_productos(self, solo_activos: bool = True) -> List[Producto]:
        if solo_activos:
            sql = "SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado FROM Producto WHERE estado = 1 ORDER BY nombre ASC;"
        else:
            sql = "SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado FROM Producto ORDER BY nombre ASC;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                Producto(
                    id_producto=fila["id_producto"],
                    codigo=fila["codigo"],
                    nombre=fila["nombre"],
                    precio_venta=float(fila["precio_venta"]),
                    id_categoria=fila["id_categoria"],
                    estado=fila["estado"],
                )
                for fila in filas
            ]

    def listar_productos_por_categoria(
        self, id_categoria: int, solo_activos: bool = True
    ) -> List[Producto]:
        if solo_activos:
            sql = "SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado FROM Producto WHERE id_categoria = ? AND estado = 1 ORDER BY nombre ASC;"
        else:
            sql = "SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado FROM Producto WHERE id_categoria = ? ORDER BY nombre ASC;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql, (id_categoria,))
            filas = cursor.fetchall()
            return [
                Producto(
                    id_producto=fila["id_producto"],
                    codigo=fila["codigo"],
                    nombre=fila["nombre"],
                    precio_venta=float(fila["precio_venta"]),
                    id_categoria=fila["id_categoria"],
                    estado=fila["estado"],
                )
                for fila in filas
            ]

    def obtener_producto_por_id(self, id_producto: int) -> Optional[Producto]:
        sql = "SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado FROM Producto WHERE id_producto = ?;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql, (id_producto,))
            fila = cursor.fetchone()
            if fila is None:
                return None
            return Producto(
                id_producto=fila["id_producto"],
                codigo=fila["codigo"],
                nombre=fila["nombre"],
                precio_venta=float(fila["precio_venta"]),
                id_categoria=fila["id_categoria"],
                estado=fila["estado"],
            )

    def obtener_producto_por_codigo(self, codigo: str) -> Optional[Producto]:
        sql = "SELECT id_producto, codigo, nombre, precio_venta, id_categoria, estado FROM Producto WHERE codigo = ?;"
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(sql, (codigo,))
            fila = cursor.fetchone()
            if fila is None:
                return None
            return Producto(
                id_producto=fila["id_producto"],
                codigo=fila["codigo"],
                nombre=fila["nombre"],
                precio_venta=float(fila["precio_venta"]),
                id_categoria=fila["id_categoria"],
                estado=fila["estado"],
            )

    def crear_producto(self, producto: Producto) -> int:
        sql = "INSERT INTO Producto (codigo, nombre, precio_venta, id_categoria, estado) VALUES (?, ?, ?, ?, ?);"
        with get_db_transaction(self._db_path) as conn:
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
            return cursor.lastrowid

    def actualizar_producto(self, producto: Producto) -> bool:
        sql = "UPDATE Producto SET codigo = ?, nombre = ?, precio_venta = ?, id_categoria = ?, estado = ? WHERE id_producto = ?;"
        with get_db_transaction(self._db_path) as conn:
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

    def cambiar_estado_producto(self, id_producto: int, nuevo_estado: int) -> bool:
        sql = "UPDATE Producto SET estado = ? WHERE id_producto = ?;"
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (nuevo_estado, id_producto))
            return cursor.rowcount > 0
