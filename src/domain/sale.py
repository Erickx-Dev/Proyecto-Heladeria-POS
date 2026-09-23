from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.core.exceptions import MontoInvalidoError, PagoInsuficienteError, ValidacionError

METODOS_PAGO_VALIDOS: tuple[str, ...] = ("EFECTIVO", "TARJETA", "TRANSFERENCIA", "OTRO")


@dataclass
class DetalleVenta:

    id_detalle: Optional[int] = None
    id_venta: int = 0
    id_producto: int = 0
    cantidad: int = 1
    precio_unitario: float = 0.0
    subtotal: float = 0.0

    def calcular_subtotal(self) -> float:
        self.subtotal = round(self.cantidad * self.precio_unitario, 2)
        return self.subtotal

    def validar(self) -> None:
        if self.id_producto <= 0:
            raise ValidacionError("El id_producto debe ser un identificador válido.")
        if self.cantidad <= 0:
            raise ValidacionError("La cantidad del producto debe ser mayor a cero.")
        if self.precio_unitario < 0.0:
            raise MontoInvalidoError("El precio unitario no puede ser negativo.")


@dataclass
class Venta:

    id_venta: Optional[int] = None
    id_caja: int = 0
    fecha_hora: str = ""
    total: float = 0.0
    metodo_pago: str = "EFECTIVO"
    dinero_recibido: float = 0.0
    cambio: float = 0.0
    detalles: List[DetalleVenta] = field(default_factory=list)

    def calcular_cambio(self) -> float:
        if self.metodo_pago == "EFECTIVO":
            if self.dinero_recibido < self.total:
                raise PagoInsuficienteError(
                    f"Dinero recibido (${self.dinero_recibido:,.2f}) es menor al total (${self.total:,.2f})."
                )
            self.cambio = round(self.dinero_recibido - self.total, 2)
        else:
            self.dinero_recibido = self.total
            self.cambio = 0.0
        return self.cambio

    def agregar_detalle(self, detalle: DetalleVenta) -> None:
        detalle.validar()
        detalle.calcular_subtotal()
        self.detalles.append(detalle)
        self.total = round(sum(d.subtotal for d in self.detalles), 2)

    def validar(self) -> None:
        if self.id_caja <= 0:
            raise ValidacionError("El id_caja debe ser un identificador válido.")

        if self.metodo_pago not in METODOS_PAGO_VALIDOS:
            raise ValidacionError(
                f"Método de pago inválido: '{self.metodo_pago}'. Válidos: {METODOS_PAGO_VALIDOS}."
            )

        if self.total < 0.0:
            raise MontoInvalidoError("El total de la venta no puede ser negativo.")

        if self.metodo_pago == "EFECTIVO" and self.dinero_recibido < self.total:
            raise PagoInsuficienteError()
