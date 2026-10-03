from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_transaction
from src.core.exceptions import (
    CajaNoAbiertaError,
    GastoExcedeSaldoDisponibleError,
    MontoInvalidoError,
    ValidacionError,
)
from src.domain.expense import Gasto
from src.repositories.expense_repository import ExpenseRepository
from src.services.cash_service import CashService


class ExpenseService:

    def __init__(
        self,
        expense_repository: Optional[ExpenseRepository] = None,
        cash_service: Optional[CashService] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path
        self._expense_repo: ExpenseRepository = expense_repository or ExpenseRepository(db_path=db_path)
        self._cash_service: CashService = cash_service or CashService(db_path=db_path)

    def _registrar_auditoria(
        self,
        accion: str,
        id_usuario: Optional[int],
        detalles: str,
    ) -> None:
        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_transaction(self._db_path) as conn:
            conn.execute(
                "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) "
                "VALUES (?, ?, ?, ?, ?);",
                (id_usuario, accion, "GASTOS", fecha_hora, detalles),
            )

    def registrar_gasto(
        self,
        id_usuario: int,
        monto: float,
        descripcion: str,
    ) -> Gasto:
        turno = self._cash_service.obtener_turno_activo()

        if monto <= 0.0:
            raise MontoInvalidoError("El monto del gasto debe ser mayor a cero.")

        if not descripcion or not descripcion.strip():
            raise ValidacionError("La descripción del gasto es obligatoria.")

        saldo_disponible: float = self._cash_service.obtener_saldo_disponible(turno.id_caja)
        if monto > saldo_disponible:
            raise GastoExcedeSaldoDisponibleError(
                monto_solicitado=monto,
                saldo_disponible=saldo_disponible,
            )

        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gasto: Gasto = Gasto(
            id_caja=turno.id_caja,
            fecha_hora=fecha_hora,
            monto=monto,
            descripcion=descripcion.strip(),
            id_usuario=id_usuario,
        )
        id_gasto: int = self._expense_repo.registrar_gasto(gasto)
        gasto.id_gasto = id_gasto

        self._registrar_auditoria(
            "GASTO_REGISTRADO",
            id_usuario,
            f"Gasto id={id_gasto} de ${monto:,.2f} registrado en caja id={turno.id_caja}. "
            f"Descripción: '{descripcion.strip()}'.",
        )

        return gasto

    def listar_gastos_turno_activo(self) -> List[Gasto]:
        turno = self._cash_service.obtener_turno_activo()
        return self._expense_repo.listar_gastos_por_caja(turno.id_caja)

    def obtener_total_gastos_turno_activo(self) -> float:
        turno = self._cash_service.obtener_turno_activo()
        return self._expense_repo.calcular_total_gastos(turno.id_caja)
