from __future__ import annotations

import unittest

from src.core.exceptions import DescripcionGastoVaciaError, MontoInvalidoError
from src.domain.cash_register import (
    ESTADO_ABIERTA,
    ESTADO_CERRADA,
    Arqueo,
    TurnoCaja,
)
from src.domain.expense import Gasto


class TestTurnoCaja(unittest.TestCase):

    def test_turno_nuevo_esta_abierto_por_defecto(self) -> None:
        turno: TurnoCaja = TurnoCaja(
            id_usuario=1,
            fecha_apertura="2026-09-22 08:00:00",
            monto_inicial=100000.0,
        )
        self.assertTrue(turno.esta_abierta())
        self.assertEqual(turno.estado, ESTADO_ABIERTA)

    def test_turno_cerrado_no_esta_abierto(self) -> None:
        turno: TurnoCaja = TurnoCaja(
            id_usuario=1,
            fecha_apertura="2026-09-22 08:00:00",
            monto_inicial=100000.0,
            estado=ESTADO_CERRADA,
        )
        self.assertFalse(turno.esta_abierta())

    def test_cerrar_turno_modifica_estado_a_cerrada(self) -> None:
        turno: TurnoCaja = TurnoCaja(
            id_usuario=1,
            fecha_apertura="2026-09-22 08:00:00",
            monto_inicial=100000.0,
        )
        turno.cerrar(
            monto_final_real=105000.0,
            diferencia=5000.0,
            fecha_cierre="2026-09-22 18:00:00",
        )
        self.assertFalse(turno.esta_abierta())
        self.assertEqual(turno.estado, ESTADO_CERRADA)
        self.assertEqual(turno.monto_final_real, 105000.0)
        self.assertEqual(turno.diferencia, 5000.0)
        self.assertEqual(turno.fecha_cierre, "2026-09-22 18:00:00")

    def test_cerrar_turno_genera_fecha_automatica_si_no_se_proporciona(self) -> None:
        turno: TurnoCaja = TurnoCaja(
            id_usuario=1,
            fecha_apertura="2026-09-22 08:00:00",
            monto_inicial=100000.0,
        )
        turno.cerrar(monto_final_real=100000.0, diferencia=0.0)
        self.assertIsNotNone(turno.fecha_cierre)
        self.assertNotEqual(turno.fecha_cierre, "")

    def test_turno_nuevo_tiene_campos_cierre_none(self) -> None:
        turno: TurnoCaja = TurnoCaja(
            id_usuario=1,
            fecha_apertura="2026-09-22 08:00:00",
            monto_inicial=50000.0,
        )
        self.assertIsNone(turno.fecha_cierre)
        self.assertIsNone(turno.monto_final_real)
        self.assertIsNone(turno.diferencia)


class TestArqueo(unittest.TestCase):

    def test_arqueo_caja_cuadrada(self) -> None:
        arqueo: Arqueo = Arqueo(
            monto_inicial=100000.0,
            total_ventas_efectivo=250000.0,
            total_gastos=15000.0,
            monto_fisico_real=335000.0,
        )
        self.assertEqual(arqueo.saldo_esperado, 335000.0)
        self.assertEqual(arqueo.diferencia, 0.0)
        self.assertEqual(arqueo.tipo_diferencia, "CUADRADO")

    def test_arqueo_con_sobrante(self) -> None:
        arqueo: Arqueo = Arqueo(
            monto_inicial=100000.0,
            total_ventas_efectivo=200000.0,
            total_gastos=10000.0,
            monto_fisico_real=295000.0,
        )
        self.assertEqual(arqueo.saldo_esperado, 290000.0)
        self.assertEqual(arqueo.diferencia, 5000.0)
        self.assertEqual(arqueo.tipo_diferencia, "SOBRANTE")

    def test_arqueo_con_faltante(self) -> None:
        arqueo: Arqueo = Arqueo(
            monto_inicial=100000.0,
            total_ventas_efectivo=200000.0,
            total_gastos=10000.0,
            monto_fisico_real=285000.0,
        )
        self.assertEqual(arqueo.saldo_esperado, 290000.0)
        self.assertEqual(arqueo.diferencia, -5000.0)
        self.assertEqual(arqueo.tipo_diferencia, "FALTANTE")

    def test_arqueo_sin_ventas_ni_gastos(self) -> None:
        arqueo: Arqueo = Arqueo(
            monto_inicial=100000.0,
            total_ventas_efectivo=0.0,
            total_gastos=0.0,
            monto_fisico_real=100000.0,
        )
        self.assertEqual(arqueo.saldo_esperado, 100000.0)
        self.assertEqual(arqueo.diferencia, 0.0)
        self.assertEqual(arqueo.tipo_diferencia, "CUADRADO")

    def test_arqueo_con_monto_inicial_cero(self) -> None:
        arqueo: Arqueo = Arqueo(
            monto_inicial=0.0,
            total_ventas_efectivo=150000.0,
            total_gastos=5000.0,
            monto_fisico_real=145000.0,
        )
        self.assertEqual(arqueo.saldo_esperado, 145000.0)
        self.assertEqual(arqueo.diferencia, 0.0)

    def test_obtener_resumen_contiene_todas_las_claves(self) -> None:
        arqueo: Arqueo = Arqueo(
            monto_inicial=100000.0,
            total_ventas_efectivo=50000.0,
            total_gastos=3000.0,
            monto_fisico_real=148000.0,
        )
        resumen = arqueo.obtener_resumen()
        claves_esperadas = [
            "monto_inicial",
            "total_ventas_efectivo",
            "total_gastos",
            "saldo_esperado",
            "monto_fisico_real",
            "diferencia",
            "tipo_diferencia",
        ]
        for clave in claves_esperadas:
            with self.subTest(clave=clave):
                self.assertIn(clave, resumen)

    def test_obtener_resumen_valores_correctos(self) -> None:
        arqueo: Arqueo = Arqueo(
            monto_inicial=100000.0,
            total_ventas_efectivo=200000.0,
            total_gastos=10000.0,
            monto_fisico_real=292000.0,
        )
        resumen = arqueo.obtener_resumen()
        self.assertEqual(resumen["monto_inicial"], 100000.0)
        self.assertEqual(resumen["total_ventas_efectivo"], 200000.0)
        self.assertEqual(resumen["total_gastos"], 10000.0)
        self.assertEqual(resumen["saldo_esperado"], 290000.0)
        self.assertEqual(resumen["monto_fisico_real"], 292000.0)
        self.assertEqual(resumen["diferencia"], 2000.0)
        self.assertEqual(resumen["tipo_diferencia"], "SOBRANTE")


class TestGasto(unittest.TestCase):

    def test_gasto_valido_no_lanza_excepcion(self) -> None:
        gasto: Gasto = Gasto(
            id_caja=1,
            fecha_hora="2026-09-22 10:30:00",
            monto=5000.0,
            descripcion="Compra de bolsas de hielo de emergencia",
            id_usuario=1,
        )
        gasto.validar()

    def test_gasto_con_monto_cero_lanza_excepcion(self) -> None:
        gasto: Gasto = Gasto(
            id_caja=1,
            fecha_hora="2026-09-22 10:30:00",
            monto=0.0,
            descripcion="Intento de gasto sin monto",
            id_usuario=1,
        )
        with self.assertRaises(MontoInvalidoError):
            gasto.validar()

    def test_gasto_con_monto_negativo_lanza_excepcion(self) -> None:
        gasto: Gasto = Gasto(
            id_caja=1,
            fecha_hora="2026-09-22 10:30:00",
            monto=-1000.0,
            descripcion="Intento de gasto negativo",
            id_usuario=1,
        )
        with self.assertRaises(MontoInvalidoError):
            gasto.validar()

    def test_gasto_con_descripcion_vacia_lanza_excepcion(self) -> None:
        gasto: Gasto = Gasto(
            id_caja=1,
            fecha_hora="2026-09-22 10:30:00",
            monto=5000.0,
            descripcion="",
            id_usuario=1,
        )
        with self.assertRaises(DescripcionGastoVaciaError):
            gasto.validar()

    def test_gasto_con_descripcion_solo_espacios_lanza_excepcion(self) -> None:
        gasto: Gasto = Gasto(
            id_caja=1,
            fecha_hora="2026-09-22 10:30:00",
            monto=5000.0,
            descripcion="   ",
            id_usuario=1,
        )
        with self.assertRaises(DescripcionGastoVaciaError):
            gasto.validar()


if __name__ == "__main__":
    unittest.main()
