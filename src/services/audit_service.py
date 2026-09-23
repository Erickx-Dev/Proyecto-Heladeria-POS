from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union

from database.connection import DEFAULT_DB_PATH
from src.domain.audit import (
    ACCION_CAJA_APERTURA,
    ACCION_CAJA_CIERRE,
    ACCION_GASTO_REGISTRADO,
    ACCION_MERMA_REGISTRADA,
    ACCION_PRECIO_MODIFICADO,
    ACCION_VENTA_ANULADA,
    MODULO_CAJA,
    MODULO_CATALOGO,
    MODULO_GASTOS,
    MODULO_INVENTARIO,
    MODULO_VENTAS,
    AuditoriaLog,
)
from src.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(
        self,
        audit_repository: Optional[Union[AuditRepository, str, Path]] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        if isinstance(audit_repository, (str, Path)):
            self._db_path = audit_repository
            self._repo = AuditRepository(db_path=self._db_path)
        elif audit_repository is not None:
            self._repo = audit_repository
            self._db_path = db_path if db_path is not None else self._repo.db_path
        else:
            self._db_path = db_path if db_path is not None else DEFAULT_DB_PATH
            self._repo = AuditRepository(db_path=self._db_path)

    @property
    def repository(self) -> AuditRepository:
        return self._repo

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
            accion=accion.strip(),
            modulo=modulo.strip(),
            fecha_hora=fecha_hora,
            id_usuario=id_usuario,
            detalles=detalles,
        )
        self._repo.insertar(log)
        return log

    def registrar_cambio_estado(
        self,
        accion: str,
        modulo: str,
        id_usuario: Optional[int],
        estado_anterior: Any,
        estado_nuevo: Any,
        motivo: Optional[str] = None,
    ) -> AuditoriaLog:
        payload = {
            "previo": estado_anterior,
            "posterior": estado_nuevo,
            "motivo": motivo,
        }
        detalles_json = json.dumps(payload, ensure_ascii=False)
        return self.registrar_evento(
            accion=accion,
            modulo=modulo,
            id_usuario=id_usuario,
            detalles=detalles_json,
        )

    def registrar_anulacion_venta(
        self,
        id_venta: int,
        total: float,
        motivo: str,
        id_usuario: Optional[int] = None,
    ) -> AuditoriaLog:
        estado_anterior = {"id_venta": id_venta, "total": total, "estado": "COMPLETADA"}
        estado_nuevo = {"id_venta": id_venta, "total": total, "estado": "ANULADA"}
        return self.registrar_cambio_estado(
            accion=ACCION_VENTA_ANULADA,
            modulo=MODULO_VENTAS,
            id_usuario=id_usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            motivo=motivo,
        )

    def registrar_apertura_caja(
        self,
        id_caja: int,
        monto_inicial: float,
        id_usuario: Optional[int] = None,
    ) -> AuditoriaLog:
        estado_anterior = {"id_caja": id_caja, "estado": "SIN_APERTURAR"}
        estado_nuevo = {"id_caja": id_caja, "monto_inicial": monto_inicial, "estado": "ABIERTA"}
        return self.registrar_cambio_estado(
            accion=ACCION_CAJA_APERTURA,
            modulo=MODULO_CAJA,
            id_usuario=id_usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            motivo="Apertura formal de turno de caja",
        )

    def registrar_cierre_caja(
        self,
        id_caja: int,
        monto_esperado: float,
        monto_real: float,
        diferencia: float,
        id_usuario: Optional[int] = None,
    ) -> AuditoriaLog:
        estado_anterior = {"id_caja": id_caja, "estado": "ABIERTA"}
        estado_nuevo = {
            "id_caja": id_caja,
            "monto_esperado": monto_esperado,
            "monto_real": monto_real,
            "diferencia": diferencia,
            "estado": "CERRADA",
        }
        return self.registrar_cambio_estado(
            accion=ACCION_CAJA_CIERRE,
            modulo=MODULO_CAJA,
            id_usuario=id_usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            motivo="Arqueo y cierre definitivo de turno",
        )

    def registrar_gasto(
        self,
        id_gasto: int,
        monto: float,
        descripcion: str,
        id_usuario: Optional[int] = None,
    ) -> AuditoriaLog:
        payload = {
            "id_gasto": id_gasto,
            "monto": monto,
            "descripcion": descripcion,
        }
        return self.registrar_evento(
            accion=ACCION_GASTO_REGISTRADO,
            modulo=MODULO_GASTOS,
            id_usuario=id_usuario,
            detalles=json.dumps(payload, ensure_ascii=False),
        )

    def registrar_merma(
        self,
        id_merma: int,
        id_insumo: int,
        cantidad: float,
        motivo: str,
        id_usuario: Optional[int] = None,
    ) -> AuditoriaLog:
        payload = {
            "id_merma": id_merma,
            "id_insumo": id_insumo,
            "cantidad": cantidad,
            "motivo": motivo,
        }
        return self.registrar_evento(
            accion=ACCION_MERMA_REGISTRADA,
            modulo=MODULO_INVENTARIO,
            id_usuario=id_usuario,
            detalles=json.dumps(payload, ensure_ascii=False),
        )

    def registrar_modificacion_precio(
        self,
        id_producto: int,
        precio_anterior: float,
        precio_nuevo: float,
        id_usuario: Optional[int] = None,
        motivo: Optional[str] = None,
    ) -> AuditoriaLog:
        estado_anterior = {"id_producto": id_producto, "precio": precio_anterior}
        estado_nuevo = {"id_producto": id_producto, "precio": precio_nuevo}
        return self.registrar_cambio_estado(
            accion=ACCION_PRECIO_MODIFICADO,
            modulo=MODULO_CATALOGO,
            id_usuario=id_usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            motivo=motivo,
        )

    def obtener_logs(
        self,
        limite: int = 100,
        modulo: Optional[str] = None,
        accion: Optional[str] = None,
        id_usuario: Optional[int] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> List[AuditoriaLog]:
        return self._repo.listar(
            limite=limite,
            modulo=modulo,
            accion=accion,
            id_usuario=id_usuario,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

    def obtener_log_por_id(self, id_log: int) -> Optional[AuditoriaLog]:
        return self._repo.obtener_por_id(id_log)

    def contar_logs(
        self,
        modulo: Optional[str] = None,
        accion: Optional[str] = None,
        id_usuario: Optional[int] = None,
    ) -> int:
        return self._repo.contar(modulo=modulo, accion=accion, id_usuario=id_usuario)


AuditoriaService = AuditService
