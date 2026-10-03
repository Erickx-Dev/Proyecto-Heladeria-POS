from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import (
    CajaNoAbiertaError,
    CajaYaAbiertaError,
    GastoExcedeSaldoDisponibleError,
    MontoInvalidoError,
    ValidacionError,
)
from src.domain.cash_register import ESTADO_ABIERTA, ESTADO_CERRADA
from src.domain.expense import Gasto
from src.repositories.cash_repository import CashRepository
from src.repositories.expense_repository import ExpenseRepository
from src.services.cash_service import CashService
from src.services.expense_service import ExpenseService


class TestCashRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cash_repo.db"
        inicializar_base_de_datos(self.db_path)
        self.repo = CashRepository(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_abrir_caja_retorna_id_positivo(self) -> None:
        id_caja = self.repo.abrir_caja(1, 100000.0, "2026-10-02 08:00:00")
        self.assertIsInstance(id_caja, int)
        self.assertGreater(id_caja, 0)

    def test_obtener_caja_activa_existente(self) -> None:
        self.repo.abrir_caja(1, 50000.0, "2026-10-02 08:00:00")
        caja = self.repo.obtener_caja_activa()
        self.assertIsNotNone(caja)
        self.assertEqual(caja.estado, ESTADO_ABIERTA)
        self.assertEqual(caja.monto_inicial, 50000.0)

    def test_obtener_caja_activa_ninguna(self) -> None:
        caja = self.repo.obtener_caja_activa()
        self.assertIsNone(caja)

    def test_cerrar_caja_exitoso(self) -> None:
        id_caja = self.repo.abrir_caja(1, 100000.0, "2026-10-02 08:00:00")
        resultado = self.repo.cerrar_caja(id_caja, 95000.0, -5000.0, "2026-10-02 18:00:00")
        self.assertTrue(resultado)

        caja = self.repo.obtener_caja_por_id(id_caja)
        self.assertEqual(caja.estado, ESTADO_CERRADA)
        self.assertEqual(caja.monto_final_real, 95000.0)
        self.assertEqual(caja.diferencia, -5000.0)
        self.assertEqual(caja.fecha_cierre, "2026-10-02 18:00:00")

    def test_cerrar_caja_id_inexistente(self) -> None:
        resultado = self.repo.cerrar_caja(9999, 100.0, 0.0, "2026-10-02 18:00:00")
        self.assertFalse(resultado)

    def test_obtener_caja_por_id_existente(self) -> None:
        id_caja = self.repo.abrir_caja(1, 75000.0, "2026-10-02 08:00:00")
        caja = self.repo.obtener_caja_por_id(id_caja)
        self.assertIsNotNone(caja)
        self.assertEqual(caja.id_caja, id_caja)
        self.assertEqual(caja.id_usuario, 1)
        self.assertEqual(caja.monto_inicial, 75000.0)

    def test_obtener_caja_por_id_inexistente(self) -> None:
        caja = self.repo.obtener_caja_por_id(9999)
        self.assertIsNone(caja)

    def test_obtener_total_ventas_efectivo_sin_ventas(self) -> None:
        id_caja = self.repo.abrir_caja(1, 100000.0, "2026-10-02 08:00:00")
        total = self.repo.obtener_total_ventas_efectivo(id_caja)
        self.assertEqual(total, 0.0)


class TestExpenseRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_expense_repo.db"
        inicializar_base_de_datos(self.db_path)
        self.cash_repo = CashRepository(db_path=self.db_path)
        self.expense_repo = ExpenseRepository(db_path=self.db_path)
        self.id_caja = self.cash_repo.abrir_caja(1, 100000.0, "2026-10-02 08:00:00")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_registrar_gasto_retorna_id_positivo(self) -> None:
        gasto = Gasto(
            id_caja=self.id_caja,
            fecha_hora="2026-10-02 10:00:00",
            monto=5000.0,
            descripcion="Compra de servilletas",
            id_usuario=1,
        )
        id_gasto = self.expense_repo.registrar_gasto(gasto)
        self.assertIsInstance(id_gasto, int)
        self.assertGreater(id_gasto, 0)

    def test_listar_gastos_por_caja(self) -> None:
        gasto1 = Gasto(
            id_caja=self.id_caja, fecha_hora="2026-10-02 10:00:00",
            monto=3000.0, descripcion="Servilletas", id_usuario=1,
        )
        gasto2 = Gasto(
            id_caja=self.id_caja, fecha_hora="2026-10-02 11:00:00",
            monto=7000.0, descripcion="Vasos desechables", id_usuario=1,
        )
        self.expense_repo.registrar_gasto(gasto1)
        self.expense_repo.registrar_gasto(gasto2)

        gastos = self.expense_repo.listar_gastos_por_caja(self.id_caja)
        self.assertEqual(len(gastos), 2)
        self.assertEqual(gastos[0].monto, 3000.0)
        self.assertEqual(gastos[1].monto, 7000.0)

    def test_listar_gastos_caja_sin_gastos(self) -> None:
        gastos = self.expense_repo.listar_gastos_por_caja(self.id_caja)
        self.assertEqual(len(gastos), 0)

    def test_calcular_total_gastos(self) -> None:
        for monto in [5000.0, 3000.0, 2000.0]:
            gasto = Gasto(
                id_caja=self.id_caja, fecha_hora="2026-10-02 10:00:00",
                monto=monto, descripcion=f"Gasto de {monto}", id_usuario=1,
            )
            self.expense_repo.registrar_gasto(gasto)

        total = self.expense_repo.calcular_total_gastos(self.id_caja)
        self.assertEqual(total, 10000.0)

    def test_calcular_total_sin_gastos(self) -> None:
        total = self.expense_repo.calcular_total_gastos(self.id_caja)
        self.assertEqual(total, 0.0)

    def test_registrar_gasto_invalido_monto_cero(self) -> None:
        gasto = Gasto(
            id_caja=self.id_caja, fecha_hora="2026-10-02 10:00:00",
            monto=0.0, descripcion="Intento inválido", id_usuario=1,
        )
        with self.assertRaises(MontoInvalidoError):
            self.expense_repo.registrar_gasto(gasto)

    def test_registrar_gasto_invalido_descripcion_vacia(self) -> None:
        gasto = Gasto(
            id_caja=self.id_caja, fecha_hora="2026-10-02 10:00:00",
            monto=1000.0, descripcion="", id_usuario=1,
        )
        with self.assertRaises(ValidacionError):
            self.expense_repo.registrar_gasto(gasto)


class TestCashService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cash_svc.db"
        inicializar_base_de_datos(self.db_path)
        self.cash_repo = CashRepository(db_path=self.db_path)
        self.expense_repo = ExpenseRepository(db_path=self.db_path)
        self.cash_service = CashService(
            cash_repository=self.cash_repo,
            expense_repository=self.expense_repo,
            db_path=self.db_path,
        )
        self.id_usuario = 1

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_abrir_turno_exitoso(self) -> None:
        turno = self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        self.assertIsNotNone(turno)
        self.assertEqual(turno.estado, ESTADO_ABIERTA)
        self.assertEqual(turno.monto_inicial, 100000.0)
        self.assertEqual(turno.id_usuario, self.id_usuario)

    def test_abrir_turno_con_monto_cero(self) -> None:
        turno = self.cash_service.abrir_turno(self.id_usuario, 0.0)
        self.assertIsNotNone(turno)
        self.assertEqual(turno.monto_inicial, 0.0)

    def test_abrir_turno_doble_lanza_error(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        with self.assertRaises(CajaYaAbiertaError):
            self.cash_service.abrir_turno(self.id_usuario, 50000.0)

    def test_abrir_turno_monto_negativo(self) -> None:
        with self.assertRaises(MontoInvalidoError):
            self.cash_service.abrir_turno(self.id_usuario, -1.0)

    def test_obtener_turno_activo_existente(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        turno = self.cash_service.obtener_turno_activo()
        self.assertIsNotNone(turno)
        self.assertTrue(turno.esta_abierta())

    def test_obtener_turno_sin_caja_lanza_error(self) -> None:
        with self.assertRaises(CajaNoAbiertaError):
            self.cash_service.obtener_turno_activo()

    def test_cerrar_turno_cuadre_exacto(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        arqueo = self.cash_service.cerrar_turno(self.id_usuario, 100000.0)
        self.assertEqual(arqueo.saldo_esperado, 100000.0)
        self.assertEqual(arqueo.diferencia, 0.0)
        self.assertEqual(arqueo.tipo_diferencia, "CUADRADO")

    def test_cerrar_turno_sobrante(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        arqueo = self.cash_service.cerrar_turno(self.id_usuario, 105000.0)
        self.assertEqual(arqueo.diferencia, 5000.0)
        self.assertEqual(arqueo.tipo_diferencia, "SOBRANTE")

    def test_cerrar_turno_faltante(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        arqueo = self.cash_service.cerrar_turno(self.id_usuario, 98000.0)
        self.assertEqual(arqueo.diferencia, -2000.0)
        self.assertEqual(arqueo.tipo_diferencia, "FALTANTE")

    def test_cerrar_turno_con_gastos(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        turno = self.cash_service.obtener_turno_activo()

        gasto = Gasto(
            id_caja=turno.id_caja, fecha_hora="2026-10-02 10:00:00",
            monto=15000.0, descripcion="Compra de insumos urgentes", id_usuario=1,
        )
        self.expense_repo.registrar_gasto(gasto)

        arqueo = self.cash_service.cerrar_turno(self.id_usuario, 85000.0)
        self.assertEqual(arqueo.saldo_esperado, 85000.0)
        self.assertEqual(arqueo.total_gastos, 15000.0)
        self.assertEqual(arqueo.diferencia, 0.0)
        self.assertEqual(arqueo.tipo_diferencia, "CUADRADO")

    def test_cerrar_turno_sin_caja_lanza_error(self) -> None:
        with self.assertRaises(CajaNoAbiertaError):
            self.cash_service.cerrar_turno(self.id_usuario, 100000.0)

    def test_cerrar_turno_monto_negativo(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        with self.assertRaises(MontoInvalidoError):
            self.cash_service.cerrar_turno(self.id_usuario, -1.0)

    def test_saldo_disponible_sin_movimientos(self) -> None:
        turno = self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        saldo = self.cash_service.obtener_saldo_disponible(turno.id_caja)
        self.assertEqual(saldo, 100000.0)

    def test_saldo_disponible_con_gastos(self) -> None:
        turno = self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        gasto = Gasto(
            id_caja=turno.id_caja, fecha_hora="2026-10-02 10:00:00",
            monto=20000.0, descripcion="Compra de materiales", id_usuario=1,
        )
        self.expense_repo.registrar_gasto(gasto)
        saldo = self.cash_service.obtener_saldo_disponible(turno.id_caja)
        self.assertEqual(saldo, 80000.0)

    def test_abrir_nuevo_turno_despues_de_cerrar(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        self.cash_service.cerrar_turno(self.id_usuario, 100000.0)

        turno2 = self.cash_service.abrir_turno(self.id_usuario, 80000.0)
        self.assertIsNotNone(turno2)
        self.assertEqual(turno2.monto_inicial, 80000.0)


class TestExpenseService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_expense_svc.db"
        inicializar_base_de_datos(self.db_path)
        self.cash_repo = CashRepository(db_path=self.db_path)
        self.expense_repo = ExpenseRepository(db_path=self.db_path)
        self.cash_service = CashService(
            cash_repository=self.cash_repo,
            expense_repository=self.expense_repo,
            db_path=self.db_path,
        )
        self.expense_service = ExpenseService(
            expense_repository=self.expense_repo,
            cash_service=self.cash_service,
            db_path=self.db_path,
        )
        self.id_usuario = 1

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_registrar_gasto_exitoso(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        gasto = self.expense_service.registrar_gasto(
            self.id_usuario, 5000.0, "Compra de servilletas",
        )
        self.assertIsNotNone(gasto)
        self.assertIsNotNone(gasto.id_gasto)
        self.assertEqual(gasto.monto, 5000.0)
        self.assertEqual(gasto.descripcion, "Compra de servilletas")

    def test_gasto_sin_caja_abierta(self) -> None:
        with self.assertRaises(CajaNoAbiertaError):
            self.expense_service.registrar_gasto(
                self.id_usuario, 5000.0, "Intento sin caja",
            )

    def test_gasto_monto_negativo(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        with self.assertRaises(MontoInvalidoError):
            self.expense_service.registrar_gasto(
                self.id_usuario, -100.0, "Monto negativo",
            )

    def test_gasto_monto_cero(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        with self.assertRaises(MontoInvalidoError):
            self.expense_service.registrar_gasto(
                self.id_usuario, 0.0, "Monto cero",
            )

    def test_gasto_descripcion_vacia(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        with self.assertRaises(ValidacionError):
            self.expense_service.registrar_gasto(
                self.id_usuario, 5000.0, "",
            )

    def test_gasto_descripcion_solo_espacios(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        with self.assertRaises(ValidacionError):
            self.expense_service.registrar_gasto(
                self.id_usuario, 5000.0, "   ",
            )

    def test_gasto_excede_saldo_disponible(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 10000.0)
        with self.assertRaises(GastoExcedeSaldoDisponibleError) as ctx:
            self.expense_service.registrar_gasto(
                self.id_usuario, 15000.0, "Gasto excesivo",
            )
        self.assertEqual(ctx.exception.monto_solicitado, 15000.0)
        self.assertEqual(ctx.exception.saldo_disponible, 10000.0)

    def test_gastos_multiples_reducen_saldo(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 50000.0)

        self.expense_service.registrar_gasto(self.id_usuario, 20000.0, "Primer gasto")
        self.expense_service.registrar_gasto(self.id_usuario, 15000.0, "Segundo gasto")

        saldo = self.cash_service.obtener_saldo_disponible(
            self.cash_service.obtener_turno_activo().id_caja,
        )
        self.assertEqual(saldo, 15000.0)

        with self.assertRaises(GastoExcedeSaldoDisponibleError):
            self.expense_service.registrar_gasto(
                self.id_usuario, 20000.0, "Excede remanente",
            )

    def test_listar_gastos_turno_activo(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        self.expense_service.registrar_gasto(self.id_usuario, 3000.0, "Gasto A")
        self.expense_service.registrar_gasto(self.id_usuario, 7000.0, "Gasto B")

        gastos = self.expense_service.listar_gastos_turno_activo()
        self.assertEqual(len(gastos), 2)

    def test_total_gastos_turno_activo(self) -> None:
        self.cash_service.abrir_turno(self.id_usuario, 100000.0)
        self.expense_service.registrar_gasto(self.id_usuario, 3000.0, "Gasto A")
        self.expense_service.registrar_gasto(self.id_usuario, 7000.0, "Gasto B")

        total = self.expense_service.obtener_total_gastos_turno_activo()
        self.assertEqual(total, 10000.0)


class TestFlujoTurnoCompleto(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_flujo.db"
        inicializar_base_de_datos(self.db_path)
        self.cash_repo = CashRepository(db_path=self.db_path)
        self.expense_repo = ExpenseRepository(db_path=self.db_path)
        self.cash_service = CashService(
            cash_repository=self.cash_repo,
            expense_repository=self.expense_repo,
            db_path=self.db_path,
        )
        self.expense_service = ExpenseService(
            expense_repository=self.expense_repo,
            cash_service=self.cash_service,
            db_path=self.db_path,
        )
        self.id_usuario = 1

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_flujo_turno_completo_con_gastos_y_arqueo(self) -> None:
        monto_inicial = 200000.0
        turno = self.cash_service.abrir_turno(self.id_usuario, monto_inicial)
        self.assertEqual(turno.estado, ESTADO_ABIERTA)
        self.assertEqual(turno.monto_inicial, monto_inicial)

        gastos_registrados = [
            ("Compra de conos y barquillos", 25000.0),
            ("Pago de servicio de agua", 15000.0),
            ("Servilletas y cucharas plásticas", 8000.0),
            ("Taxi para entrega de pedido", 12000.0),
        ]
        total_gastos_esperado = 0.0
        for descripcion, monto in gastos_registrados:
            gasto = self.expense_service.registrar_gasto(
                self.id_usuario, monto, descripcion,
            )
            self.assertIsNotNone(gasto.id_gasto)
            total_gastos_esperado += monto

        total_real = self.expense_service.obtener_total_gastos_turno_activo()
        self.assertEqual(total_real, total_gastos_esperado)
        self.assertEqual(total_real, 60000.0)

        saldo = self.cash_service.obtener_saldo_disponible(turno.id_caja)
        saldo_esperado = monto_inicial - total_gastos_esperado
        self.assertEqual(saldo, saldo_esperado)

        arqueo = self.cash_service.cerrar_turno(self.id_usuario, 140000.0)

        self.assertEqual(arqueo.monto_inicial, 200000.0)
        self.assertEqual(arqueo.total_ventas_efectivo, 0.0)
        self.assertEqual(arqueo.total_gastos, 60000.0)
        self.assertEqual(arqueo.saldo_esperado, 140000.0)
        self.assertEqual(arqueo.monto_fisico_real, 140000.0)
        self.assertEqual(arqueo.diferencia, 0.0)
        self.assertEqual(arqueo.tipo_diferencia, "CUADRADO")

        with self.assertRaises(CajaNoAbiertaError):
            self.cash_service.obtener_turno_activo()

        caja_cerrada = self.cash_repo.obtener_caja_por_id(turno.id_caja)
        self.assertEqual(caja_cerrada.estado, ESTADO_CERRADA)
        self.assertEqual(caja_cerrada.monto_final_real, 140000.0)
        self.assertEqual(caja_cerrada.diferencia, 0.0)
        self.assertIsNotNone(caja_cerrada.fecha_cierre)

        gastos_persistidos = self.expense_repo.listar_gastos_por_caja(turno.id_caja)
        self.assertEqual(len(gastos_persistidos), 4)

        resumen = arqueo.obtener_resumen()
        self.assertEqual(resumen["monto_inicial"], 200000.0)
        self.assertEqual(resumen["total_ventas_efectivo"], 0.0)
        self.assertEqual(resumen["total_gastos"], 60000.0)
        self.assertEqual(resumen["saldo_esperado"], 140000.0)
        self.assertEqual(resumen["monto_fisico_real"], 140000.0)
        self.assertEqual(resumen["diferencia"], 0.0)
        self.assertEqual(resumen["tipo_diferencia"], "CUADRADO")


if __name__ == "__main__":
    unittest.main()
