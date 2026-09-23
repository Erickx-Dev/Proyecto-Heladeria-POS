from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from database.connection import DEFAULT_DB_PATH, get_connection
from src.domain.audit import AuditoriaLog


class AuditRepository:
    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path = db_path if db_path is not None else DEFAULT_DB_PATH

    @property
    def db_path(self) -> Union[str, Path]:
        return self._db_path

    def insertar(self, log: AuditoriaLog) -> int:
        conn = get_connection(self._db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (log.id_usuario, log.accion, log.modulo, log.fecha_hora, log.detalles),
                )
                log.id_log = cursor.lastrowid
                return log.id_log
        finally:
            conn.close()

    def obtener_por_id(self, id_log: int) -> Optional[AuditoriaLog]:
        conn = get_connection(self._db_path)
        try:
            cursor = conn.execute(
                """
                SELECT id_log, id_usuario, accion, modulo, fecha_hora, detalles
                FROM AuditoriaLog
                WHERE id_log = ?
                """,
                (id_log,),
            )
            fila = cursor.fetchone()
            if fila is None:
                return None
            return AuditoriaLog(
                id_log=fila["id_log"],
                id_usuario=fila["id_usuario"],
                accion=fila["accion"],
                modulo=fila["modulo"],
                fecha_hora=fila["fecha_hora"],
                detalles=fila["detalles"],
            )
        finally:
            conn.close()

    def listar(
        self,
        limite: int = 100,
        modulo: Optional[str] = None,
        accion: Optional[str] = None,
        id_usuario: Optional[int] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> List[AuditoriaLog]:
        query = "SELECT id_log, id_usuario, accion, modulo, fecha_hora, detalles FROM AuditoriaLog"
        condiciones: List[str] = []
        params: List[Union[str, int]] = []

        if modulo is not None:
            condiciones.append("modulo = ?")
            params.append(modulo.strip())

        if accion is not None:
            condiciones.append("accion = ?")
            params.append(accion.strip())

        if id_usuario is not None:
            condiciones.append("id_usuario = ?")
            params.append(id_usuario)

        if fecha_inicio is not None:
            condiciones.append("fecha_hora >= ?")
            params.append(fecha_inicio.strip())

        if fecha_fin is not None:
            condiciones.append("fecha_hora <= ?")
            params.append(fecha_fin.strip())

        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)

        query += " ORDER BY fecha_hora DESC, id_log DESC LIMIT ?"
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

    def contar(
        self,
        modulo: Optional[str] = None,
        accion: Optional[str] = None,
        id_usuario: Optional[int] = None,
    ) -> int:
        query = "SELECT COUNT(*) FROM AuditoriaLog"
        condiciones: List[str] = []
        params: List[Union[str, int]] = []

        if modulo is not None:
            condiciones.append("modulo = ?")
            params.append(modulo.strip())

        if accion is not None:
            condiciones.append("accion = ?")
            params.append(accion.strip())

        if id_usuario is not None:
            condiciones.append("id_usuario = ?")
            params.append(id_usuario)

        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)

        conn = get_connection(self._db_path)
        try:
            cursor = conn.execute(query, tuple(params))
            resultado = cursor.fetchone()
            return int(resultado[0]) if resultado else 0
        finally:
            conn.close()
