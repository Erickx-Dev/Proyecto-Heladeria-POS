from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from src.core.exceptions import (
    CantidadInvalidaError,
    MetodoPagoInvalidoError,
    PagoInsuficienteError,
    VentaSinItemsError,
)


class MetodoPago(str, Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"
    OTRO = "OTRO"

    @classmethod
    def es_valido(cls, valor: str) -> bool:
        return valor.upper() in cls._value2member_map_


@dataclass
class DetalleVenta:
    id_producto: int
    cantidad: int
    precio_unitario: float
    subtotal: float = 0.0
    id_detalle: Optional[int] = None
    id_venta: Optional[int] = None
    nombre_producto: Optional[str] = None

    def __post_init__(self) -> None:
        self.validar()
        if self.subtotal == 0.0:
            self.subtotal = self.calcular_subtotal()

    def validar(self) -> None:
        if self.id_producto <= 0:
            raise ValueError("El ID de producto debe ser mayor a cero.")
        if self.cantidad <= 0:
            raise CantidadInvalidaError("La cantidad vendida debe ser mayor a cero.")
        if self.precio_unitario < 0.0:
            raise ValueError("El precio unitario no puede ser negativo.")

    def calcular_subtotal(self) -> float:
        return round(self.cantidad * self.precio_unitario, 2)


@dataclass
class Venta:
    id_caja: int
    fecha_hora: str
    total: float = 0.0
    metodo_pago: str = MetodoPago.EFECTIVO.value
    dinero_recibido: float = 0.0
    cambio: float = 0.0
    detalles: List[DetalleVenta] = field(default_factory=list)
    id_venta: Optional[int] = None

    def __post_init__(self) -> None:
        self.metodo_pago = self.metodo_pago.upper()
        if self.detalles and self.total == 0.0:
            self.recalcular_total()

    def agregar_detalle(self, detalle: DetalleVenta) -> None:
        detalle.validar()
        self.detalles.append(detalle)
        self.recalcular_total()

    def recalcular_total(self) -> float:
        self.total = round(sum(d.calcular_subtotal() for d in self.detalles), 2)
        return self.total

    def liquidar_pago(self, metodo_pago: str, dinero_recibido: float = 0.0) -> float:
        metodo_normalizado = metodo_pago.strip().upper()
        if not MetodoPago.es_valido(metodo_normalizado):
            raise MetodoPagoInvalidoError(metodo_pago)

        self.metodo_pago = metodo_normalizado

        if self.total == 0.0:
            self.recalcular_total()

        if self.metodo_pago == MetodoPago.EFECTIVO.value:
            if round(dinero_recibido, 2) < round(self.total, 2):
                raise PagoInsuficienteError(
                    total_requerido=self.total,
                    monto_pagado=dinero_recibido,
                )
            self.dinero_recibido = round(dinero_recibido, 2)
            self.cambio = round(self.dinero_recibido - self.total, 2)
        else:
            self.dinero_recibido = self.total
            self.cambio = 0.0

        return self.cambio

    def validar(self) -> None:
        if self.id_caja <= 0:
            raise ValueError("El ID de caja debe ser mayor a cero.")
        if not self.fecha_hora or not self.fecha_hora.strip():
            raise ValueError("La fecha y hora de la venta no pueden estar vacías.")
        if not self.detalles:
            raise VentaSinItemsError()
        if not MetodoPago.es_valido(self.metodo_pago):
            raise MetodoPagoInvalidoError(self.metodo_pago)
        if self.total < 0.0:
            raise ValueError("El total de la venta no puede ser negativo.")


@dataclass
class TicketVenta:
    id_venta: int
    id_caja: int
    fecha_hora: str
    metodo_pago: str
    total: float
    dinero_recibido: float
    cambio: float
    items: List[Dict[str, Any]] = field(default_factory=list)

    def generar_texto(self, ancho: int = 40) -> str:
        linea = "=" * ancho
        separador = "-" * ancho
        lineas = [
            linea,
            "HELADERIA ARTESANAL POS".center(ancho),
            "COMPROBANTE DE PAGO".center(ancho),
            linea,
            f"Venta Consecutiva: #{self.id_venta:<6} Caja: #{self.id_caja}",
            f"Fecha y Hora: {self.fecha_hora}",
            f"Metodo de Pago: {self.metodo_pago}",
            separador,
            f"{'CANT':<5}{'PRODUCTO':<23}{'TOTAL':>12}",
            separador,
        ]
        for it in self.items:
            cant = str(it.get("cantidad", 1))
            nom = str(it.get("nombre", "Producto"))[:22]
            sub = f"${float(it.get('subtotal', 0.0)):,.2f}"
            lineas.append(f"{cant:<5}{nom:<23}{sub:>12}")
        lineas.extend([
            separador,
            f"{'TOTAL A PAGAR:':<26}{f'${self.total:,.2f}':>14}",
            f"{'PAGO RECIBIDO:':<26}{f'${self.dinero_recibido:,.2f}':>14}",
            f"{'CAMBIO / DEVUELTA:':<26}{f'${self.cambio:,.2f}':>14}",
            linea,
            "Gracias por su compra".center(ancho),
            linea,
        ])
        return "\n".join(lineas)
