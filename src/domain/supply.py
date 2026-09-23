from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Insumo:
    nombre: str
    unidad_medida: str
    stock_actual: float = 0.0
    stock_minimo: float = 0.0
    id_insumo: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del insumo no puede estar vacío.")
        if not self.unidad_medida or not self.unidad_medida.strip():
            raise ValueError("La unidad de medida no puede estar vacía.")
        if self.stock_actual < 0:
            raise ValueError("El stock actual no puede ser un valor negativo.")
        if self.stock_minimo < 0:
            raise ValueError("El stock mínimo no puede ser un valor negativo.")

        self.nombre = self.nombre.strip()
        self.unidad_medida = self.unidad_medida.strip()
        self.stock_actual = float(self.stock_actual)
        self.stock_minimo = float(self.stock_minimo)

    def esta_en_stock_minimo(self) -> bool:
        return self.stock_actual <= self.stock_minimo

    def asentar_abastecimiento(self, cantidad: float) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad de abastecimiento debe ser estrictamente positiva (> 0).")
        self.stock_actual = round(self.stock_actual + cantidad, 4)

    def deducir_stock(self, cantidad: float) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad a deducir debe ser estrictamente positiva (> 0).")
        if cantidad > self.stock_actual:
            raise ValueError(
                f"Stock insuficiente para {self.nombre}. Disponible: {self.stock_actual}, Requerido: {cantidad}."
            )
        self.stock_actual = round(self.stock_actual - cantidad, 4)
