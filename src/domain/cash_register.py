from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Union

from src.core.exceptions import MontoInvalidoError, ValidacionError

ESTADO_ABIERTA: str = "ABIERTA"
ESTADO_CERRADA: str = "CERRADA"


@dataclass
class TurnoCaja:

    id_caja: Optional[int] = None
    id_usuario: int = 0
    fecha_apertura: str = ""
    monto_inicial: float = 0.0
    fecha_cierre: Optional[str] = None
    monto_final_real: Optional[float] = None
    diferencia: Optional[float] = None
    estado: str = field(default=ESTADO_ABIERTA)

    def esta_abierta(self) -> bool:
        return self.estado == ESTADO_ABIERTA

    def cerrar(
        self,
        monto_final_real: float,
        diferencia: float,
        fecha_cierre: Optional[str] = None,
    ) -> None:
        if monto_final_real < 0.0:
            raise MontoInvalidoError("El monto final contado no puede ser negativo.")
        self.monto_final_real = monto_final_real
        self.diferencia = diferencia
        self.fecha_cierre = fecha_cierre or datetime.now().isoformat(
            sep=" ", timespec="seconds"
        )
        self.estado = ESTADO_CERRADA

    def validar(self) -> None:
        if self.id_usuario <= 0:
            raise ValidacionError("El id_usuario debe ser un identificador válido.")
        if self.monto_inicial < 0.0:
            raise MontoInvalidoError("El monto inicial de caja no puede ser negativo.")
        if self.estado not in (ESTADO_ABIERTA, ESTADO_CERRADA):
            raise ValidacionError("El estado de la caja debe ser ABIERTA o CERRADA.")


@dataclass
class Arqueo:

    monto_inicial: float = 0.0
    total_ventas_efectivo: float = 0.0
    total_gastos: float = 0.0
    monto_fisico_real: float = 0.0

    @property
    def saldo_esperado(self) -> float:
        return round(self.monto_inicial + self.total_ventas_efectivo - self.total_gastos, 2)

    @property
    def diferencia(self) -> float:
        return round(self.monto_fisico_real - self.saldo_esperado, 2)

    @property
    def tipo_diferencia(self) -> str:
        dif: float = self.diferencia
        if dif == 0.0:
            return "CUADRADO"
        elif dif > 0.0:
            return "SOBRANTE"
        else:
            return "FALTANTE"

    def obtener_resumen(self) -> Dict[str, Union[float, str]]:
        return {
            "monto_inicial": self.monto_inicial,
            "total_ventas_efectivo": self.total_ventas_efectivo,
            "total_gastos": self.total_gastos,
            "saldo_esperado": self.saldo_esperado,
            "monto_fisico_real": self.monto_fisico_real,
            "diferencia": self.diferencia,
            "tipo_diferencia": self.tipo_diferencia,
        }
