from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.core.exceptions import (
    CajaNoAbiertaError,
    StockInsuficienteError,
    ValidacionError,
)
from src.domain.cash_register import TurnoCaja
from src.domain.product import Producto
from src.domain.sale import METODOS_PAGO_VALIDOS, DetalleVenta, Venta
from src.repositories.cash_repository import CashRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.recipe_repository import RecipeRepository
from src.repositories.sale_repository import SaleRepository
from src.repositories.supply_repository import SupplyRepository


@dataclass
class ItemVenta:
    """Línea de comanda: producto (o topping, que también es un producto) y cantidad."""

    id_producto: int
    cantidad: int = 1


class POSService:

    def __init__(
        self,
        sale_repository: Optional[SaleRepository] = None,
        cash_repository: Optional[CashRepository] = None,
        product_repository: Optional[ProductRepository] = None,
        recipe_repository: Optional[RecipeRepository] = None,
        supply_repository: Optional[SupplyRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._sale_repo: SaleRepository = sale_repository or SaleRepository(db_path=db_path)
        self._cash_repo: CashRepository = cash_repository or CashRepository(db_path=db_path)
        self._product_repo: ProductRepository = product_repository or ProductRepository(db_path=db_path)
        self._recipe_repo: RecipeRepository = recipe_repository or RecipeRepository(db_path=db_path)
        self._supply_repo: SupplyRepository = supply_repository or SupplyRepository(db_path=db_path)

    def _obtener_turno_abierto(self) -> TurnoCaja:
        caja: Optional[TurnoCaja] = self._cash_repo.obtener_caja_activa()
        if caja is None:
            raise CajaNoAbiertaError()
        return caja

    def _construir_detalles(self, items: List[ItemVenta]) -> List[DetalleVenta]:
        detalles: List[DetalleVenta] = []
        for item in items:
            if item.cantidad <= 0:
                raise ValidacionError("La cantidad de cada producto debe ser mayor a cero.")

            producto: Optional[Producto] = self._product_repo.obtener_por_id(item.id_producto)
            if producto is None:
                raise ValidacionError(f"No existe el producto con id {item.id_producto}.")
            if not producto.es_activo():
                raise ValidacionError(f"El producto '{producto.nombre}' está suspendido y no puede venderse.")

            detalles.append(
                DetalleVenta(
                    id_producto=producto.id_producto,
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio_venta,
                )
            )
        return detalles

    def _verificar_stock(self, detalles: List[DetalleVenta]) -> None:
        """Comprobación preventiva agregando el consumo total por insumo."""
        requerido: Dict[int, float] = {}
        for detalle in detalles:
            for receta in self._recipe_repo.obtener_receta_por_producto(detalle.id_producto):
                requerido[receta.id_insumo] = round(
                    requerido.get(receta.id_insumo, 0.0) + receta.cantidad_necesaria * detalle.cantidad,
                    4,
                )

        for id_insumo, cantidad in requerido.items():
            insumo = self._supply_repo.obtener_por_id(id_insumo)
            if insumo is None:
                raise ValidacionError(f"No existe el insumo con id {id_insumo}.")
            if cantidad > insumo.stock_actual:
                raise StockInsuficienteError(
                    f"Stock insuficiente para {insumo.nombre}. "
                    f"Disponible: {insumo.stock_actual}, Requerido: {cantidad}."
                )

    def calcular_total(self, items: List[ItemVenta]) -> float:
        """Calcula el total de una comanda con los precios vigentes (para mostrar en UI)."""
        if not items:
            raise ValidacionError("La comanda debe contener al menos un producto.")
        venta: Venta = Venta()
        for detalle in self._construir_detalles(items):
            venta.agregar_detalle(detalle)
        return venta.total

    def registrar_venta(
        self,
        id_usuario: int,
        items: List[ItemVenta],
        metodo_pago: str,
        dinero_recibido: Optional[float] = None,
    ) -> Venta:
        if not items:
            raise ValidacionError("La comanda debe contener al menos un producto.")

        metodo: str = (metodo_pago or "").strip().upper()
        if metodo not in METODOS_PAGO_VALIDOS:
            raise ValidacionError(
                f"Método de pago inválido: '{metodo_pago}'. Válidos: {METODOS_PAGO_VALIDOS}."
            )

        caja: TurnoCaja = self._obtener_turno_abierto()
        detalles: List[DetalleVenta] = self._construir_detalles(items)
        self._verificar_stock(detalles)

        venta: Venta = Venta(
            id_caja=caja.id_caja,
            fecha_hora=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            metodo_pago=metodo,
        )
        for detalle in detalles:
            venta.agregar_detalle(detalle)

        if metodo == "EFECTIVO":
            if dinero_recibido is None:
                raise ValidacionError("Debe indicar el dinero recibido para pagos en efectivo.")
            venta.dinero_recibido = round(dinero_recibido, 2)
        venta.calcular_cambio()

        venta.id_venta = self._sale_repo.registrar_venta(venta, id_usuario)
        for detalle in venta.detalles:
            detalle.id_venta = venta.id_venta
        return venta

    def obtener_venta(self, id_venta: int) -> Venta:
        venta: Optional[Venta] = self._sale_repo.obtener_venta_por_id(id_venta)
        if venta is None:
            raise ValidacionError(f"No existe la venta con id {id_venta}.")
        return venta
