from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from database.connection import DEFAULT_DB_PATH, get_connection
from src.domain.user import Rol, Usuario


class UserRepository:
    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path = db_path if db_path is not None else DEFAULT_DB_PATH

    @property
    def db_path(self) -> Union[str, Path]:
        return self._db_path

    def obtener_por_id(self, id_usuario: int) -> Optional[Usuario]:
        conn = get_connection(self._db_path)
        try:
            cursor = conn.execute(
                """
                SELECT u.id_usuario, u.nombre, u.username, u.password_hash, u.id_rol, u.estado, r.nombre_rol
                FROM Usuario u
                INNER JOIN Rol r ON u.id_rol = r.id_rol
                WHERE u.id_usuario = ?
                """,
                (id_usuario,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            rol = Rol(nombre_rol=row["nombre_rol"], id_rol=row["id_rol"])
            return Usuario.crear(
                nombre=row["nombre"],
                username=row["username"],
                password_hash=row["password_hash"],
                id_rol=row["id_rol"],
                estado=row["estado"],
                id_usuario=row["id_usuario"],
                rol=rol,
            )
        finally:
            conn.close()

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        conn = get_connection(self._db_path)
        try:
            cursor = conn.execute(
                """
                SELECT u.id_usuario, u.nombre, u.username, u.password_hash, u.id_rol, u.estado, r.nombre_rol
                FROM Usuario u
                INNER JOIN Rol r ON u.id_rol = r.id_rol
                WHERE u.username = ?
                """,
                (username.strip(),),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            rol = Rol(nombre_rol=row["nombre_rol"], id_rol=row["id_rol"])
            return Usuario.crear(
                nombre=row["nombre"],
                username=row["username"],
                password_hash=row["password_hash"],
                id_rol=row["id_rol"],
                estado=row["estado"],
                id_usuario=row["id_usuario"],
                rol=rol,
            )
        finally:
            conn.close()

    def listar_todos(self, solo_activos: bool = False) -> List[Usuario]:
        query = """
            SELECT u.id_usuario, u.nombre, u.username, u.password_hash, u.id_rol, u.estado, r.nombre_rol
            FROM Usuario u
            INNER JOIN Rol r ON u.id_rol = r.id_rol
        """
        params: List[int] = []
        if solo_activos:
            query += " WHERE u.estado = ?"
            params.append(1)
        query += " ORDER BY u.id_usuario ASC"

        conn = get_connection(self._db_path)
        try:
            cursor = conn.execute(query, tuple(params))
            filas = cursor.fetchall()
            usuarios: List[Usuario] = []
            for row in filas:
                rol = Rol(nombre_rol=row["nombre_rol"], id_rol=row["id_rol"])
                usuario = Usuario.crear(
                    nombre=row["nombre"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    id_rol=row["id_rol"],
                    estado=row["estado"],
                    id_usuario=row["id_usuario"],
                    rol=rol,
                )
                usuarios.append(usuario)
            return usuarios
        finally:
            conn.close()

    def insertar(
        self,
        nombre: str,
        username: str,
        password_hash: str,
        id_rol: int,
        estado: int = 1,
    ) -> int:
        conn = get_connection(self._db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO Usuario (nombre, username, password_hash, id_rol, estado)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (nombre.strip(), username.strip(), password_hash, id_rol, estado),
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def actualizar_datos(
        self,
        id_usuario: int,
        nombre: str,
        username: str,
        id_rol: int,
    ) -> bool:
        conn = get_connection(self._db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE Usuario
                    SET nombre = ?, username = ?, id_rol = ?
                    WHERE id_usuario = ?
                    """,
                    (nombre.strip(), username.strip(), id_rol, id_usuario),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def actualizar_estado(self, id_usuario: int, estado: int) -> bool:
        conn = get_connection(self._db_path)
        try:
            with conn:
                cursor = conn.execute(
                    "UPDATE Usuario SET estado = ? WHERE id_usuario = ?",
                    (estado, id_usuario),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def actualizar_password_hash(self, id_usuario: int, password_hash: str) -> bool:
        conn = get_connection(self._db_path)
        try:
            with conn:
                cursor = conn.execute(
                    "UPDATE Usuario SET password_hash = ? WHERE id_usuario = ?",
                    (password_hash, id_usuario),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def existe_username(self, username: str, excluir_id_usuario: Optional[int] = None) -> bool:
        query = "SELECT 1 FROM Usuario WHERE username = ?"
        params: List[Union[str, int]] = [username.strip()]
        if excluir_id_usuario is not None:
            query += " AND id_usuario != ?"
            params.append(excluir_id_usuario)

        conn = get_connection(self._db_path)
        try:
            cursor = conn.execute(query, tuple(params))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def obtener_rol_por_id(self, id_rol: int) -> Optional[Rol]:
        conn = get_connection(self._db_path)
        try:
            cursor = conn.execute(
                "SELECT id_rol, nombre_rol FROM Rol WHERE id_rol = ?",
                (id_rol,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return Rol(nombre_rol=row["nombre_rol"], id_rol=row["id_rol"])
        finally:
            conn.close()
