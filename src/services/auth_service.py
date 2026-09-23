from __future__ import annotations

from pathlib import Path
from typing import Optional, Union
import bcrypt

from database.connection import DEFAULT_DB_PATH, get_connection
from src.domain.user import Administrador, Empleado, Rol, Usuario
from src.services.audit_service import AuditService


class AuthService:
    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        self._db_path = db_path if db_path is not None else DEFAULT_DB_PATH
        self._audit_service = audit_service or AuditService(db_path=self._db_path)

    @property
    def db_path(self) -> Union[str, Path]:
        return self._db_path

    @property
    def audit_service(self) -> AuditService:
        return self._audit_service

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False

    def autenticar(self, username: str, password: str) -> Optional[Usuario]:
        clean_username = username.strip()
        if not clean_username or not password:
            return None

        conn = get_connection(self._db_path)
        try:
            cursor = conn.execute(
                """
                SELECT u.id_usuario, u.nombre, u.username, u.password_hash, u.id_rol, u.estado, r.nombre_rol
                FROM Usuario u
                INNER JOIN Rol r ON u.id_rol = r.id_rol
                WHERE u.username = ?
                """,
                (clean_username,),
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        if row is None:
            self._audit_service.registrar_evento(
                accion="LOGIN_FALLIDO",
                modulo="AUTH",
                id_usuario=None,
                detalles=f"Usuario inexistente: {clean_username}",
            )
            return None

        if row["estado"] != 1:
            self._audit_service.registrar_evento(
                accion="LOGIN_BLOQUEADO",
                modulo="AUTH",
                id_usuario=row["id_usuario"],
                detalles=f"Usuario inactivo: {clean_username}",
            )
            return None

        if not self.verify_password(password, row["password_hash"]):
            self._audit_service.registrar_evento(
                accion="LOGIN_FALLIDO",
                modulo="AUTH",
                id_usuario=row["id_usuario"],
                detalles=f"Contraseña incorrecta para usuario: {clean_username}",
            )
            return None

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

        self._audit_service.registrar_evento(
            accion="LOGIN_EXITOSO",
            modulo="AUTH",
            id_usuario=usuario.id_usuario,
            detalles=f"Inicio de sesión exitoso como {rol.nombre_rol}",
        )

        return usuario

    def registrar_usuario(
        self,
        nombre: str,
        username: str,
        password: str,
        id_rol: int,
        estado: int = 1,
    ) -> Usuario:
        clean_nombre = nombre.strip()
        clean_username = username.strip()
        password_cifrada = self.hash_password(password)

        conn = get_connection(self._db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO Usuario (nombre, username, password_hash, id_rol, estado)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (clean_nombre, clean_username, password_cifrada, id_rol, estado),
                )
                id_usuario = cursor.lastrowid

                cursor_rol = conn.execute(
                    "SELECT nombre_rol FROM Rol WHERE id_rol = ?",
                    (id_rol,),
                )
                rol_row = cursor_rol.fetchone()
                nombre_rol = rol_row["nombre_rol"] if rol_row else ""

            rol = Rol(nombre_rol=nombre_rol, id_rol=id_rol)
            usuario = Usuario.crear(
                nombre=clean_nombre,
                username=clean_username,
                password_hash=password_cifrada,
                id_rol=id_rol,
                estado=estado,
                id_usuario=id_usuario,
                rol=rol,
            )

            self._audit_service.registrar_evento(
                accion="USUARIO_CREADO",
                modulo="AUTH",
                id_usuario=id_usuario,
                detalles=f"Registro de nuevo usuario: {clean_username} ({nombre_rol})",
            )
            return usuario
        finally:
            conn.close()

    def obtener_usuario_por_id(self, id_usuario: int) -> Optional[Usuario]:
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
