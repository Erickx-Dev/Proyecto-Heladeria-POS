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
        """Registra un evento en AuditoriaLog con módulo 'GASTOS'."""
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
        """Registra un gasto de caja menor.

        Validaciones:
            1. Debe existir un turno de caja abierto.
            2. El monto debe ser estrictamente positivo.
            3. La descripción debe ser una justificación no vacía.
            4. El monto no debe exceder el saldo disponible en gaveta.

        Raises:
            CajaNoAbiertaError: Si no hay turno abierto.
            MontoInvalidoError: Si el monto no es positivo.
            ValidacionError: Si la descripción está vacía.
            GastoExcedeSaldoDisponibleError: Si no hay liquidez suficiente.
        """
        # 1. Validar turno abierto
        turno = self._cash_service.obtener_turno_activo()

        # 2. Validar monto positivo
        if monto <= 0.0:
            raise MontoInvalidoError("El monto del gasto debe ser mayor a cero.")

        # 3. Validar descripción justificada
        if not descripcion or not descripcion.strip():
            raise ValidacionError("La descripción del gasto es obligatoria.")

        # 4. Verificar liquidez suficiente en gaveta
        saldo_disponible: float = self._cash_service.obtener_saldo_disponible(turno.id_caja)  # type: ignore[arg-type]
        if monto > saldo_disponible:
            raise GastoExcedeSaldoDisponibleError(
                monto_solicitado=monto,
                saldo_disponible=saldo_disponible,
            )

        # 5. Crear y persistir gasto
        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gasto: Gasto = Gasto(
            id_caja=turno.id_caja,  # type: ignore[arg-type]
            fecha_hora=fecha_hora,
            monto=monto,
            descripcion=descripcion.strip(),
            id_usuario=id_usuario,
        )
        id_gasto: int = self._expense_repo.registrar_gasto(gasto)
        gasto.id_gasto = id_gasto

        # 6. Auditoría
        self._registrar_auditoria(
            "GASTO_REGISTRADO",
            id_usuario,
            f"Gasto id={id_gasto} de ${monto:,.2f} registrado en caja id={turno.id_caja}. "
            f"Descripción: '{descripcion.strip()}'.",
        )

        return gasto

    def listar_gastos_turno_activo(self) -> List[Gasto]:
        """Lista todos los gastos del turno activo actual.

        Raises:
            CajaNoAbiertaError: Si no hay turno abierto.
        """
        turno = self._cash_service.obtener_turno_activo()
        return self._expense_repo.listar_gastos_por_caja(turno.id_caja)  # type: ignore[arg-type]

    def obtener_total_gastos_turno_activo(self) -> float:
        """Retorna el total de gastos del turno activo.

        Raises:
            CajaNoAbiertaError: Si no hay turno abierto.
        """
        turno = self._cash_service.obtener_turno_activo()
        return self._expense_repo.calcular_total_gastos(turno.id_caja)  # type: ignore[arg-type]
