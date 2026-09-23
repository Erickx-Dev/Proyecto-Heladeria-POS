from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import (
    CajaNoAbiertaError,
    PagoInsuficienteError,
    ProductoNoEncontradoError,
    StockInsuficienteError,
    VentaSinItemsError,
)
from src.services.cash_service import CashService
from src.services.inventory_service import InventoryService
from src.services.product_service import ProductService
from src.services.sale_service import SaleService


class TestSaleService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_heladeria.db"
        inicializar_base_de_datos(db_path=self.db_path, forzar=True)
        self.cash_service = CashService(db_path=self.db_path)
        self.product_service = ProductService(db_path=self.db_path)
        self.inventory_service = InventoryService(db_path=self.db_path)
        self.sale_service = SaleService(db_path=self.db_path)

        self.producto_1 = self.product_service.registrar_producto(
            codigo="HEL-01",
            nombre="Cono Doble Chocolate",
            precio_venta=6000.0,
            id_categoria=1,
        )
        self.producto_2 = self.product_service.registrar_producto(
            codigo="TOPP-01",
            nombre="Lluvia de Almendras",
            precio_venta=1500.0,
            id_categoria=3,
        )

        self.insumo_cono = self.inventory_service.registrar_insumo(
            nombre="Conos de Galleta",
            unidad_medida="Unidades",
            stock_actual=50.0,
            stock_minimo=10.0,
        )
        self.insumo_helado = self.inventory_service.registrar_insumo(
            nombre="Helado Chocolate Litros",
            unidad_medida="Litros",
            stock_actual=20.0,
            stock_minimo=5.0,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_calcular_comanda_calcula_subtotales_y_totales(self) -> None:
        items = [
            {"id_producto": self.producto_1.id_producto, "cantidad": 2},
            {"id_producto": self.producto_2.id_producto, "cantidad": 3},
        ]
        comanda = self.sale_service.calcular_comanda(items)
        self.assertEqual(comanda["total"], 16500.0)
        self.assertEqual(comanda["cantidad_items"], 5)
        self.assertEqual(len(comanda["items"]), 2)
        self.assertEqual(comanda["items"][0]["subtotal"], 12000.0)
        self.assertEqual(comanda["items"][1]["subtotal"], 4500.0)

    def test_calcular_comanda_con_producto_inexistente_lanza_excepcion(self) -> None:
        items = [{"id_producto": 99999, "cantidad": 1}]
        with self.assertRaises(ProductoNoEncontradoError):
            self.sale_service.calcular_comanda(items)

    def test_calcular_comanda_vacia_lanza_excepcion(self) -> None:
        with self.assertRaises(VentaSinItemsError):
            self.sale_service.calcular_comanda([])

    def test_procesar_venta_sin_caja_abierta_lanza_excepcion(self) -> None:
        items = [{"id_producto": self.producto_1.id_producto, "cantidad": 1}]
        with self.assertRaises(CajaNoAbiertaError):
            self.sale_service.procesar_venta(
                items=items,
                metodo_pago="EFECTIVO",
                dinero_recibido=10000.0,
            )

    def test_procesar_venta_efectivo_exitosa_y_emision_ticket(self) -> None:
        caja = self.cash_service.abrir_turno(id_usuario=1, monto_inicial=50000.0)

        items = [
            {"id_producto": self.producto_1.id_producto, "cantidad": 2},
            {"id_producto": self.producto_2.id_producto, "cantidad": 1},
        ]
        insumos = [
            {"id_insumo": self.insumo_cono.id_insumo, "cantidad": 2.0},
            {"id_insumo": self.insumo_helado.id_insumo, "cantidad": 0.5},
        ]

        venta, ticket = self.sale_service.procesar_venta(
            items=items,
            metodo_pago="EFECTIVO",
            dinero_recibido=15000.0,
            id_caja=caja.id_caja,
            id_usuario=1,
            insumos_a_descontar=insumos,
        )

        self.assertIsNotNone(venta.id_venta)
        self.assertEqual(venta.total, 13500.0)
        self.assertEqual(venta.dinero_recibido, 15000.0)
        self.assertEqual(venta.cambio, 1500.0)
        self.assertEqual(len(venta.detalles), 2)

        cono_actualizado = self.inventory_service.obtener_insumo(self.insumo_cono.id_insumo)
        helado_actualizado = self.inventory_service.obtener_insumo(self.insumo_helado.id_insumo)
        self.assertEqual(cono_actualizado.stock_actual, 48.0)
        self.assertEqual(helado_actualizado.stock_actual, 19.5)

        self.assertEqual(ticket.id_venta, venta.id_venta)
        self.assertEqual(ticket.total, 13500.0)
        self.assertEqual(ticket.cambio, 1500.0)
        texto = ticket.generar_texto(ancho=40)
        self.assertIn("Cono Doble Chocolate", texto)
        self.assertIn("$13,500.00", texto)
        self.assertIn("$1,500.00", texto)

    def test_procesar_venta_transferencia_exitosa(self) -> None:
        caja = self.cash_service.abrir_turno(id_usuario=1, monto_inicial=20000.0)
        items = [{"id_producto": self.producto_1.id_producto, "cantidad": 1}]

        venta, ticket = self.sale_service.procesar_venta(
            items=items,
            metodo_pago="TRANSFERENCIA",
            id_caja=caja.id_caja,
            id_usuario=1,
        )

        self.assertEqual(venta.total, 6000.0)
        self.assertEqual(venta.dinero_recibido, 6000.0)
        self.assertEqual(venta.cambio, 0.0)
        self.assertEqual(ticket.metodo_pago, "TRANSFERENCIA")

    def test_procesar_venta_efectivo_con_pago_insuficiente_lanza_excepcion(self) -> None:
        caja = self.cash_service.abrir_turno(id_usuario=1, monto_inicial=10000.0)
        items = [{"id_producto": self.producto_1.id_producto, "cantidad": 2}]

        with self.assertRaises(PagoInsuficienteError):
            self.sale_service.procesar_venta(
                items=items,
                metodo_pago="EFECTIVO",
                dinero_recibido=10000.0,
                id_caja=caja.id_caja,
            )

    def test_rollback_atomico_si_falla_descuento_de_insumo(self) -> None:
        caja = self.cash_service.abrir_turno(id_usuario=1, monto_inicial=10000.0)
        items = [{"id_producto": self.producto_1.id_producto, "cantidad": 1}]
        insumos = [
            {"id_insumo": self.insumo_cono.id_insumo, "cantidad": 1000.0},
        ]

        with self.assertRaises(StockInsuficienteError):
            self.sale_service.procesar_venta(
                items=items,
                metodo_pago="EFECTIVO",
                dinero_recibido=10000.0,
                id_caja=caja.id_caja,
                insumos_a_descontar=insumos,
            )

        ventas_en_caja = self.sale_service.listar_ventas_por_caja(caja.id_caja)
        self.assertEqual(len(ventas_en_caja), 0)

        cono_intacto = self.inventory_service.obtener_insumo(self.insumo_cono.id_insumo)
        self.assertEqual(cono_intacto.stock_actual, 50.0)


if __name__ == "__main__":
    unittest.main()
