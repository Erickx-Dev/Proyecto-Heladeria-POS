from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from database.connection import DEFAULT_DB_PATH, get_connection
from src.domain.audit import AuditoriaLog


class AuditService:
    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path = db_path if db_path is not None else DEFAULT_DB_PATH

    @property
    def db_path(self) -> Union[str, Path]:
        return self._db_path

    def registrar_evento(
        self,
        accion: str,
        modulo: str,
        id_usuario: Optional[int] = None,
        detalles: Optional[str] = None,
    ) -> AuditoriaLog:
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = AuditoriaLog(
            accion=accion,
            modulo=modulo,
            fecha_hora=fecha_hora,
            id_usuario=id_usuario,
            detalles=detalles,
        )
        conn = get_connection(self._db_path)
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) VALUES (?, ?, ?, ?, ?)",
                    (log.id_usuario, log.accion, log.modulo, log.fecha_hora, log.detalles),
                )
                log.id_log = cursor.lastrowid
            return log
        finally:
            conn.close()

    def obtener_logs(
        self,
        limite: int = 100,
        modulo: Optional[str] = None,
        id_usuario: Optional[int] = None,
    ) -> List[AuditoriaLog]:
        query = "SELECT id_log, id_usuario, accion, modulo, fecha_hora, detalles FROM AuditoriaLog"
        params: List[Union[str, int]] = []
        condiciones: List[str] = []

        if modulo is not None:
            condiciones.append("modulo = ?")
            params.append(modulo)
        if id_usuario is not None:
            condiciones.append("id_usuario = ?")
            params.append(id_usuario)

        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)

        query += " ORDER BY fecha_hora DESC LIMIT ?"
        params.append(limite)

        conn = get_connection(self._db_path)
        try:
            cursor = conn.execute(query, tuple(params))
            filas = cursor.fetchall()
            logs: List[AuditoriaLog] = []
            for fila in filas:
                logs.append(
                    AuditoriaLog(
                        id_log=fila["id_log"],
                        id_usuario=fila["id_usuario"],
                        accion=fila["accion"],
                        modulo=fila["modulo"],
                        fecha_hora=fila["fecha_hora"],
                        detalles=fila["detalles"],
                    )
                )
            return logs
        finally:
            conn.close()


AuditoriaService = AuditService
