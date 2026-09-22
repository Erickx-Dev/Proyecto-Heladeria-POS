from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union

from src.core.exceptions import (
    CajaNoAbiertaError,
    CajaYaAbiertaError,
    GastoExcedeSaldoDisponibleError,
    MontoInvalidoError,
)
from src.domain.cash_register import Arqueo, TurnoCaja
from src.domain.expense import Gasto
from src.repositories.cash_repository import CashRepository


class CashService:

    def __init__(
        self, db_path: Optional[Union[str, Path]] = None
    ) -> None:
        self._repositorio: CashRepository = CashRepository(db_path=db_path)

    def abrir_turno(self, id_usuario: int, monto_inicial: float) -> TurnoCaja:
        if monto_inicial < 0.0:
            raise MontoInvalidoError(
                "El monto inicial de caja no puede ser negativo."
            )

        caja_existente: Optional[TurnoCaja] = self._repositorio.obtener_caja_activa()
        if caja_existente is not None:
            raise CajaYaAbiertaError()

        fecha_apertura: str = datetime.now().isoformat(sep=" ", timespec="seconds")
        turno: TurnoCaja = TurnoCaja(
            id_usuario=id_usuario,
            fecha_apertura=fecha_apertura,
            monto_inicial=monto_inicial,
        )

        id_generado: int = self._repositorio.crear_caja(turno)
        turno.id_caja = id_generado

        self._repositorio.registrar_auditoria(
            id_usuario=id_usuario,
            accion="APERTURA_CAJA",
            modulo="CAJA",
            detalles=(
                f"Turno de caja #{id_generado} abierto con monto inicial "
                f"de ${monto_inicial:,.2f} por usuario #{id_usuario}."
            ),
        )

        return turno

    def obtener_turno_activo(
        self, id_usuario: Optional[int] = None
    ) -> TurnoCaja:
        caja: Optional[TurnoCaja] = self._repositorio.obtener_caja_activa(
            id_usuario=id_usuario
        )
        if caja is None:
            raise CajaNoAbiertaError()
        return caja

    def registrar_gasto_menor(
        self,
        id_usuario: int,
        monto: float,
        descripcion: str,
        id_caja: Optional[int] = None,
    ) -> Gasto:
        if id_caja is not None:
            turno: Optional[TurnoCaja] = self._repositorio.obtener_caja_por_id(id_caja)
            if turno is None or not turno.esta_abierta():
                raise CajaNoAbiertaError()
        else:
            turno = self.obtener_turno_activo()
            id_caja = turno.id_caja

        fecha_hora: str = datetime.now().isoformat(sep=" ", timespec="seconds")
        gasto: Gasto = Gasto(
            id_caja=id_caja,
            fecha_hora=fecha_hora,
            monto=monto,
            descripcion=descripcion,
            id_usuario=id_usuario,
        )
        gasto.validar()

        total_ventas_efectivo: float = self._repositorio.obtener_total_ventas_efectivo(
            id_caja
        )
        total_gastos_previos: float = self._repositorio.obtener_total_gastos_por_caja(
            id_caja
        )
        saldo_disponible: float = (
            turno.monto_inicial + total_ventas_efectivo - total_gastos_previos
        )

        if monto > saldo_disponible:
            raise GastoExcedeSaldoDisponibleError(
                monto_solicitado=monto,
                saldo_disponible=saldo_disponible,
            )

        id_generado: int = self._repositorio.registrar_gasto(gasto)
        gasto.id_gasto = id_generado

        self._repositorio.registrar_auditoria(
            id_usuario=id_usuario,
            accion="GASTO_CAJA_MENOR",
            modulo="CAJA",
            detalles=(
                f"Gasto #{id_generado} registrado por ${monto:,.2f} - "
                f"Concepto: '{descripcion}' - Caja #{id_caja}."
            ),
        )

        return gasto

    def calcular_arqueo(
        self,
        monto_fisico_real: float,
        id_caja: Optional[int] = None,
    ) -> Arqueo:
        if monto_fisico_real < 0.0:
            raise MontoInvalidoError(
                "El monto físico contado no puede ser negativo."
            )

        if id_caja is not None:
            turno: Optional[TurnoCaja] = self._repositorio.obtener_caja_por_id(id_caja)
            if turno is None or not turno.esta_abierta():
                raise CajaNoAbiertaError()
        else:
            turno = self.obtener_turno_activo()
            id_caja = turno.id_caja

        total_ventas_efectivo: float = self._repositorio.obtener_total_ventas_efectivo(
            id_caja
        )
        total_gastos: float = self._repositorio.obtener_total_gastos_por_caja(
            id_caja
        )

        arqueo: Arqueo = Arqueo(
            monto_inicial=turno.monto_inicial,
            total_ventas_efectivo=total_ventas_efectivo,
            total_gastos=total_gastos,
            monto_fisico_real=monto_fisico_real,
        )

        return arqueo

    def cerrar_turno(
        self,
        id_usuario: int,
        monto_fisico_real: float,
        id_caja: Optional[int] = None,
    ) -> Tuple[TurnoCaja, Arqueo]:
        arqueo: Arqueo = self.calcular_arqueo(
            monto_fisico_real=monto_fisico_real,
            id_caja=id_caja,
        )

        if id_caja is not None:
            turno: TurnoCaja = self._repositorio.obtener_caja_por_id(id_caja)
        else:
            turno = self.obtener_turno_activo()
            id_caja = turno.id_caja

        fecha_cierre: str = datetime.now().isoformat(sep=" ", timespec="seconds")
        turno.cerrar(
            monto_final_real=monto_fisico_real,
            diferencia=arqueo.diferencia,
            fecha_cierre=fecha_cierre,
        )

        self._repositorio.actualizar_cierre_caja(
            id_caja=id_caja,
            fecha_cierre=turno.fecha_cierre,
            monto_final_real=monto_fisico_real,
            diferencia=arqueo.diferencia,
        )

        resumen = arqueo.obtener_resumen()
        self._repositorio.registrar_auditoria(
            id_usuario=id_usuario,
            accion="CIERRE_CAJA",
            modulo="CAJA",
            detalles=(
                f"Turno de caja #{id_caja} cerrado. "
                f"Saldo esperado: ${resumen['saldo_esperado']:,.2f} | "
                f"Efectivo contado: ${monto_fisico_real:,.2f} | "
                f"Diferencia: ${arqueo.diferencia:,.2f} ({arqueo.tipo_diferencia})."
            ),
        )

        return turno, arqueo
