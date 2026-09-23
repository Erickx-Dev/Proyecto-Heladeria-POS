from __future__ import annotations

from typing import Optional


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
