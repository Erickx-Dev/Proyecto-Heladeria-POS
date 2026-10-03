from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from database.connection import get_db_transaction
from src.core.exceptions import AutenticacionError, ValidacionError
from src.core.security import verify_password
from src.domain.audit import AuditoriaLog
from src.domain.user import Usuario
from src.repositories.user_repository import UserRepository


class AuthService:

    def __init__(
        self,
        user_repository: Optional[UserRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path
        self._user_repository: UserRepository = user_repository or UserRepository(db_path=db_path)
        self._usuario_actual: Optional[Usuario] = None

    def _registrar_auditoria(
        self,
        accion: str,
        id_usuario: Optional[int],
        detalles: str,
    ) -> None:
        from datetime import datetime

        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_transaction(self._db_path) as conn:
            conn.execute(
                "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) "
                "VALUES (?, ?, ?, ?, ?);",
                (id_usuario, accion, "AUTH", fecha_hora, detalles),
            )

    def autenticar(self, username: str, password_plana: str) -> Usuario:
        if not username or not username.strip():
            raise ValidacionError("El nombre de usuario no puede estar vacío.")

        if not password_plana:
            raise ValidacionError("La contraseña no puede estar vacía.")

        usuario: Optional[Usuario] = self._user_repository.obtener_por_username(username.strip())

        if usuario is None:
            self._registrar_auditoria(
                "LOGIN_FALLIDO",
                None,
                f"Intento de acceso con username inexistente: {username}",
            )
            raise AutenticacionError("Credenciales inválidas.")

        if not usuario.es_activo():
            self._registrar_auditoria(
                "LOGIN_FALLIDO",
                usuario.id_usuario,
                f"Intento de acceso con usuario inactivo: {username}",
            )
            raise AutenticacionError("El usuario se encuentra inactivo.")

        if not verify_password(password_plana, usuario.password_hash):
            self._registrar_auditoria(
                "LOGIN_FALLIDO",
                usuario.id_usuario,
                f"Contraseña incorrecta para usuario: {username}",
            )
            raise AutenticacionError("Credenciales inválidas.")

        self._usuario_actual = usuario

        self._registrar_auditoria(
            "LOGIN_EXITOSO",
            usuario.id_usuario,
            f"Inicio de sesión exitoso: {username} (rol: {usuario.id_rol})",
        )

        return usuario

    def obtener_usuario_actual(self) -> Optional[Usuario]:
        return self._usuario_actual

    def cerrar_sesion(self) -> None:
        if self._usuario_actual is not None:
            self._registrar_auditoria(
                "LOGOUT",
                self._usuario_actual.id_usuario,
                f"Cierre de sesión: {self._usuario_actual.username}",
            )
        self._usuario_actual = None
