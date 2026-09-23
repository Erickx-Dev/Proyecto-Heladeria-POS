from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.core.exceptions import CantidadInvalidaError, StockInsuficienteError


class NivelAlertaStock(str, Enum):
    NORMAL = "VERDE"
    ADVERTENCIA = "NARANJA"
    CRITICO = "ROJO"


@dataclass
class Insumo:
    id_insumo: Optional[int]
    nombre: str
    unidad_medida: str
    stock_actual: float = 0.0
    stock_minimo: float = 0.0

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del insumo no puede estar vacío.")
        if not self.unidad_medida or not self.unidad_medida.strip():
            raise ValueError("La unidad de medida no puede estar vacía.")
        if self.stock_actual < 0.0:
            raise ValueError("El stock actual no puede ser negativo.")
        if self.stock_minimo < 0.0:
            raise ValueError("El stock mínimo no puede ser negativo.")

    def descontar(self, cantidad: float) -> None:
        if cantidad <= 0.0:
            raise CantidadInvalidaError("La cantidad a descontar debe ser mayor a cero.")
        if round(self.stock_actual, 4) < round(cantidad, 4):
            raise StockInsuficienteError(
                id_insumo=self.id_insumo or 0,
                cantidad_solicitada=cantidad,
                stock_disponible=self.stock_actual,
            )
        self.stock_actual = round(self.stock_actual - cantidad, 4)

    def incrementar(self, cantidad: float) -> None:
        if cantidad <= 0.0:
            raise CantidadInvalidaError("La cantidad a incrementar debe ser mayor a cero.")
        self.stock_actual = round(self.stock_actual + cantidad, 4)

    def obtener_nivel_alerta(self) -> NivelAlertaStock:
        if self.stock_actual <= self.stock_minimo:
            return NivelAlertaStock.CRITICO
        if self.stock_actual <= (self.stock_minimo * 1.5):
            return NivelAlertaStock.ADVERTENCIA
        return NivelAlertaStock.NORMAL

    def requiere_resurtido(self) -> bool:
        return self.stock_actual <= self.stock_minimo
