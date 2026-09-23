from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import (
    CantidadInvalidaError,
    InsumoNoEncontradoError,
    MermaInvalidaError,
    StockInsuficienteError,
)
from src.services.inventory_service import InventoryService


class TestInventoryService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_heladeria.db"
        inicializar_base_de_datos(db_path=self.db_path, forzar=True)
        self.service = InventoryService(db_path=self.db_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_registrar_y_obtener_insumo(self) -> None:
        insumo = self.service.registrar_insumo(
            nombre="Base de Vainilla",
            unidad_medida="Litros",
            stock_actual=25.0,
            stock_minimo=5.0,
        )
        self.assertIsNotNone(insumo.id_insumo)

        obtenido = self.service.obtener_insumo(insumo.id_insumo)
        self.assertEqual(obtenido.nombre, "Base de Vainilla")
        self.assertEqual(obtenido.stock_actual, 25.0)
        self.assertEqual(obtenido.stock_minimo, 5.0)

    def test_descontar_stock_exitoso(self) -> None:
        insumo = self.service.registrar_insumo(
            nombre="Conos de Galleta",
            unidad_medida="Unidades",
            stock_actual=100.0,
            stock_minimo=20.0,
        )
        actualizado = self.service.descontar_stock(insumo.id_insumo, 15.0)
        self.assertEqual(actualizado.stock_actual, 85.0)

        en_db = self.service.obtener_insumo(insumo.id_insumo)
        self.assertEqual(en_db.stock_actual, 85.0)

    def test_descontar_stock_insuficiente_lanza_excepcion(self) -> None:
        insumo = self.service.registrar_insumo(
            nombre="Sirope de Caramelo",
            unidad_medida="Litros",
            stock_actual=3.0,
            stock_minimo=1.0,
        )
        with self.assertRaises(StockInsuficienteError):
            self.service.descontar_stock(insumo.id_insumo, 10.0)

    def test_descontar_insumo_inexistente_lanza_excepcion(self) -> None:
        with self.assertRaises(InsumoNoEncontradoError):
            self.service.descontar_stock(99999, 1.0)

    def test_descontar_cantidad_invalida_lanza_excepcion(self) -> None:
        insumo = self.service.registrar_insumo(
            nombre="Fresas",
            unidad_medida="Kg",
            stock_actual=10.0,
            stock_minimo=2.0,
        )
        with self.assertRaises(CantidadInvalidaError):
            self.service.descontar_stock(insumo.id_insumo, 0.0)

        with self.assertRaises(CantidadInvalidaError):
            self.service.descontar_stock(insumo.id_insumo, -5.0)

    def test_incrementar_stock(self) -> None:
        insumo = self.service.registrar_insumo(
            nombre="Gomitas",
            unidad_medida="Kg",
            stock_actual=5.0,
            stock_minimo=2.0,
        )
        actualizado = self.service.incrementar_stock(insumo.id_insumo, 10.0, id_usuario=1)
        self.assertEqual(actualizado.stock_actual, 15.0)

    def test_verificar_alertas_stock(self) -> None:
        self.service.registrar_insumo("Chocolate", "Kg", stock_actual=20.0, stock_minimo=5.0)
        self.service.registrar_insumo("Arequipe", "Kg", stock_actual=6.0, stock_minimo=5.0)
        self.service.registrar_insumo("Maracuya", "Kg", stock_actual=3.0, stock_minimo=5.0)

        alertas = self.service.verificar_alertas_stock()
        self.assertEqual(len(alertas), 3)

        mapa_alertas = {a["nombre"]: a for a in alertas}
        self.assertEqual(mapa_alertas["Chocolate"]["nivel_alerta"], "VERDE")
        self.assertFalse(mapa_alertas["Chocolate"]["requiere_resurtido"])

        self.assertEqual(mapa_alertas["Arequipe"]["nivel_alerta"], "NARANJA")
        self.assertFalse(mapa_alertas["Arequipe"]["requiere_resurtido"])

        self.assertEqual(mapa_alertas["Maracuya"]["nivel_alerta"], "ROJO")
        self.assertTrue(mapa_alertas["Maracuya"]["requiere_resurtido"])

        criticos = self.service.listar_insumos_criticos()
        self.assertEqual(len(criticos), 1)
        self.assertEqual(criticos[0].nombre, "Maracuya")

    def test_registrar_merma_exitosa_descuenta_stock(self) -> None:
        insumo = self.service.registrar_insumo(
            nombre="Helado de Mango",
            unidad_medida="Litros",
            stock_actual=15.0,
            stock_minimo=3.0,
        )
        merma = self.service.registrar_merma(
            id_insumo=insumo.id_insumo,
            cantidad=2.5,
            motivo="Descongelamiento nocturno de vitrina",
            id_usuario=1,
        )
        self.assertIsNotNone(merma.id_merma)
        self.assertEqual(merma.cantidad, 2.5)

        en_db = self.service.obtener_insumo(insumo.id_insumo)
        self.assertEqual(en_db.stock_actual, 12.5)

        mermas = self.service.listar_mermas()
        self.assertEqual(len(mermas), 1)
        self.assertEqual(mermas[0].motivo, "Descongelamiento nocturno de vitrina")

    def test_registrar_merma_con_stock_insuficiente_lanza_excepcion(self) -> None:
        insumo = self.service.registrar_insumo(
            nombre="Mora",
            unidad_medida="Kg",
            stock_actual=2.0,
            stock_minimo=1.0,
        )
        with self.assertRaises(StockInsuficienteError):
            self.service.registrar_merma(
                id_insumo=insumo.id_insumo,
                cantidad=10.0,
                motivo="Derrame accidental",
                id_usuario=1,
            )

    def test_registrar_merma_con_motivo_vacio_lanza_excepcion(self) -> None:
        insumo = self.service.registrar_insumo(
            nombre="Nueces",
            unidad_medida="Kg",
            stock_actual=5.0,
            stock_minimo=1.0,
        )
        with self.assertRaises(MermaInvalidaError):
            self.service.registrar_merma(
                id_insumo=insumo.id_insumo,
                cantidad=1.0,
                motivo="   ",
                id_usuario=1,
            )


if __name__ == "__main__":
    unittest.main()
