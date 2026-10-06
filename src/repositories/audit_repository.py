from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_cursor, get_db_transaction
from src.domain.audit import AuditoriaLog


class AuditRepository:
    """Repositorio de solo inserción y consulta sobre AuditoriaLog (inalterable)."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    @staticmethod
    def _fila_a_log(fila: sqlite3.Row) -> AuditoriaLog:
        return AuditoriaLog(
            id_log=fila["id_log"],
            id_usuario=fila["id_usuario"],
            accion=fila["accion"],
            modulo=fila["modulo"],
            fecha_hora=fila["fecha_hora"],
            detalles=fila["detalles"],
        )

    @staticmethod
    def insertar_en_conexion(conn: sqlite3.Connection, log: AuditoriaLog) -> int:
        """Inserta un log dentro de una transacción ya abierta (para operaciones atómicas)."""
        log.validar()
        cursor = conn.execute(
            "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) "
            "VALUES (?, ?, ?, ?, ?);",
            (log.id_usuario, log.accion.strip(), log.modulo.strip(), log.fecha_hora, log.detalles),
        )
        return cursor.lastrowid

    def registrar_log(self, log: AuditoriaLog) -> int:
        with get_db_transaction(self._db_path) as conn:
            return self.insertar_en_conexion(conn, log)

    def obtener_por_id(self, id_log: int) -> Optional[AuditoriaLog]:
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_log, id_usuario, accion, modulo, fecha_hora, detalles "
                "FROM AuditoriaLog WHERE id_log = ?;",
                (id_log,),
            )
            fila = cursor.fetchone()
            return self._fila_a_log(fila) if fila else None

    def listar_logs(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        id_usuario: Optional[int] = None,
        modulo: Optional[str] = None,
    ) -> List[AuditoriaLog]:
        condiciones: List[str] = []
        parametros: List[object] = []

        if fecha_desde:
            condiciones.append("fecha_hora >= ?")
            parametros.append(fecha_desde)
        if fecha_hasta:
            if len(fecha_hasta) == 10:
                fecha_hasta = f"{fecha_hasta} 23:59:59"
            condiciones.append("fecha_hora <= ?")
            parametros.append(fecha_hasta)
        if id_usuario is not None:
            condiciones.append("id_usuario = ?")
            parametros.append(id_usuario)
        if modulo:
            condiciones.append("modulo = ?")
            parametros.append(modulo)

        where: str = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT id_log, id_usuario, accion, modulo, fecha_hora, detalles "
                f"FROM AuditoriaLog{where} ORDER BY fecha_hora DESC, id_log DESC;",
                tuple(parametros),
            )
            return [self._fila_a_log(fila) for fila in cursor.fetchall()]
