from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, Optional

from src.core.exceptions import ValidacionError


class Permiso(str, Enum):
    VENTAS = "VENTAS"
    CAJA = "CAJA"
    GASTOS = "GASTOS"
    MERMAS = "MERMAS"
    CATALOGO = "CATALOGO"
    INVENTARIO = "INVENTARIO"
    GESTIONAR_USUARIOS = "GESTIONAR_USUARIOS"
    REPORTES = "REPORTES"
    AUDITORIA = "AUDITORIA"
    BACKUP = "BACKUP"


PERMISOS_POR_ROL: Dict[int, FrozenSet[Permiso]] = {
    1: frozenset(Permiso),
    2: frozenset({
        Permiso.VENTAS,
        Permiso.CAJA,
        Permiso.GASTOS,
        Permiso.MERMAS,
    }),
}


@dataclass
class Rol:

    id_rol: Optional[int] = None
    nombre_rol: str = ""

    def validar(self) -> None:
        if not self.nombre_rol or not self.nombre_rol.strip():
            raise ValidacionError("El nombre del rol no puede estar vacío.")


@dataclass
class Usuario:

    id_usuario: Optional[int] = None
    nombre: str = ""
    username: str = ""
    password_hash: str = ""
    id_rol: int = 2
    estado: int = 1

    def es_activo(self) -> bool:
        return self.estado == 1

    def es_administrador(self) -> bool:
        return self.id_rol == 1

    def tiene_permiso(self, permiso: Permiso) -> bool:
        if not self.es_activo():
            return False
        permisos_rol: FrozenSet[Permiso] = PERMISOS_POR_ROL.get(self.id_rol, frozenset())
        return permiso in permisos_rol

    def has_permission(self, permiso: Permiso) -> bool:
        return self.tiene_permiso(permiso)

    def validar(self) -> None:
        if not self.nombre or not self.nombre.strip():
            raise ValidacionError("El nombre del usuario no puede estar vacío.")

        if not self.username or len(self.username.strip()) < 3:
            raise ValidacionError("El username debe tener al menos 3 caracteres.")

        if not self.password_hash or len(self.password_hash) != 60:
            raise ValidacionError("El password_hash debe tener exactamente 60 caracteres (formato bcrypt).")

        if self.id_rol not in (1, 2):
            raise ValidacionError("El id_rol debe ser 1 (Administrador) o 2 (Empleado).")

        if self.estado not in (0, 1):
            raise ValidacionError("El estado debe ser 1 (Activo) o 0 (Inactivo).")
