from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from database.connection import get_db_transaction
from src.core.exceptions import (
    CajaNoAbiertaError,
    CantidadInvalidaError,
    ProductoNoEncontradoError,
    VentaSinItemsError,
)
from src.domain.sale import DetalleVenta, TicketVenta, Venta
from src.repositories.cash_repository import CashRepository
from src.repositories.inventory_repository import InventoryRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.sale_repository import SaleRepository
from src.services.inventory_service import InventoryService


class SaleService:

    def __init__(
        self,
        sale_repository: Optional[SaleRepository] = None,
        product_repository: Optional[ProductRepository] = None,
        inventory_repository: Optional[InventoryRepository] = None,
        cash_repository: Optional[CashRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._db_path = db_path
        self._sale_repo: SaleRepository = (
            sale_repository if sale_repository is not None else SaleRepository(db_path=db_path)
        )
        self._product_repo: ProductRepository = (
            product_repository if product_repository is not None else ProductRepository(db_path=db_path)
        )
        self._inventory_repo: InventoryRepository = (
            inventory_repository if inventory_repository is not None else InventoryRepository(db_path=db_path)
        )
        self._cash_repo: CashRepository = (
            cash_repository if cash_repository is not None else CashRepository(db_path=db_path)
        )
        self._inventory_service: InventoryService = InventoryService(
            repository=self._inventory_repo, db_path=db_path
        )

    def calcular_comanda(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not items:
            raise VentaSinItemsError("La comanda no contiene ítems.")

        desglose: List[Dict[str, Any]] = []
        total = 0.0

        for item in items:
            id_producto = int(item["id_producto"])
            cantidad = int(item["cantidad"])
            if cantidad <= 0:
                raise CantidadInvalidaError(f"La cantidad para el producto #{id_producto} debe ser mayor a cero.")

            producto = self._product_repo.obtener_producto_por_id(id_producto)
            if producto is None:
                raise ProductoNoEncontradoError(id_producto)

            precio_unitario = float(item.get("precio_unitario", producto.precio_venta))
            subtotal = round(cantidad * precio_unitario, 2)
            total = round(total + subtotal, 2)

            desglose.append({
                "id_producto": id_producto,
                "nombre": producto.nombre,
                "codigo": producto.codigo,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal,
            })

        return {
            "items": desglose,
            "total": total,
            "cantidad_items": sum(i["cantidad"] for i in desglose),
        }

    def procesar_venta(
        self,
        items: List[Dict[str, Any]],
        metodo_pago: str,
        dinero_recibido: float = 0.0,
        id_caja: Optional[int] = None,
        id_usuario: Optional[int] = None,
        insumos_a_descontar: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Venta, TicketVenta]:
        if not items:
            raise VentaSinItemsError()

        if id_caja is not None:
            caja = self._cash_repo.obtener_caja_por_id(id_caja)
            if caja is None or not caja.esta_abierta():
                raise CajaNoAbiertaError("La caja especificada no existe o se encuentra cerrada.")
        else:
            caja = self._cash_repo.obtener_caja_activa()
            if caja is None:
                raise CajaNoAbiertaError("No existe un turno de caja abierto para registrar la venta.")
            id_caja = caja.id_caja

        comanda = self.calcular_comanda(items)
        fecha_hora = datetime.now().isoformat(sep=" ", timespec="seconds")

        detalles: List[DetalleVenta] = []
        for it in comanda["items"]:
            detalles.append(
                DetalleVenta(
                    id_producto=it["id_producto"],
                    cantidad=it["cantidad"],
                    precio_unitario=it["precio_unitario"],
                    subtotal=it["subtotal"],
                    nombre_producto=it["nombre"],
                )
            )

        venta = Venta(
            id_caja=id_caja,
            fecha_hora=fecha_hora,
            total=comanda["total"],
            metodo_pago=metodo_pago,
            detalles=detalles,
        )
        venta.liquidar_pago(metodo_pago=metodo_pago, dinero_recibido=dinero_recibido)

        with get_db_transaction(self._db_path) as conn:
            id_venta = self._sale_repo.registrar_venta_transaccional(venta, conn=conn)
            venta.id_venta = id_venta

            if insumos_a_descontar:
                for ins in insumos_a_descontar:
                    id_insumo = int(ins["id_insumo"])
                    cant = float(ins["cantidad"])
                    self._inventory_service.descontar_stock(
                        id_insumo=id_insumo,
                        cantidad=cant,
                        conn=conn,
                    )

            self._inventory_repo.registrar_auditoria(
                id_usuario=id_usuario or caja.id_usuario,
                accion="REGISTRO_VENTA",
                modulo="VENTAS",
                detalles=(
                    f"Venta #{id_venta} registrada en Caja #{id_caja}. "
                    f"Total: ${venta.total:,.2f} | Método: {venta.metodo_pago} | "
                    f"Recibido: ${venta.dinero_recibido:,.2f} | Cambio: ${venta.cambio:,.2f}."
                ),
                conn=conn,
            )

        ticket = self.emitir_ticket(venta)
        return venta, ticket

    def emitir_ticket(self, venta: Venta) -> TicketVenta:
        if venta.id_venta is None:
            raise ValueError("No se puede emitir ticket para una venta no persistida.")

        items_ticket: List[Dict[str, Any]] = []
        for det in venta.detalles:
            nombre = det.nombre_producto
            if not nombre:
                prod = self._product_repo.obtener_producto_por_id(det.id_producto)
                nombre = prod.nombre if prod else f"Producto #{det.id_producto}"
            items_ticket.append({
                "id_producto": det.id_producto,
                "nombre": nombre,
                "cantidad": det.cantidad,
                "precio_unitario": det.precio_unitario,
                "subtotal": det.subtotal,
            })

        return TicketVenta(
            id_venta=venta.id_venta,
            id_caja=venta.id_caja,
            fecha_hora=venta.fecha_hora,
            metodo_pago=venta.metodo_pago,
            total=venta.total,
            dinero_recibido=venta.dinero_recibido,
            cambio=venta.cambio,
            items=items_ticket,
        )

    def obtener_venta(self, id_venta: int) -> Optional[Venta]:
        return self._sale_repo.obtener_venta_por_id(id_venta)

    def listar_ventas_por_caja(self, id_caja: int) -> List[Venta]:
        return self._sale_repo.listar_ventas_por_caja(id_caja)
