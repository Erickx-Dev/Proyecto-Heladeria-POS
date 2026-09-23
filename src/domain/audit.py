from __future__ import annotations

import json
from typing import Any, Dict, Optional

MODULO_VENTAS: str = "VENTAS"
MODULO_CAJA: str = "CAJA"
MODULO_GASTOS: str = "GASTOS"
MODULO_INVENTARIO: str = "INVENTARIO"
MODULO_CATALOGO: str = "CATALOGO"
MODULO_USUARIOS: str = "USUARIOS"
MODULO_AUTH: str = "AUTH"

ACCION_VENTA_ANULADA: str = "VENTA_ANULADA"
ACCION_CAJA_APERTURA: str = "CAJA_APERTURA"
ACCION_CAJA_CIERRE: str = "CAJA_CIERRE"
ACCION_GASTO_REGISTRADO: str = "GASTO_REGISTRADO"
ACCION_MERMA_REGISTRADA: str = "MERMA_REGISTRADA"
ACCION_PRECIO_MODIFICADO: str = "PRECIO_MODIFICADO"
ACCION_LOGIN_EXITOSO: str = "LOGIN_EXITOSO"
ACCION_LOGIN_FALLIDO: str = "LOGIN_FALLIDO"
ACCION_LOGIN_BLOQUEADO: str = "LOGIN_BLOQUEADO"
ACCION_USUARIO_CREADO: str = "USUARIO_CREADO"
ACCION_USUARIO_ACTUALIZADO: str = "USUARIO_ACTUALIZADO"
ACCION_USUARIO_ACTIVADO: str = "USUARIO_ACTIVADO"
ACCION_USUARIO_DESACTIVADO: str = "USUARIO_DESACTIVADO"
ACCION_PASSWORD_MODIFICADA: str = "PASSWORD_MODIFICADA"


class AuditoriaLog:
    def __init__(
        self,
        accion: str = "",
        modulo: str = "",
        fecha_hora: str = "",
        id_usuario: Optional[int] = None,
        detalles: Optional[str] = None,
        id_log: Optional[int] = None,
    ) -> None:
        self._id_log = id_log
        self._id_usuario = id_usuario
        self._accion = accion
        self._modulo = modulo
        self._fecha_hora = fecha_hora
        self._detalles = detalles

    @property
    def id_log(self) -> Optional[int]:
        return self._id_log

    @id_log.setter
    def id_log(self, valor: Optional[int]) -> None:
        self._id_log = valor

    @property
    def id_usuario(self) -> Optional[int]:
        return self._id_usuario

    @id_usuario.setter
    def id_usuario(self, valor: Optional[int]) -> None:
        self._id_usuario = valor

    @property
    def accion(self) -> str:
        return self._accion

    @accion.setter
    def accion(self, valor: str) -> None:
        self._accion = valor

    @property
    def modulo(self) -> str:
        return self._modulo

    @modulo.setter
    def modulo(self, valor: str) -> None:
        self._modulo = valor

    @property
    def fecha_hora(self) -> str:
        return self._fecha_hora

    @fecha_hora.setter
    def fecha_hora(self, valor: str) -> None:
        self._fecha_hora = valor

    @property
    def detalles(self) -> Optional[str]:
        return self._detalles

    @detalles.setter
    def detalles(self, valor: Optional[str]) -> None:
        self._detalles = valor

    def obtener_detalles_dict(self) -> Optional[Dict[str, Any]]:
        if not self._detalles:
            return None
        try:
            parsed = json.loads(self._detalles)
            if isinstance(parsed, dict):
                return parsed
            return {"valor": parsed}
        except (ValueError, TypeError):
            return {"texto": self._detalles}
