from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from src.core.exceptions import (
    CredencialInvalidaError,
    ReglaNegocioError,
    RolInvalidoError,
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
)
from src.domain.user import Usuario
from src.repositories.user_repository import UserRepository
from src.services.audit_service import AuditService
from src.services.auth_service import AuthService


class UserService:
    def __init__(
        self,
        user_repository: Optional[UserRepository] = None,
        audit_service: Optional[AuditService] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._user_repo = user_repository or UserRepository(db_path=db_path)
        self._audit_service = audit_service or AuditService(db_path=db_path)

    @property
    def user_repository(self) -> UserRepository:
        return self._user_repo

    @property
    def audit_service(self) -> AuditService:
        return self._audit_service

    def crear_usuario(
        self,
        nombre: str,
        username: str,
        password: str,
        id_rol: int,
        estado: int = 1,
        id_operador: Optional[int] = None,
    ) -> Usuario:
        clean_nombre = nombre.strip()
        clean_username = username.strip()

        if not clean_nombre:
            raise CredencialInvalidaError("El nombre no puede estar vacío.")

        if len(clean_username) < 3:
            raise CredencialInvalidaError("El nombre de usuario debe tener al menos 3 caracteres.")

        if not password or len(password) < 4:
            raise CredencialInvalidaError("La contraseña debe tener al menos 4 caracteres.")

        if estado not in (0, 1):
            raise ReglaNegocioError("El estado debe ser 0 o 1.")

        rol = self._user_repo.obtener_rol_por_id(id_rol)
        if rol is None:
            raise RolInvalidoError(f"El rol con ID {id_rol} no es válido.")

        if self._user_repo.existe_username(clean_username):
            raise UsuarioDuplicadoError(f"El nombre de usuario '{clean_username}' ya se encuentra registrado.")

        password_hash = AuthService.hash_password(password)
        id_usuario = self._user_repo.insertar(
            nombre=clean_nombre,
            username=clean_username,
            password_hash=password_hash,
            id_rol=id_rol,
            estado=estado,
        )

        self._audit_service.registrar_evento(
            accion="USUARIO_CREADO",
            modulo="USUARIOS",
            id_usuario=id_operador,
            detalles=f"Creado usuario '{clean_username}' (ID: {id_usuario}) con rol {rol.nombre_rol}",
        )

        usuario = self._user_repo.obtener_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontradoError("Error al recuperar el usuario recién creado.")
        return usuario

    def modificar_password(
        self,
        id_usuario: int,
        password_nueva: str,
        id_operador: Optional[int] = None,
    ) -> bool:
        usuario = self._user_repo.obtener_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")

        if not password_nueva or len(password_nueva) < 4:
            raise CredencialInvalidaError("La nueva contraseña debe tener al menos 4 caracteres.")

        nuevo_hash = AuthService.hash_password(password_nueva)
        exito = self._user_repo.actualizar_password_hash(id_usuario, nuevo_hash)

        if exito:
            self._audit_service.registrar_evento(
                accion="PASSWORD_MODIFICADA",
                modulo="USUARIOS",
                id_usuario=id_operador,
                detalles=f"Contraseña actualizada para el usuario '{usuario.username}' (ID: {id_usuario})",
            )
        return exito

    def cambiar_estado(
        self,
        id_usuario: int,
        nuevo_estado: int,
        id_operador: Optional[int] = None,
    ) -> bool:
        if nuevo_estado not in (0, 1):
            raise ReglaNegocioError("El estado debe ser 0 (inactivo) o 1 (activo).")

        usuario = self._user_repo.obtener_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")

        exito = self._user_repo.actualizar_estado(id_usuario, nuevo_estado)
        if exito:
            accion = "USUARIO_ACTIVADO" if nuevo_estado == 1 else "USUARIO_DESACTIVADO"
            self._audit_service.registrar_evento(
                accion=accion,
                modulo="USUARIOS",
                id_usuario=id_operador,
                detalles=f"Estado del usuario '{usuario.username}' (ID: {id_usuario}) actualizado a {nuevo_estado}",
            )
        return exito

    def actualizar_datos(
        self,
        id_usuario: int,
        nombre: Optional[str] = None,
        username: Optional[str] = None,
        id_rol: Optional[int] = None,
        id_operador: Optional[int] = None,
    ) -> Usuario:
        usuario = self._user_repo.obtener_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontradoError(f"Usuario con ID {id_usuario} no encontrado.")

        nuevo_nombre = usuario.nombre
        if nombre is not None:
            clean_nombre = nombre.strip()
            if not clean_nombre:
                raise CredencialInvalidaError("El nombre no puede estar vacío.")
            nuevo_nombre = clean_nombre

        nuevo_username = usuario.username
        if username is not None:
            clean_username = username.strip()
            if len(clean_username) < 3:
                raise CredencialInvalidaError("El nombre de usuario debe tener al menos 3 caracteres.")
            if self._user_repo.existe_username(clean_username, excluir_id_usuario=id_usuario):
                raise UsuarioDuplicadoError(f"El nombre de usuario '{clean_username}' ya está en uso por otra cuenta.")
            nuevo_username = clean_username

        nuevo_id_rol = usuario.id_rol
        if id_rol is not None:
            rol = self._user_repo.obtener_rol_por_id(id_rol)
            if rol is None:
                raise RolInvalidoError(f"El rol con ID {id_rol} no es válido.")
            nuevo_id_rol = id_rol

        self._user_repo.actualizar_datos(id_usuario, nuevo_nombre, nuevo_username, nuevo_id_rol)

        self._audit_service.registrar_evento(
            accion="USUARIO_ACTUALIZADO",
            modulo="USUARIOS",
            id_usuario=id_operador,
            detalles=f"Datos modificados para el usuario '{nuevo_username}' (ID: {id_usuario})",
        )

        usuario_actualizado = self._user_repo.obtener_por_id(id_usuario)
        if usuario_actualizado is None:
            raise UsuarioNoEncontradoError("Error al recuperar el usuario actualizado.")
        return usuario_actualizado

    def obtener_usuario_por_id(self, id_usuario: int) -> Optional[Usuario]:
        return self._user_repo.obtener_por_id(id_usuario)

    def obtener_usuario_por_username(self, username: str) -> Optional[Usuario]:
        return self._user_repo.obtener_por_username(username)

    def listar_usuarios(self, solo_activos: bool = False) -> List[Usuario]:
        return self._user_repo.listar_todos(solo_activos=solo_activos)
