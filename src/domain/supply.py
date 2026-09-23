from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.exceptions import StockInsuficienteError, ValidacionError


@dataclass
class Insumo:

    id_insumo: Optional[int] = None
    nombre: str = ""
    unidad_medida: str = ""
    stock_actual: float = 0.0
    stock_minimo: float = 0.0

    def esta_en_alerta_stock(self) -> bool:
        return self.stock_actual <= self.stock_minimo

    def descontar(self, cantidad: float) -> None:
        if cantidad <= 0.0:
            raise ValidacionError("La cantidad a descontar debe ser mayor a cero.")
        if cantidad > self.stock_actual:
            raise StockInsuficienteError(
                f"Stock insuficiente para {self.nombre}. Disponible: {self.stock_actual}, Solicitado: {cantidad}."
            )
        self.stock_actual = round(self.stock_actual - cantidad, 4)

    def reabastecer(self, cantidad: float) -> None:
        if cantidad <= 0.0:
            raise ValidacionError("La cantidad a reabastecer debe ser mayor a cero.")
        self.stock_actual = round(self.stock_actual + cantidad, 4)

    def validar(self) -> None:
        if not self.nombre or not self.nombre.strip():
            raise ValidacionError("El nombre del insumo no puede estar vacío.")

        if not self.unidad_medida or not self.unidad_medida.strip():
            raise ValidacionError("La unidad de medida no puede estar vacía.")

        if self.stock_actual < 0.0:
            raise ValidacionError("El stock actual no puede ser negativo.")

        if self.stock_minimo < 0.0:
            raise ValidacionError("El stock mínimo no puede ser negativo.")
