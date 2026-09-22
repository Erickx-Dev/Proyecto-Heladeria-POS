from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.connection import get_db_transaction
from database.migrations import inicializar_base_de_datos
from src.core.exceptions import (
    CajaNoAbiertaError,
    CajaYaAbiertaError,
    DescripcionGastoVaciaError,
    GastoExcedeSaldoDisponibleError,
    MontoInvalidoError,
)
from src.domain.cash_register import ESTADO_ABIERTA, ESTADO_CERRADA, Arqueo, TurnoCaja
from src.domain.expense import Gasto
from src.services.cash_service import CashService


class TestCashServiceApertura(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path: Path = Path(self.temp_dir.name) / "test_caja.db"
        inicializar_base_de_datos(self.db_path)
        self.servicio: CashService = CashService(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_apertura_exitosa_de_turno(self) -> None:
        turno: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=100000.0
        )
        self.assertIsNotNone(turno.id_caja)
        self.assertEqual(turno.id_usuario, 1)
        self.assertEqual(turno.monto_inicial, 100000.0)
        self.assertTrue(turno.esta_abierta())
        self.assertIsNotNone(turno.fecha_apertura)

    def test_apertura_con_monto_inicial_cero(self) -> None:
        turno: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=0.0
        )
        self.assertIsNotNone(turno.id_caja)
        self.assertEqual(turno.monto_inicial, 0.0)
        self.assertTrue(turno.esta_abierta())

    def test_apertura_con_monto_negativo_lanza_excepcion(self) -> None:
        with self.assertRaises(MontoInvalidoError):
            self.servicio.abrir_turno(id_usuario=1, monto_inicial=-50000.0)

    def test_doble_apertura_lanza_excepcion(self) -> None:
        self.servicio.abrir_turno(id_usuario=1, monto_inicial=100000.0)
        with self.assertRaises(CajaYaAbiertaError):
            self.servicio.abrir_turno(id_usuario=1, monto_inicial=50000.0)

    def test_apertura_genera_log_de_auditoria(self) -> None:
        self.servicio.abrir_turno(id_usuario=1, monto_inicial=100000.0)
        from database.connection import get_db_cursor

        with get_db_cursor(db_path=self.db_path) as cursor:
            cursor.execute(
                "SELECT accion, modulo FROM AuditoriaLog WHERE accion = 'APERTURA_CAJA'"
            )
            log = cursor.fetchone()
            self.assertIsNotNone(log)
            self.assertEqual(log["accion"], "APERTURA_CAJA")
            self.assertEqual(log["modulo"], "CAJA")


class TestCashServiceObtenerTurno(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path: Path = Path(self.temp_dir.name) / "test_caja.db"
        inicializar_base_de_datos(self.db_path)
        self.servicio: CashService = CashService(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_obtener_turno_activo_existente(self) -> None:
        turno_creado: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=100000.0
        )
        turno_activo: TurnoCaja = self.servicio.obtener_turno_activo()
        self.assertEqual(turno_activo.id_caja, turno_creado.id_caja)
        self.assertTrue(turno_activo.esta_abierta())

    def test_obtener_turno_activo_sin_caja_lanza_excepcion(self) -> None:
        with self.assertRaises(CajaNoAbiertaError):
            self.servicio.obtener_turno_activo()


class TestCashServiceGastos(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path: Path = Path(self.temp_dir.name) / "test_caja.db"
        inicializar_base_de_datos(self.db_path)
        self.servicio: CashService = CashService(db_path=self.db_path)
        self.turno: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=100000.0
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_registro_exitoso_de_gasto_menor(self) -> None:
        gasto: Gasto = self.servicio.registrar_gasto_menor(
            id_usuario=1,
            monto=5000.0,
            descripcion="Compra de bolsas de hielo de emergencia",
        )
        self.assertIsNotNone(gasto.id_gasto)
        self.assertEqual(gasto.monto, 5000.0)
        self.assertEqual(gasto.id_caja, self.turno.id_caja)

    def test_gasto_sin_turno_activo_lanza_excepcion(self) -> None:
        self.servicio.cerrar_turno(
            id_usuario=1, monto_fisico_real=100000.0
        )
        with self.assertRaises(CajaNoAbiertaError):
            self.servicio.registrar_gasto_menor(
                id_usuario=1,
                monto=5000.0,
                descripcion="Intento de gasto sin caja",
            )

    def test_gasto_con_monto_negativo_lanza_excepcion(self) -> None:
        with self.assertRaises(MontoInvalidoError):
            self.servicio.registrar_gasto_menor(
                id_usuario=1,
                monto=-1000.0,
                descripcion="Gasto negativo inválido",
            )

    def test_gasto_con_monto_cero_lanza_excepcion(self) -> None:
        with self.assertRaises(MontoInvalidoError):
            self.servicio.registrar_gasto_menor(
                id_usuario=1,
                monto=0.0,
                descripcion="Gasto con monto cero",
            )

    def test_gasto_con_descripcion_vacia_lanza_excepcion(self) -> None:
        with self.assertRaises(DescripcionGastoVaciaError):
            self.servicio.registrar_gasto_menor(
                id_usuario=1,
                monto=5000.0,
                descripcion="",
            )

    def test_gasto_que_excede_saldo_disponible_lanza_excepcion(self) -> None:
        with self.assertRaises(GastoExcedeSaldoDisponibleError):
            self.servicio.registrar_gasto_menor(
                id_usuario=1,
                monto=150000.0,
                descripcion="Gasto que excede el saldo",
            )

    def test_multiples_gastos_reducen_saldo_disponible(self) -> None:
        self.servicio.registrar_gasto_menor(
            id_usuario=1,
            monto=60000.0,
            descripcion="Primer gasto operativo",
        )
        self.servicio.registrar_gasto_menor(
            id_usuario=1,
            monto=30000.0,
            descripcion="Segundo gasto operativo",
        )
        with self.assertRaises(GastoExcedeSaldoDisponibleError):
            self.servicio.registrar_gasto_menor(
                id_usuario=1,
                monto=20000.0,
                descripcion="Tercer gasto que excede el saldo",
            )

    def test_gasto_genera_log_de_auditoria(self) -> None:
        self.servicio.registrar_gasto_menor(
            id_usuario=1,
            monto=5000.0,
            descripcion="Productos de aseo",
        )
        from database.connection import get_db_cursor

        with get_db_cursor(db_path=self.db_path) as cursor:
            cursor.execute(
                "SELECT accion FROM AuditoriaLog WHERE accion = 'GASTO_CAJA_MENOR'"
            )
            log = cursor.fetchone()
            self.assertIsNotNone(log)
            self.assertEqual(log["accion"], "GASTO_CAJA_MENOR")


class TestCashServiceCierreArqueo(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path: Path = Path(self.temp_dir.name) / "test_caja.db"
        inicializar_base_de_datos(self.db_path)
        self.servicio: CashService = CashService(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _simular_venta_efectivo(self, id_caja: int, total: float) -> None:
        from datetime import datetime

        with get_db_transaction(db_path=self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO Venta (id_caja, fecha_hora, total, metodo_pago,
                                   dinero_recibido, cambio)
                VALUES (?, ?, ?, 'EFECTIVO', ?, 0.0)
                """,
                (
                    id_caja,
                    datetime.now().isoformat(sep=" ", timespec="seconds"),
                    total,
                    total,
                ),
            )

    def test_cierre_exitoso_con_caja_cuadrada(self) -> None:
        turno: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=100000.0
        )
        turno_cerrado, arqueo = self.servicio.cerrar_turno(
            id_usuario=1, monto_fisico_real=100000.0
        )
        self.assertFalse(turno_cerrado.esta_abierta())
        self.assertEqual(turno_cerrado.estado, ESTADO_CERRADA)
        self.assertEqual(arqueo.diferencia, 0.0)
        self.assertEqual(arqueo.tipo_diferencia, "CUADRADO")

    def test_cierre_con_ventas_y_gastos_cuadrado(self) -> None:
        turno: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=100000.0
        )
        self._simular_venta_efectivo(turno.id_caja, 150000.0)
        self._simular_venta_efectivo(turno.id_caja, 100000.0)
        self.servicio.registrar_gasto_menor(
            id_usuario=1, monto=10000.0, descripcion="Hielo de emergencia"
        )
        self.servicio.registrar_gasto_menor(
            id_usuario=1, monto=5000.0, descripcion="Servilletas"
        )
        turno_cerrado, arqueo = self.servicio.cerrar_turno(
            id_usuario=1, monto_fisico_real=335000.0
        )
        self.assertEqual(arqueo.saldo_esperado, 335000.0)
        self.assertEqual(arqueo.diferencia, 0.0)
        self.assertEqual(arqueo.tipo_diferencia, "CUADRADO")

    def test_cierre_con_sobrante(self) -> None:
        turno: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=100000.0
        )
        self._simular_venta_efectivo(turno.id_caja, 50000.0)
        turno_cerrado, arqueo = self.servicio.cerrar_turno(
            id_usuario=1, monto_fisico_real=155000.0
        )
        self.assertEqual(arqueo.saldo_esperado, 150000.0)
        self.assertEqual(arqueo.diferencia, 5000.0)
        self.assertEqual(arqueo.tipo_diferencia, "SOBRANTE")

    def test_cierre_con_faltante(self) -> None:
        turno: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=100000.0
        )
        self._simular_venta_efectivo(turno.id_caja, 50000.0)
        turno_cerrado, arqueo = self.servicio.cerrar_turno(
            id_usuario=1, monto_fisico_real=145000.0
        )
        self.assertEqual(arqueo.saldo_esperado, 150000.0)
        self.assertEqual(arqueo.diferencia, -5000.0)
        self.assertEqual(arqueo.tipo_diferencia, "FALTANTE")

    def test_cierre_sin_turno_activo_lanza_excepcion(self) -> None:
        with self.assertRaises(CajaNoAbiertaError):
            self.servicio.cerrar_turno(
                id_usuario=1, monto_fisico_real=100000.0
            )

    def test_cierre_con_monto_negativo_lanza_excepcion(self) -> None:
        self.servicio.abrir_turno(id_usuario=1, monto_inicial=100000.0)
        with self.assertRaises(MontoInvalidoError):
            self.servicio.cerrar_turno(
                id_usuario=1, monto_fisico_real=-10000.0
            )

    def test_cierre_genera_log_de_auditoria(self) -> None:
        self.servicio.abrir_turno(id_usuario=1, monto_inicial=100000.0)
        self.servicio.cerrar_turno(
            id_usuario=1, monto_fisico_real=100000.0
        )
        from database.connection import get_db_cursor

        with get_db_cursor(db_path=self.db_path) as cursor:
            cursor.execute(
                "SELECT accion FROM AuditoriaLog WHERE accion = 'CIERRE_CAJA'"
            )
            log = cursor.fetchone()
            self.assertIsNotNone(log)
            self.assertEqual(log["accion"], "CIERRE_CAJA")

    def test_caja_persistida_con_datos_de_cierre(self) -> None:
        turno: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=100000.0
        )
        id_caja: int = turno.id_caja
        self.servicio.cerrar_turno(
            id_usuario=1, monto_fisico_real=100000.0
        )
        from src.repositories.cash_repository import CashRepository

        repo = CashRepository(db_path=self.db_path)
        caja_db: TurnoCaja = repo.obtener_caja_por_id(id_caja)
        self.assertIsNotNone(caja_db)
        self.assertEqual(caja_db.estado, ESTADO_CERRADA)
        self.assertIsNotNone(caja_db.fecha_cierre)
        self.assertEqual(caja_db.monto_final_real, 100000.0)
        self.assertEqual(caja_db.diferencia, 0.0)

    def test_reabrir_caja_despues_de_cierre(self) -> None:
        self.servicio.abrir_turno(id_usuario=1, monto_inicial=100000.0)
        self.servicio.cerrar_turno(
            id_usuario=1, monto_fisico_real=100000.0
        )
        turno_nuevo: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=80000.0
        )
        self.assertIsNotNone(turno_nuevo.id_caja)
        self.assertTrue(turno_nuevo.esta_abierta())
        self.assertEqual(turno_nuevo.monto_inicial, 80000.0)


class TestCashServiceCalcularArqueo(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path: Path = Path(self.temp_dir.name) / "test_caja.db"
        inicializar_base_de_datos(self.db_path)
        self.servicio: CashService = CashService(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_calcular_arqueo_sin_cerrar(self) -> None:
        turno: TurnoCaja = self.servicio.abrir_turno(
            id_usuario=1, monto_inicial=100000.0
        )
        arqueo: Arqueo = self.servicio.calcular_arqueo(
            monto_fisico_real=100000.0
        )
        self.assertEqual(arqueo.saldo_esperado, 100000.0)
        turno_activo: TurnoCaja = self.servicio.obtener_turno_activo()
        self.assertTrue(turno_activo.esta_abierta())


if __name__ == "__main__":
    unittest.main()
