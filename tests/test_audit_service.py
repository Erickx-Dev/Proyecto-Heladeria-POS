from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.domain.audit import (
    ACCION_CAJA_APERTURA,
    ACCION_CAJA_CIERRE,
    ACCION_GASTO_REGISTRADO,
    ACCION_MERMA_REGISTRADA,
    ACCION_PRECIO_MODIFICADO,
    ACCION_VENTA_ANULADA,
    MODULO_CAJA,
    MODULO_CATALOGO,
    MODULO_GASTOS,
    MODULO_INVENTARIO,
    MODULO_VENTAS,
)
from src.services.audit_service import AuditService


class TestAuditService(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_rf14.db"
        inicializar_base_de_datos(self.db_path)
        self.audit_service = AuditService(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_registrar_evento_basico(self) -> None:
        log = self.audit_service.registrar_evento(
            accion="TEST_ACCION",
            modulo="TEST_MODULO",
            id_usuario=1,
            detalles="Detalle plano de prueba",
        )
        self.assertIsNotNone(log.id_log)
        self.assertEqual(log.accion, "TEST_ACCION")
        self.assertEqual(log.modulo, "TEST_MODULO")
        self.assertEqual(log.id_usuario, 1)

        recuperado = self.audit_service.obtener_log_por_id(log.id_log)
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.detalles, "Detalle plano de prueba")

    def test_registrar_cambio_estado_estructurado_previo_posterior(self) -> None:
        previo = {"estado": "ACTIVO", "nivel": 1}
        posterior = {"estado": "SUSPENDIDO", "nivel": 0}
        log = self.audit_service.registrar_cambio_estado(
            accion="CAMBIO_ESTADO",
            modulo="SEGURIDAD",
            id_usuario=1,
            estado_anterior=previo,
            estado_nuevo=posterior,
            motivo="Incumplimiento de politicas",
        )
        detalles = log.obtener_detalles_dict()
        self.assertIsNotNone(detalles)
        self.assertEqual(detalles["previo"]["estado"], "ACTIVO")
        self.assertEqual(detalles["posterior"]["estado"], "SUSPENDIDO")
        self.assertEqual(detalles["motivo"], "Incumplimiento de politicas")

    def test_registrar_anulacion_venta(self) -> None:
        log = self.audit_service.registrar_anulacion_venta(
            id_venta=105,
            total=45000.0,
            motivo="Error de digitacion del cajero",
            id_usuario=1,
        )
        self.assertEqual(log.accion, ACCION_VENTA_ANULADA)
        self.assertEqual(log.modulo, MODULO_VENTAS)

        detalles = log.obtener_detalles_dict()
        self.assertEqual(detalles["previo"]["id_venta"], 105)
        self.assertEqual(detalles["previo"]["estado"], "COMPLETADA")
        self.assertEqual(detalles["posterior"]["estado"], "ANULADA")
        self.assertEqual(detalles["motivo"], "Error de digitacion del cajero")

    def test_registrar_apertura_y_cierre_caja(self) -> None:
        log_apertura = self.audit_service.registrar_apertura_caja(
            id_caja=1,
            monto_inicial=50000.0,
            id_usuario=1,
        )
        self.assertEqual(log_apertura.accion, ACCION_CAJA_APERTURA)
        self.assertEqual(log_apertura.modulo, MODULO_CAJA)
        detalles_apertura = log_apertura.obtener_detalles_dict()
        self.assertEqual(detalles_apertura["posterior"]["monto_inicial"], 50000.0)

        log_cierre = self.audit_service.registrar_cierre_caja(
            id_caja=1,
            monto_esperado=150000.0,
            monto_real=148000.0,
            diferencia=-2000.0,
            id_usuario=1,
        )
        self.assertEqual(log_cierre.accion, ACCION_CAJA_CIERRE)
        detalles_cierre = log_cierre.obtener_detalles_dict()
        self.assertEqual(detalles_cierre["posterior"]["diferencia"], -2000.0)
        self.assertEqual(detalles_cierre["posterior"]["estado"], "CERRADA")

    def test_registrar_gasto_operativo(self) -> None:
        log = self.audit_service.registrar_gasto(
            id_gasto=12,
            monto=15000.0,
            descripcion="Compra de servilletas de emergencia",
            id_usuario=1,
        )
        self.assertEqual(log.accion, ACCION_GASTO_REGISTRADO)
        self.assertEqual(log.modulo, MODULO_GASTOS)

        detalles = log.obtener_detalles_dict()
        self.assertEqual(detalles["monto"], 15000.0)
        self.assertEqual(detalles["descripcion"], "Compra de servilletas de emergencia")

    def test_registrar_merma_inventario(self) -> None:
        log = self.audit_service.registrar_merma(
            id_merma=3,
            id_insumo=5,
            cantidad=2.5,
            motivo="Fallo en refrigeracion nocturna",
            id_usuario=1,
        )
        self.assertEqual(log.accion, ACCION_MERMA_REGISTRADA)
        self.assertEqual(log.modulo, MODULO_INVENTARIO)

        detalles = log.obtener_detalles_dict()
        self.assertEqual(detalles["id_insumo"], 5)
        self.assertEqual(detalles["cantidad"], 2.5)
        self.assertEqual(detalles["motivo"], "Fallo en refrigeracion nocturna")

    def test_registrar_modificacion_precio(self) -> None:
        log = self.audit_service.registrar_modificacion_precio(
            id_producto=20,
            precio_anterior=8000.0,
            precio_nuevo=9500.0,
            id_usuario=1,
            motivo="Ajuste inflacionario de temporada",
        )
        self.assertEqual(log.accion, ACCION_PRECIO_MODIFICADO)
        self.assertEqual(log.modulo, MODULO_CATALOGO)

        detalles = log.obtener_detalles_dict()
        self.assertEqual(detalles["previo"]["precio"], 8000.0)
        self.assertEqual(detalles["posterior"]["precio"], 9500.0)
        self.assertEqual(detalles["motivo"], "Ajuste inflacionario de temporada")

    def test_filtros_de_bitacora(self) -> None:
        self.audit_service.registrar_anulacion_venta(1, 1000.0, "Motivo 1", 1)
        self.audit_service.registrar_gasto(1, 500.0, "Gasto 1", 1)
        self.audit_service.registrar_merma(1, 1, 1.0, "Merma 1", 1)

        logs_ventas = self.audit_service.obtener_logs(modulo=MODULO_VENTAS)
        self.assertEqual(len(logs_ventas), 1)
        self.assertEqual(logs_ventas[0].modulo, MODULO_VENTAS)

        logs_gastos = self.audit_service.obtener_logs(modulo=MODULO_GASTOS)
        self.assertEqual(len(logs_gastos), 1)

        total_contado = self.audit_service.contar_logs()
        self.assertEqual(total_contado, 3)

    def test_inalterabilidad_de_bitacora(self) -> None:
        repo = self.audit_service.repository
        self.assertFalse(hasattr(repo, "actualizar"))
        self.assertFalse(hasattr(repo, "eliminar"))
        self.assertFalse(hasattr(repo, "borrar"))
        self.assertFalse(hasattr(self.audit_service, "eliminar_log"))
        self.assertFalse(hasattr(self.audit_service, "actualizar_log"))


if __name__ == "__main__":
    unittest.main()
