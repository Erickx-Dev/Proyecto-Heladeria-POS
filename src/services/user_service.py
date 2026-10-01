from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_transaction
from src.core.exceptions import AutorizacionError, ValidacionError
from src.core.security import hash_password
from src.domain.user import Permiso, Usuario
from src.repositories.user_repository import UserRepository


LONGITUD_MINIMA_PASSWORD: int = 6


class UserService:

    def __init__(
        self,
        user_repository: Optional[UserRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path
        self._user_repository: UserRepository = user_repository or UserRepository(db_path=db_path)

    def _registrar_auditoria(
        self,
        accion: str,
        id_usuario: Optional[int],
        detalles: str,
    ) -> None:
        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_transaction(self._db_path) as conn:
            conn.execute(
                "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) "
                "VALUES (?, ?, ?, ?, ?);",
                (id_usuario, accion, "USUARIOS", fecha_hora, detalles),
            )

    def _verificar_permiso(self, autor: Usuario, permiso: Permiso) -> None:
        if not autor.has_permission(permiso):
            raise AutorizacionError(
                f"El usuario '{autor.username}' no tiene el permiso '{permiso.value}'."
            )

    def _contar_administradores_activos(self) -> int:
        usuarios: List[Usuario] = self._user_repository.listar_usuarios(solo_activos=True)
        return sum(1 for u in usuarios if u.es_administrador())

    def _validar_proteccion_ultimo_admin(self, id_usuario: int) -> None:
        usuario_objetivo: Optional[Usuario] = self._user_repository.obtener_por_id(id_usuario)
        if usuario_objetivo is None:
            raise ValidacionError("El usuario especificado no existe.")
        if usuario_objetivo.es_administrador() and usuario_objetivo.es_activo():
            if self._contar_administradores_activos() <= 1:
                raise ValidacionError(
                    "No se puede modificar al único administrador activo del sistema."
                )

    def crear_usuario(
        self,
        autor: Usuario,
        nombre: str,
        username: str,
        password_plana: str,
        id_rol: int,
    ) -> Usuario:
        self._verificar_permiso(autor, Permiso.GESTIONAR_USUARIOS)

        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del usuario no puede estar vacío.")

        if not username or len(username.strip()) < 3:
            raise ValidacionError("El username debe tener al menos 3 caracteres.")

        if not password_plana or len(password_plana) < LONGITUD_MINIMA_PASSWORD:
            raise ValidacionError(
                f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres."
            )

        if id_rol not in (1, 2):
            raise ValidacionError("El id_rol debe ser 1 (Administrador) o 2 (Empleado).")

        existente: Optional[Usuario] = self._user_repository.obtener_por_username(username.strip())
        if existente is not None:
            raise ValidacionError(f"El username '{username}' ya está en uso.")

        password_hash: str = hash_password(password_plana)

        nuevo_usuario: Usuario = Usuario(
            nombre=nombre.strip(),
            username=username.strip(),
            password_hash=password_hash,
            id_rol=id_rol,
            estado=1,
        )

        id_creado: int = self._user_repository.crear_usuario(nuevo_usuario)
        nuevo_usuario.id_usuario = id_creado

        self._registrar_auditoria(
            "USUARIO_CREADO",
            autor.id_usuario,
            f"Usuario '{username}' creado con rol {id_rol} por '{autor.username}'.",
        )

        return nuevo_usuario

    def actualizar_usuario(
        self,
        autor: Usuario,
        id_usuario: int,
        nombre: str,
        id_rol: int,
        estado: int,
    ) -> Usuario:
        self._verificar_permiso(autor, Permiso.GESTIONAR_USUARIOS)

        usuario_actual: Optional[Usuario] = self._user_repository.obtener_por_id(id_usuario)
        if usuario_actual is None:
            raise ValidacionError("El usuario especificado no existe.")

        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del usuario no puede estar vacío.")

        if id_rol not in (1, 2):
            raise ValidacionError("El id_rol debe ser 1 (Administrador) o 2 (Empleado).")

        if estado not in (0, 1):
            raise ValidacionError("El estado debe ser 1 (Activo) o 0 (Inactivo).")

        cambio_de_rol: bool = usuario_actual.id_rol != id_rol
        desactivacion: bool = usuario_actual.estado == 1 and estado == 0

        if usuario_actual.es_administrador() and usuario_actual.es_activo():
            if cambio_de_rol or desactivacion:
                self._validar_proteccion_ultimo_admin(id_usuario)

        usuario_actualizado: Usuario = Usuario(
            id_usuario=id_usuario,
            nombre=nombre.strip(),
            username=usuario_actual.username,
            password_hash=usuario_actual.password_hash,
            id_rol=id_rol,
            estado=estado,
        )

        self._user_repository.actualizar_usuario(usuario_actualizado)

        self._registrar_auditoria(
            "USUARIO_ACTUALIZADO",
            autor.id_usuario,
            f"Usuario id={id_usuario} actualizado por '{autor.username}'. "
            f"Nombre='{nombre}', Rol={id_rol}, Estado={estado}.",
        )

        return usuario_actualizado

    def cambiar_password(
        self,
        autor: Usuario,
        id_usuario: int,
        nueva_password_plana: str,
    ) -> bool:
        es_propio: bool = autor.id_usuario == id_usuario

        if not es_propio:
            self._verificar_permiso(autor, Permiso.GESTIONAR_USUARIOS)

        usuario_objetivo: Optional[Usuario] = self._user_repository.obtener_por_id(id_usuario)
        if usuario_objetivo is None:
            raise ValidacionError("El usuario especificado no existe.")

        if not nueva_password_plana or len(nueva_password_plana) < LONGITUD_MINIMA_PASSWORD:
            raise ValidacionError(
                f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres."
            )

        nuevo_hash: str = hash_password(nueva_password_plana)
        resultado: bool = self._user_repository.cambiar_password(id_usuario, nuevo_hash)

        self._registrar_auditoria(
            "PASSWORD_CAMBIADA",
            autor.id_usuario,
            f"Contraseña del usuario id={id_usuario} cambiada por '{autor.username}'.",
        )

        return resultado

    def cambiar_estado(
        self,
        autor: Usuario,
        id_usuario: int,
        nuevo_estado: int,
    ) -> bool:
        self._verificar_permiso(autor, Permiso.GESTIONAR_USUARIOS)

        if nuevo_estado not in (0, 1):
            raise ValidacionError("El estado debe ser 1 (Activo) o 0 (Inactivo).")

        usuario_objetivo: Optional[Usuario] = self._user_repository.obtener_por_id(id_usuario)
        if usuario_objetivo is None:
            raise ValidacionError("El usuario especificado no existe.")

        if usuario_objetivo.es_administrador() and usuario_objetivo.es_activo() and nuevo_estado == 0:
            self._validar_proteccion_ultimo_admin(id_usuario)

        resultado: bool = self._user_repository.cambiar_estado(id_usuario, nuevo_estado)

        self._registrar_auditoria(
            "ESTADO_CAMBIADO",
            autor.id_usuario,
            f"Estado del usuario id={id_usuario} cambiado a {nuevo_estado} por '{autor.username}'.",
        )

        return resultado

    def obtener_por_id(self, id_usuario: int) -> Optional[Usuario]:
        return self._user_repository.obtener_por_id(id_usuario)

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        return self._user_repository.obtener_por_username(username)

    def listar_usuarios(self, solo_activos: bool = False) -> List[Usuario]:
        return self._user_repository.listar_usuarios(solo_activos=solo_activos)
