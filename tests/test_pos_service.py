from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.connection import get_connection
from database.migrations import inicializar_base_de_datos
from src.core.exceptions import (
    CajaNoAbiertaError,
    PagoInsuficienteError,
    StockInsuficienteError,
    ValidacionError,
)
from src.domain.audit import AuditoriaLog
from src.domain.product import Producto
from src.domain.sale import DetalleVenta, Venta
from src.domain.supply import Insumo
from src.repositories.audit_repository import AuditRepository
from src.repositories.cash_repository import CashRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.recipe_repository import RecipeRepository
from src.repositories.sale_repository import SaleRepository
from src.repositories.supply_repository import SupplyRepository
from src.services.cash_service import CashService
from src.services.pos_service import ItemVenta, POSService


class BaseOla5(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_pos.db"
        inicializar_base_de_datos(self.db_path)

        self.product_repo = ProductRepository(db_path=self.db_path)
        self.supply_repo = SupplyRepository(db_path=self.db_path)
        self.recipe_repo = RecipeRepository(db_path=self.db_path)
        self.cash_repo = CashRepository(db_path=self.db_path)
        self.sale_repo = SaleRepository(db_path=self.db_path)
        self.audit_repo = AuditRepository(db_path=self.db_path)
        self.pos = POSService(db_path=self.db_path)

        self.id_leche = self.supply_repo.crear_insumo(Insumo(nombre="Leche", unidad_medida="L", stock_actual=10.0, stock_minimo=1.0))
        self.id_fresa = self.supply_repo.crear_insumo(Insumo(nombre="Fresa", unidad_medida="kg", stock_actual=5.0, stock_minimo=1.0))

        self.id_helado = self.product_repo.crear_producto(
            Producto(codigo="HEL-01", nombre="Helado Fresa", precio_venta=5000.0, id_categoria=1)
        )
        self.id_malteada = self.product_repo.crear_producto(
            Producto(codigo="MAL-01", nombre="Malteada", precio_venta=8000.0, id_categoria=2)
        )
        self.id_topping = self.product_repo.crear_producto(
            Producto(codigo="TOP-01", nombre="Topping Chocolate", precio_venta=1500.0, id_categoria=3)
        )

        self.recipe_repo.asociar_insumo_a_producto(self.id_helado, self.id_leche, 0.5)
        self.recipe_repo.asociar_insumo_a_producto(self.id_helado, self.id_fresa, 0.2)
        self.recipe_repo.asociar_insumo_a_producto(self.id_malteada, self.id_leche, 1.0)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def abrir_caja(self) -> int:
        return self.cash_repo.abrir_caja(1, 50000.0, "2026-10-05 08:00:00")

    def stock(self, id_insumo: int) -> float:
        return self.supply_repo.obtener_por_id(id_insumo).stock_actual

    def contar(self, tabla: str) -> int:
        conn = get_connection(self.db_path)
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {tabla};").fetchone()[0]
        finally:
            conn.close()


class TestAuditRepository(BaseOla5):

    def test_registrar_y_obtener_log(self) -> None:
        id_log = self.audit_repo.registrar_log(
            AuditoriaLog(id_usuario=1, accion="PRUEBA", modulo="TEST", fecha_hora="2026-10-05 09:00:00", detalles="x")
        )
        log = self.audit_repo.obtener_por_id(id_log)
        self.assertEqual(log.accion, "PRUEBA")
        self.assertEqual(log.modulo, "TEST")

    def test_log_invalido_rechazado(self) -> None:
        with self.assertRaises(ValidacionError):
            self.audit_repo.registrar_log(AuditoriaLog(accion="", modulo="TEST", fecha_hora="2026-10-05 09:00:00"))

    def test_obtener_inexistente(self) -> None:
        self.assertIsNone(self.audit_repo.obtener_por_id(9999))

    def test_filtros_fecha_usuario_modulo(self) -> None:
        self.audit_repo.registrar_log(AuditoriaLog(id_usuario=1, accion="A", modulo="CAJA", fecha_hora="2026-10-01 10:00:00"))
        self.audit_repo.registrar_log(AuditoriaLog(id_usuario=1, accion="B", modulo="POS", fecha_hora="2026-10-03 10:00:00"))
        self.audit_repo.registrar_log(AuditoriaLog(id_usuario=None, accion="C", modulo="POS", fecha_hora="2026-10-05 10:00:00"))

        self.assertEqual(len(self.audit_repo.listar_logs()), 3)
        self.assertEqual(len(self.audit_repo.listar_logs(fecha_desde="2026-10-02 00:00:00")), 2)
        self.assertEqual(len(self.audit_repo.listar_logs(fecha_hasta="2026-10-03")), 2)
        self.assertEqual(len(self.audit_repo.listar_logs(id_usuario=1)), 2)
        self.assertEqual(len(self.audit_repo.listar_logs(modulo="POS")), 2)
        self.assertEqual(len(self.audit_repo.listar_logs(modulo="POS", id_usuario=1)), 1)


class TestSaleRepository(BaseOla5):

    def _venta(self, id_caja: int, cantidad: int = 1, metodo: str = "TRANSFERENCIA") -> Venta:
        venta = Venta(id_caja=id_caja, fecha_hora="2026-10-05 10:00:00", metodo_pago=metodo)
        venta.agregar_detalle(DetalleVenta(id_producto=self.id_helado, cantidad=cantidad, precio_unitario=5000.0))
        venta.calcular_cambio()
        return venta

    def test_registrar_venta_persiste_y_descuenta_stock(self) -> None:
        id_caja = self.abrir_caja()
        id_venta = self.sale_repo.registrar_venta(self._venta(id_caja, cantidad=2), 1)

        venta = self.sale_repo.obtener_venta_por_id(id_venta)
        self.assertEqual(venta.total, 10000.0)
        self.assertEqual(len(venta.detalles), 1)
        self.assertEqual(self.stock(self.id_leche), 9.0)
        self.assertEqual(self.stock(self.id_fresa), 4.6)

    def test_registrar_venta_genera_auditoria(self) -> None:
        id_caja = self.abrir_caja()
        self.sale_repo.registrar_venta(self._venta(id_caja), 1)
        logs = self.audit_repo.listar_logs(modulo="POS")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].accion, "VENTA_REGISTRADA")
        self.assertEqual(logs[0].id_usuario, 1)

    def test_rollback_total_ante_stock_insuficiente(self) -> None:
        id_caja = self.abrir_caja()
        venta = Venta(id_caja=id_caja, fecha_hora="2026-10-05 10:00:00", metodo_pago="TRANSFERENCIA")
        venta.agregar_detalle(DetalleVenta(id_producto=self.id_helado, cantidad=2, precio_unitario=5000.0))
        venta.agregar_detalle(DetalleVenta(id_producto=self.id_malteada, cantidad=20, precio_unitario=8000.0))
        venta.calcular_cambio()

        with self.assertRaises(StockInsuficienteError):
            self.sale_repo.registrar_venta(venta, 1)

        self.assertEqual(self.contar("Venta"), 0)
        self.assertEqual(self.contar("DetalleVenta"), 0)
        self.assertEqual(self.contar("AuditoriaLog"), 0)
        self.assertEqual(self.stock(self.id_leche), 10.0)
        self.assertEqual(self.stock(self.id_fresa), 5.0)

    def test_venta_sin_detalles_rechazada(self) -> None:
        id_caja = self.abrir_caja()
        venta = Venta(id_caja=id_caja, fecha_hora="2026-10-05 10:00:00", metodo_pago="TRANSFERENCIA")
        with self.assertRaises(ValidacionError):
            self.sale_repo.registrar_venta(venta, 1)

    def test_producto_sin_receta_no_descuenta(self) -> None:
        id_caja = self.abrir_caja()
        venta = Venta(id_caja=id_caja, fecha_hora="2026-10-05 10:00:00", metodo_pago="TRANSFERENCIA")
        venta.agregar_detalle(DetalleVenta(id_producto=self.id_topping, cantidad=3, precio_unitario=1500.0))
        venta.calcular_cambio()
        self.sale_repo.registrar_venta(venta, 1)
        self.assertEqual(self.stock(self.id_leche), 10.0)

    def test_obtener_venta_inexistente(self) -> None:
        self.assertIsNone(self.sale_repo.obtener_venta_por_id(9999))

    def test_listar_ventas_por_caja(self) -> None:
        id_caja = self.abrir_caja()
        self.sale_repo.registrar_venta(self._venta(id_caja), 1)
        self.sale_repo.registrar_venta(self._venta(id_caja), 1)
        self.assertEqual(len(self.sale_repo.listar_ventas_por_caja(id_caja)), 2)


class TestPOSService(BaseOla5):

    def test_bloquea_venta_sin_caja_abierta(self) -> None:
        with self.assertRaises(CajaNoAbiertaError):
            self.pos.registrar_venta(1, [ItemVenta(self.id_helado, 1)], "TRANSFERENCIA")

    def test_comanda_vacia(self) -> None:
        self.abrir_caja()
        with self.assertRaises(ValidacionError):
            self.pos.registrar_venta(1, [], "EFECTIVO", 1000.0)

    def test_venta_efectivo_calcula_cambio(self) -> None:
        self.abrir_caja()
        venta = self.pos.registrar_venta(
            1,
            [ItemVenta(self.id_helado, 2), ItemVenta(self.id_topping, 1)],
            "EFECTIVO",
            dinero_recibido=20000.0,
        )
        self.assertEqual(venta.total, 11500.0)
        self.assertEqual(venta.cambio, 8500.0)
        self.assertIsNotNone(venta.id_venta)
        guardada = self.pos.obtener_venta(venta.id_venta)
        self.assertEqual(len(guardada.detalles), 2)
        self.assertEqual(guardada.cambio, 8500.0)

    def test_efectivo_exacto_cambio_cero(self) -> None:
        self.abrir_caja()
        venta = self.pos.registrar_venta(1, [ItemVenta(self.id_helado, 1)], "EFECTIVO", 5000.0)
        self.assertEqual(venta.cambio, 0.0)

    def test_efectivo_insuficiente(self) -> None:
        self.abrir_caja()
        with self.assertRaises(PagoInsuficienteError):
            self.pos.registrar_venta(1, [ItemVenta(self.id_helado, 1)], "EFECTIVO", 4000.0)
        self.assertEqual(self.contar("Venta"), 0)
        self.assertEqual(self.stock(self.id_leche), 10.0)

    def test_efectivo_sin_dinero_recibido(self) -> None:
        self.abrir_caja()
        with self.assertRaises(ValidacionError):
            self.pos.registrar_venta(1, [ItemVenta(self.id_helado, 1)], "EFECTIVO")

    def test_transferencia_recibido_igual_total_sin_cambio(self) -> None:
        self.abrir_caja()
        venta = self.pos.registrar_venta(1, [ItemVenta(self.id_malteada, 1)], "transferencia")
        self.assertEqual(venta.metodo_pago, "TRANSFERENCIA")
        self.assertEqual(venta.dinero_recibido, venta.total)
        self.assertEqual(venta.cambio, 0.0)

    def test_metodo_pago_invalido(self) -> None:
        self.abrir_caja()
        with self.assertRaises(ValidacionError):
            self.pos.registrar_venta(1, [ItemVenta(self.id_helado, 1)], "BITCOIN")

    def test_producto_inexistente(self) -> None:
        self.abrir_caja()
        with self.assertRaises(ValidacionError):
            self.pos.registrar_venta(1, [ItemVenta(9999, 1)], "TRANSFERENCIA")

    def test_producto_suspendido(self) -> None:
        self.abrir_caja()
        self.product_repo.cambiar_estado(self.id_helado, 0)
        with self.assertRaises(ValidacionError):
            self.pos.registrar_venta(1, [ItemVenta(self.id_helado, 1)], "TRANSFERENCIA")

    def test_cantidad_invalida(self) -> None:
        self.abrir_caja()
        with self.assertRaises(ValidacionError):
            self.pos.registrar_venta(1, [ItemVenta(self.id_helado, 0)], "TRANSFERENCIA")

    def test_stock_insuficiente_preventivo_no_modifica_nada(self) -> None:
        self.abrir_caja()
        with self.assertRaises(StockInsuficienteError):
            self.pos.registrar_venta(1, [ItemVenta(self.id_malteada, 11)], "TRANSFERENCIA")
        self.assertEqual(self.contar("Venta"), 0)
        self.assertEqual(self.stock(self.id_leche), 10.0)

    def test_stock_insuficiente_agregado_entre_lineas(self) -> None:
        self.abrir_caja()
        # Helado 0.5 L x 12 = 6 L + Malteada 1 L x 5 = 5 L -> 11 L > 10 L
        with self.assertRaises(StockInsuficienteError):
            self.pos.registrar_venta(
                1,
                [ItemVenta(self.id_helado, 12), ItemVenta(self.id_malteada, 5)],
                "TRANSFERENCIA",
            )
        self.assertEqual(self.stock(self.id_leche), 10.0)

    def test_venta_multilinea_descuenta_insumos_compartidos(self) -> None:
        self.abrir_caja()
        self.pos.registrar_venta(
            1,
            [ItemVenta(self.id_helado, 2), ItemVenta(self.id_malteada, 3)],
            "TRANSFERENCIA",
        )
        self.assertEqual(self.stock(self.id_leche), 6.0)
        self.assertEqual(self.stock(self.id_fresa), 4.6)

    def test_calcular_total(self) -> None:
        self.assertEqual(self.pos.calcular_total([ItemVenta(self.id_helado, 2), ItemVenta(self.id_topping, 2)]), 13000.0)

    def test_venta_efectivo_se_refleja_en_arqueo(self) -> None:
        self.abrir_caja()
        self.pos.registrar_venta(1, [ItemVenta(self.id_helado, 2)], "EFECTIVO", 10000.0)
        self.pos.registrar_venta(1, [ItemVenta(self.id_helado, 1)], "TRANSFERENCIA")
        arqueo = CashService(db_path=self.db_path).cerrar_turno(1, 60000.0)
        self.assertEqual(arqueo.total_ventas_efectivo, 10000.0)
        self.assertEqual(arqueo.diferencia, 0.0)

    def test_obtener_venta_inexistente(self) -> None:
        with self.assertRaises(ValidacionError):
            self.pos.obtener_venta(9999)


if __name__ == "__main__":
    unittest.main()
