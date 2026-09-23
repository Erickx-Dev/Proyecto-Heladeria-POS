from __future__ import annotations

from typing import Optional


class Rol:
    def __init__(self, nombre_rol: str = "", id_rol: Optional[int] = None) -> None:
        self._id_rol = id_rol
        self._nombre_rol = nombre_rol

    @property
    def id_rol(self) -> Optional[int]:
        return self._id_rol

    @id_rol.setter
    def id_rol(self, valor: Optional[int]) -> None:
        self._id_rol = valor

    @property
    def nombre_rol(self) -> str:
        return self._nombre_rol

    @nombre_rol.setter
    def nombre_rol(self, valor: str) -> None:
        self._nombre_rol = valor


class Usuario:
    def __init__(
        self,
        nombre: str = "",
        username: str = "",
        password_hash: str = "",
        id_rol: int = 0,
        estado: int = 1,
        id_usuario: Optional[int] = None,
        rol: Optional[Rol] = None,
    ) -> None:
        self._id_usuario = id_usuario
        self._nombre = nombre
        self._username = username
        self._password_hash = password_hash
        self._id_rol = id_rol
        self._estado = estado
        self._rol = rol

    @property
    def id_usuario(self) -> Optional[int]:
        return self._id_usuario

    @id_usuario.setter
    def id_usuario(self, valor: Optional[int]) -> None:
        self._id_usuario = valor

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = valor

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, valor: str) -> None:
        self._username = valor

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @password_hash.setter
    def password_hash(self, valor: str) -> None:
        self._password_hash = valor

    @property
    def id_rol(self) -> int:
        return self._id_rol

    @id_rol.setter
    def id_rol(self, valor: int) -> None:
        self._id_rol = valor

    @property
    def estado(self) -> int:
        return self._estado

    @estado.setter
    def estado(self, valor: int) -> None:
        self._estado = valor

    @property
    def rol(self) -> Optional[Rol]:
        return self._rol

    @rol.setter
    def rol(self, valor: Optional[Rol]) -> None:
        self._rol = valor

    def esta_activo(self) -> bool:
        return self._estado == 1

    def es_administrador(self) -> bool:
        return False

    @classmethod
    def crear(
        cls,
        nombre: str = "",
        username: str = "",
        password_hash: str = "",
        id_rol: int = 0,
        estado: int = 1,
        id_usuario: Optional[int] = None,
        rol: Optional[Rol] = None,
    ) -> Usuario:
        if id_rol == 1:
            return Administrador(
                nombre=nombre,
                username=username,
                password_hash=password_hash,
                estado=estado,
                id_usuario=id_usuario,
                rol=rol,
            )
        elif id_rol == 2:
            return Empleado(
                nombre=nombre,
                username=username,
                password_hash=password_hash,
                estado=estado,
                id_usuario=id_usuario,
                rol=rol,
            )
        return cls(
            nombre=nombre,
            username=username,
            password_hash=password_hash,
            id_rol=id_rol,
            estado=estado,
            id_usuario=id_usuario,
            rol=rol,
        )


class Administrador(Usuario):
    def __init__(
        self,
        nombre: str = "",
        username: str = "",
        password_hash: str = "",
        estado: int = 1,
        id_usuario: Optional[int] = None,
        rol: Optional[Rol] = None,
    ) -> None:
        super().__init__(
            nombre=nombre,
            username=username,
            password_hash=password_hash,
            id_rol=1,
            estado=estado,
            id_usuario=id_usuario,
            rol=rol,
        )

    def es_administrador(self) -> bool:
        return True


class Empleado(Usuario):
    def __init__(
        self,
        nombre: str = "",
        username: str = "",
        password_hash: str = "",
        estado: int = 1,
        id_usuario: Optional[int] = None,
        rol: Optional[Rol] = None,
    ) -> None:
        super().__init__(
            nombre=nombre,
            username=username,
            password_hash=password_hash,
            id_rol=2,
            estado=estado,
            id_usuario=id_usuario,
            rol=rol,
        )

    def es_administrador(self) -> bool:
        return False
