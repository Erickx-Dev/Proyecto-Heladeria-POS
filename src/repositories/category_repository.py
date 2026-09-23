"""
Repositorio de Acceso a Datos: CategoriaRepository.

Encapsula todas las sentencias SQL y operaciones de persistencia
relacionadas con la entidad Categoria en SQLite3.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import DEFAULT_DB_PATH, get_db_cursor, get_db_transaction
from src.core.exceptions import EntidadDuplicadaError
from src.domain.category import Categoria


class CategoryRepository:
    """
    Repositorio especializado para la persistencia y consulta de categorías de productos.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH

    def crear(self, categoria: Categoria) -> Categoria:
        """
        Inserta una nueva categoría en la base de datos.

        Args:
            categoria: Entidad Categoria a persistir.

        Returns:
            Categoria: Instancia con su id_categoria asignado.

        Raises:
            EntidadDuplicadaError: Si el nombre_categoria ya existe.
        """
        sql = """
            INSERT INTO Categoria (nombre_categoria, descripcion)
            VALUES (?, ?);
        """
        try:
            with get_db_transaction(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (categoria.nombre_categoria, categoria.descripcion))
                categoria.id_categoria = cursor.lastrowid
                return categoria
        except sqlite3.IntegrityError as err:
            if "UNIQUE constraint failed" in str(err) or "nombre_categoria" in str(err):
                raise EntidadDuplicadaError(
                    f"Ya existe una categoría con el nombre '{categoria.nombre_categoria}'."
                ) from err
            raise

    def obtener_por_id(self, id_categoria: int) -> Optional[Categoria]:
        """Recupera una categoría por su identificador numérico."""
        sql = "SELECT id_categoria, nombre_categoria, descripcion FROM Categoria WHERE id_categoria = ?;"
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql, (id_categoria,))
            row = cursor.fetchone()
            if not row:
                return None
            return Categoria(
                id_categoria=row["id_categoria"],
                nombre_categoria=row["nombre_categoria"],
                descripcion=row["descripcion"],
            )

    def obtener_por_nombre(self, nombre_categoria: str) -> Optional[Categoria]:
        """Recupera una categoría por su nombre exacto."""
        sql = "SELECT id_categoria, nombre_categoria, descripcion FROM Categoria WHERE nombre_categoria = ?;"
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql, (nombre_categoria.strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            return Categoria(
                id_categoria=row["id_categoria"],
                nombre_categoria=row["nombre_categoria"],
                descripcion=row["descripcion"],
            )

    def listar_todas(self) -> List[Categoria]:
        """Retorna todas las categorías ordenadas alfabéticamente."""
        sql = "SELECT id_categoria, nombre_categoria, descripcion FROM Categoria ORDER BY nombre_categoria ASC;"
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [
                Categoria(
                    id_categoria=r["id_categoria"],
                    nombre_categoria=r["nombre_categoria"],
                    descripcion=r["descripcion"],
                )
                for r in rows
            ]

    def actualizar(self, categoria: Categoria) -> bool:
        """
        Actualiza el nombre y descripción de una categoría existente.

        Returns:
            bool: True si la fila fue actualizada, False si no existía.
        """
        if not categoria.id_categoria:
            raise ValueError("No se puede actualizar una categoría sin id_categoria asignado.")

        sql = """
            UPDATE Categoria
            SET nombre_categoria = ?, descripcion = ?
            WHERE id_categoria = ?;
        """
        try:
            with get_db_transaction(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (categoria.nombre_categoria, categoria.descripcion, categoria.id_categoria),
                )
                return cursor.rowcount > 0
        except sqlite3.IntegrityError as err:
            if "UNIQUE constraint failed" in str(err):
                raise EntidadDuplicadaError(
                    f"Ya existe otra categoría con el nombre '{categoria.nombre_categoria}'."
                ) from err
            raise

    def eliminar(self, id_categoria: int) -> bool:
        """
        Elimina una categoría si no tiene productos asociados (restringido por FK).

        Returns:
            bool: True si se eliminó, False si no existía.
        """
        sql = "DELETE FROM Categoria WHERE id_categoria = ?;"
        with get_db_transaction(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (id_categoria,))
            return cursor.rowcount > 0
