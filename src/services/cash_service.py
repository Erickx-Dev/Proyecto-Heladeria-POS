from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from database.connection import get_db_transaction
from src.core.exceptions import (
    CajaNoAbiertaError,
    CajaYaAbiertaError,
    MontoInvalidoError,
)
from src.domain.cash_register import Arqueo, TurnoCaja
from src.repositories.cash_repository import CashRepository
from src.repositories.expense_repository import ExpenseRepository


class CashService:

    def __init__(
        self,
        cash_repository: Optional[CashRepository] = None,
        expense_repository: Optional[ExpenseRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path
        self._cash_repo: CashRepository = cash_repository or CashRepository(db_path=db_path)
        self._expense_repo: ExpenseRepository = expense_repository or ExpenseRepository(db_path=db_path)

    def _registrar_auditoria(
        self,
        accion: str,
        id_usuario: Optional[int],
        detalles: str,
    ) -> None:
        """Registra un evento en AuditoriaLog con módulo 'CAJA'."""
        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_transaction(self._db_path) as conn:
            conn.execute(
                "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) "
                "VALUES (?, ?, ?, ?, ?);",
                (id_usuario, accion, "CAJA", fecha_hora, detalles),
            )

    def abrir_turno(self, id_usuario: int, monto_inicial: float) -> TurnoCaja:
        """Abre un nuevo turno de caja.

        Raises:
            CajaYaAbiertaError: Si ya hay un turno abierto.
            MontoInvalidoError: Si el monto inicial es negativo.
        """
        if monto_inicial < 0.0:
            raise MontoInvalidoError("El monto inicial no puede ser negativo.")

        caja_activa: Optional[TurnoCaja] = self._cash_repo.obtener_caja_activa()
        if caja_activa is not None:
            raise CajaYaAbiertaError()

        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id_caja: int = self._cash_repo.abrir_caja(id_usuario, monto_inicial, fecha_hora)

        self._registrar_auditoria(
            "CAJA_ABIERTA",
            id_usuario,
            f"Turno id={id_caja} abierto con fondo base de ${monto_inicial:,.2f}.",
        )

        turno: Optional[TurnoCaja] = self._cash_repo.obtener_caja_por_id(id_caja)
        return turno  # type: ignore[return-value]

    def obtener_turno_activo(self) -> TurnoCaja:
        """Retorna el turno activo o lanza CajaNoAbiertaError.

        Método esencial para validar que el POS puede operar.

        Raises:
            CajaNoAbiertaError: Si no existe una caja abierta.
        """
        caja: Optional[TurnoCaja] = self._cash_repo.obtener_caja_activa()
        if caja is None:
            raise CajaNoAbiertaError()
        return caja

    def cerrar_turno(self, id_usuario: int, monto_fisico_real: float) -> Arqueo:
        """Cierra el turno activo con conciliación de arqueo.

        Fórmula de arqueo:
            Saldo Esperado = Monto Inicial + Σ Ventas Efectivo - Σ Gastos
            Diferencia = Monto Físico Declarado - Saldo Esperado

        Raises:
            CajaNoAbiertaError: Si no hay turno abierto.
            MontoInvalidoError: Si monto_fisico_real es negativo.
        """
        if monto_fisico_real < 0.0:
            raise MontoInvalidoError("El monto físico declarado no puede ser negativo.")

        caja: TurnoCaja = self.obtener_turno_activo()

        # Calcular componentes del arqueo
        total_ventas_efectivo: float = self._cash_repo.obtener_total_ventas_efectivo(caja.id_caja)
        total_gastos: float = self._expense_repo.calcular_total_gastos(caja.id_caja)

        arqueo: Arqueo = Arqueo(
            monto_inicial=caja.monto_inicial,
            total_ventas_efectivo=total_ventas_efectivo,
            total_gastos=total_gastos,
            monto_fisico_real=monto_fisico_real,
        )

        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._cash_repo.cerrar_caja(
            caja.id_caja, monto_fisico_real, arqueo.diferencia, fecha_hora,  # type: ignore[arg-type]
        )

        self._registrar_auditoria(
            "CAJA_CERRADA",
            id_usuario,
            f"Turno id={caja.id_caja} cerrado. "
            f"Esperado=${arqueo.saldo_esperado:,.2f}, "
            f"Físico=${monto_fisico_real:,.2f}, "
            f"Diferencia=${arqueo.diferencia:,.2f} ({arqueo.tipo_diferencia}).",
        )

        return arqueo

    def obtener_saldo_disponible(self, id_caja: int) -> float:
        """Calcula el saldo disponible actual en la gaveta.

        Saldo = Monto Inicial + Ventas Efectivo - Gastos
        """
        caja: Optional[TurnoCaja] = self._cash_repo.obtener_caja_por_id(id_caja)
        if caja is None:
            raise CajaNoAbiertaError("No existe la caja especificada.")

        total_ventas: float = self._cash_repo.obtener_total_ventas_efectivo(id_caja)
        total_gastos: float = self._expense_repo.calcular_total_gastos(id_caja)
        return round(caja.monto_inicial + total_ventas - total_gastos, 2)
