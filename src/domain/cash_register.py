from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Union


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
        self.monto_final_real = monto_final_real
        self.diferencia = diferencia
        self.fecha_cierre = fecha_cierre or datetime.now().isoformat(
            sep=" ", timespec="seconds"
        )
        self.estado = ESTADO_CERRADA


@dataclass
class Arqueo:

    monto_inicial: float = 0.0
    total_ventas_efectivo: float = 0.0
    total_gastos: float = 0.0
    monto_fisico_real: float = 0.0

    @property
    def saldo_esperado(self) -> float:
        return self.monto_inicial + self.total_ventas_efectivo - self.total_gastos

    @property
    def diferencia(self) -> float:
        return round(self.monto_fisico_real - self.saldo_esperado, 2)

    @property
    def tipo_diferencia(self) -> str:
        diferencia: float = self.diferencia
        if diferencia == 0.0:
            return "CUADRADO"
        elif diferencia > 0.0:
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
