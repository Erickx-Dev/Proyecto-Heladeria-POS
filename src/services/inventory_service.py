from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from database.connection import get_db_transaction
from src.core.exceptions import (
    CantidadInvalidaError,
    InsumoNoEncontradoError,
    MermaInvalidaError,
    StockInsuficienteError,
)
from src.domain.inventory import Insumo, NivelAlertaStock
from src.domain.waste import Merma
from src.repositories.inventory_repository import InventoryRepository


class InventoryService:

    def __init__(
        self,
        repository: Optional[InventoryRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._db_path = db_path
        self._repository: InventoryRepository = (
            repository if repository is not None else InventoryRepository(db_path=db_path)
        )

    def registrar_insumo(
        self,
        nombre: str,
        unidad_medida: str,
        stock_actual: float = 0.0,
        stock_minimo: float = 0.0,
    ) -> Insumo:
        insumo = Insumo(
            id_insumo=None,
            nombre=nombre,
            unidad_medida=unidad_medida,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
        )
        id_generado = self._repository.crear_insumo(insumo)
        insumo.id_insumo = id_generado
        return insumo

    def obtener_insumo(self, id_insumo: int) -> Insumo:
        insumo = self._repository.obtener_insumo_por_id(id_insumo)
        if insumo is None:
            raise InsumoNoEncontradoError(id_insumo)
        return insumo

    def listar_insumos(self) -> List[Insumo]:
        return self._repository.listar_insumos()

    def descontar_stock(
        self,
        id_insumo: int,
        cantidad: float,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Insumo:
        if cantidad <= 0.0:
            raise CantidadInvalidaError("La cantidad a descontar debe ser mayor a cero.")

        insumo = self._repository.obtener_insumo_por_id(id_insumo, conn=conn)
        if insumo is None:
            raise InsumoNoEncontradoError(id_insumo)

        if round(insumo.stock_actual, 4) < round(cantidad, 4):
            raise StockInsuficienteError(
                id_insumo=id_insumo,
                cantidad_solicitada=cantidad,
                stock_disponible=insumo.stock_actual,
            )

        exito = self._repository.descontar_stock(id_insumo, cantidad, conn=conn)
        if not exito:
            raise StockInsuficienteError(
                id_insumo=id_insumo,
                cantidad_solicitada=cantidad,
                stock_disponible=insumo.stock_actual,
            )

        insumo.descontar(cantidad)
        return insumo

    def incrementar_stock(
        self,
        id_insumo: int,
        cantidad: float,
        id_usuario: Optional[int] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Insumo:
        if cantidad <= 0.0:
            raise CantidadInvalidaError("La cantidad a incrementar debe ser mayor a cero.")

        insumo = self._repository.obtener_insumo_por_id(id_insumo, conn=conn)
        if insumo is None:
            raise InsumoNoEncontradoError(id_insumo)

        self._repository.incrementar_stock(id_insumo, cantidad, conn=conn)
        insumo.incrementar(cantidad)

        if id_usuario is not None:
            self._repository.registrar_auditoria(
                id_usuario=id_usuario,
                accion="REABASTECIMIENTO_INSUMO",
                modulo="INVENTARIO",
                detalles=f"Ingreso de {cantidad} {insumo.unidad_medida} al insumo #{id_insumo} ({insumo.nombre}). Nuevo stock: {insumo.stock_actual}.",
                conn=conn,
            )

        return insumo

    def verificar_alertas_stock(self) -> List[Dict[str, Any]]:
        insumos = self._repository.listar_insumos()
        alertas: List[Dict[str, Any]] = []
        for ins in insumos:
            nivel = ins.obtener_nivel_alerta()
            alertas.append({
                "id_insumo": ins.id_insumo,
                "nombre": ins.nombre,
                "unidad_medida": ins.unidad_medida,
                "stock_actual": ins.stock_actual,
                "stock_minimo": ins.stock_minimo,
                "nivel_alerta": nivel.value,
                "requiere_resurtido": ins.requiere_resurtido(),
            })
        return alertas

    def listar_insumos_criticos(self) -> List[Insumo]:
        insumos = self._repository.listar_insumos()
        return [ins for ins in insumos if ins.obtener_nivel_alerta() == NivelAlertaStock.CRITICO]

    def registrar_merma(
        self,
        id_insumo: int,
        cantidad: float,
        motivo: str,
        id_usuario: int,
        fecha_hora: Optional[str] = None,
    ) -> Merma:
        if cantidad <= 0.0:
            raise MermaInvalidaError("La cantidad mermada debe ser mayor a cero.")
        if not motivo or not motivo.strip():
            raise MermaInvalidaError("El motivo o justificación de la merma no puede estar vacío.")

        fecha = (
            fecha_hora
            if fecha_hora is not None
            else datetime.now().isoformat(sep=" ", timespec="seconds")
        )

        merma = Merma(
            id_insumo=id_insumo,
            cantidad=cantidad,
            motivo=motivo.strip(),
            fecha_hora=fecha,
            id_usuario=id_usuario,
        )

        with get_db_transaction(self._db_path) as conn:
            insumo = self._repository.obtener_insumo_por_id(id_insumo, conn=conn)
            if insumo is None:
                raise InsumoNoEncontradoError(id_insumo)

            if round(insumo.stock_actual, 4) < round(cantidad, 4):
                raise StockInsuficienteError(
                    id_insumo=id_insumo,
                    cantidad_solicitada=cantidad,
                    stock_disponible=insumo.stock_actual,
                )

            self._repository.descontar_stock(id_insumo, cantidad, conn=conn)
            id_merma = self._repository.registrar_merma(merma, conn=conn)
            merma.id_merma = id_merma

            self._repository.registrar_auditoria(
                id_usuario=id_usuario,
                accion="REGISTRO_MERMA",
                modulo="INVENTARIO",
                detalles=(
                    f"Merma #{id_merma} registrada: Descarte de {cantidad} {insumo.unidad_medida} "
                    f"del insumo '{insumo.nombre}' (#{id_insumo}). Motivo: {motivo}."
                ),
                conn=conn,
            )

        return merma

    def listar_mermas(self) -> List[Merma]:
        return self._repository.listar_mermas()
