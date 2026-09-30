from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.core.exceptions import ValidacionError
from src.domain.user import Usuario


class UserRepository:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _fila_a_usuario(self, fila: sqlite3.Row) -> Usuario:
        return Usuario(
            id_usuario=fila["id_usuario"],
            nombre=fila["nombre"],
            username=fila["username"],
            password_hash=fila["password_hash"],
            id_rol=fila["id_rol"],
            estado=fila["estado"],
        )

    def obtener_por_id(self, id_usuario: int) -> Optional[Usuario]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_usuario, nombre, username, password_hash, id_rol, estado "
                "FROM Usuario WHERE id_usuario = ?;",
                (id_usuario,),
            )
            fila = cursor.fetchone()
            return self._fila_a_usuario(fila) if fila else None

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_usuario, nombre, username, password_hash, id_rol, estado "
                "FROM Usuario WHERE username = ?;",
                (username,),
            )
            fila = cursor.fetchone()
            return self._fila_a_usuario(fila) if fila else None

    def crear_usuario(self, usuario: Usuario) -> int:
        usuario.validar()
        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO Usuario (nombre, username, password_hash, id_rol, estado) "
                "VALUES (?, ?, ?, ?, ?);",
                (
                    usuario.nombre,
                    usuario.username,
                    usuario.password_hash,
                    usuario.id_rol,
                    usuario.estado,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def actualizar_usuario(self, usuario: Usuario) -> bool:
        if not usuario.id_usuario:
            raise ValidacionError("Se requiere id_usuario para actualizar.")

        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE Usuario SET nombre = ?, id_rol = ?, estado = ? "
                "WHERE id_usuario = ?;",
                (usuario.nombre, usuario.id_rol, usuario.estado, usuario.id_usuario),
            )
            return cursor.rowcount > 0

    def cambiar_password(self, id_usuario: int, nuevo_hash: str) -> bool:
        if len(nuevo_hash) != 60:
            raise ValidacionError("El nuevo hash debe tener exactamente 60 caracteres.")

        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE Usuario SET password_hash = ? WHERE id_usuario = ?;",
                (nuevo_hash, id_usuario),
            )
            return cursor.rowcount > 0

    def cambiar_estado(self, id_usuario: int, nuevo_estado: int) -> bool:
        if nuevo_estado not in (0, 1):
            raise ValidacionError("El estado debe ser 0 (Inactivo) o 1 (Activo).")

        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE Usuario SET estado = ? WHERE id_usuario = ?;",
                (nuevo_estado, id_usuario),
            )
            return cursor.rowcount > 0

    def listar_usuarios(self, solo_activos: bool = False) -> List[Usuario]:
        with get_db_cursor(self._db_path) as cursor:
            if solo_activos:
                cursor.execute(
                    "SELECT id_usuario, nombre, username, password_hash, id_rol, estado "
                    "FROM Usuario WHERE estado = 1 ORDER BY id_usuario;",
                )
            else:
                cursor.execute(
                    "SELECT id_usuario, nombre, username, password_hash, id_rol, estado "
                    "FROM Usuario ORDER BY id_usuario;",
                )
            return [self._fila_a_usuario(fila) for fila in cursor.fetchall()]
