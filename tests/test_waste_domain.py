from __future__ import annotations

import unittest

from src.core.exceptions import CantidadInvalidaError, MermaInvalidaError, StockInsuficienteError
from src.domain.inventory import Insumo, NivelAlertaStock
from src.domain.waste import Merma


class TestWasteAndInventoryDomain(unittest.TestCase):

    def test_merma_creacion_exitosa(self) -> None:
        merma = Merma(
            id_insumo=1,
            cantidad=2.5,
            motivo="Descongelamiento por falla electrica",
            fecha_hora="2026-09-22 18:30:00",
            id_usuario=1,
        )
        self.assertEqual(merma.id_insumo, 1)
        self.assertEqual(merma.cantidad, 2.5)
        self.assertEqual(merma.motivo, "Descongelamiento por falla electrica")

    def test_merma_cantidad_invalida_lanza_excepcion(self) -> None:
        with self.assertRaises(MermaInvalidaError):
            Merma(
                id_insumo=1,
                cantidad=0.0,
                motivo="Avería",
                fecha_hora="2026-09-22 18:30:00",
                id_usuario=1,
            )

        with self.assertRaises(MermaInvalidaError):
            Merma(
                id_insumo=1,
                cantidad=-1.5,
                motivo="Avería",
                fecha_hora="2026-09-22 18:30:00",
                id_usuario=1,
            )

    def test_merma_motivo_vacio_lanza_excepcion(self) -> None:
        with self.assertRaises(MermaInvalidaError):
            Merma(
                id_insumo=1,
                cantidad=1.0,
                motivo="   ",
                fecha_hora="2026-09-22 18:30:00",
                id_usuario=1,
            )

    def test_insumo_descuento_valido(self) -> None:
        insumo = Insumo(
            id_insumo=1,
            nombre="Leche Entera",
            unidad_medida="Litros",
            stock_actual=10.0,
            stock_minimo=2.0,
        )
        insumo.descontar(3.5)
        self.assertEqual(insumo.stock_actual, 6.5)

    def test_insumo_descuento_insuficiente_lanza_excepcion(self) -> None:
        insumo = Insumo(
            id_insumo=1,
            nombre="Leche Entera",
            unidad_medida="Litros",
            stock_actual=2.0,
            stock_minimo=1.0,
        )
        with self.assertRaises(StockInsuficienteError):
            insumo.descontar(5.0)

    def test_insumo_incremento_valido(self) -> None:
        insumo = Insumo(
            id_insumo=1,
            nombre="Crema",
            unidad_medida="Litros",
            stock_actual=5.0,
            stock_minimo=1.0,
        )
        insumo.incrementar(3.0)
        self.assertEqual(insumo.stock_actual, 8.0)

    def test_insumo_niveles_de_alerta_stock(self) -> None:
        insumo = Insumo(
            id_insumo=1,
            nombre="Cobertura Chocolate",
            unidad_medida="Kg",
            stock_actual=10.0,
            stock_minimo=2.0,
        )
        self.assertEqual(insumo.obtener_nivel_alerta(), NivelAlertaStock.NORMAL)
        self.assertFalse(insumo.requiere_resurtido())

        insumo.stock_actual = 2.5
        self.assertEqual(insumo.obtener_nivel_alerta(), NivelAlertaStock.ADVERTENCIA)
        self.assertFalse(insumo.requiere_resurtido())

        insumo.stock_actual = 2.0
        self.assertEqual(insumo.obtener_nivel_alerta(), NivelAlertaStock.CRITICO)
        self.assertTrue(insumo.requiere_resurtido())

        insumo.stock_actual = 0.5
        self.assertEqual(insumo.obtener_nivel_alerta(), NivelAlertaStock.CRITICO)
        self.assertTrue(insumo.requiere_resurtido())


if __name__ == "__main__":
    unittest.main()
