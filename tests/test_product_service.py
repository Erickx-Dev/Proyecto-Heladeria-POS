from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import ProductoNoEncontradoError
from src.services.product_service import ProductService


class TestProductService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_heladeria.db"
        inicializar_base_de_datos(db_path=self.db_path, forzar=True)
        self.service = ProductService(db_path=self.db_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_listar_categorias_semilla(self) -> None:
        categorias = self.service.listar_categorias()
        self.assertGreaterEqual(len(categorias), 3)

    def test_crear_categoria(self) -> None:
        cat = self.service.crear_categoria(nombre="Especiales de Temporada", descripcion="Edicion limitada")
        self.assertIsNotNone(cat.id_categoria)
        obtenida = self.service.obtener_categoria(cat.id_categoria)
        self.assertIsNotNone(obtenida)
        self.assertEqual(obtenida.nombre_categoria, "Especiales de Temporada")

    def test_registrar_y_obtener_producto(self) -> None:
        prod = self.service.registrar_producto(
            codigo="HEL-001",
            nombre="Cono Simple Artesanal",
            precio_venta=4500.0,
            id_categoria=1,
        )
        self.assertIsNotNone(prod.id_producto)

        por_id = self.service.obtener_producto_por_id(prod.id_producto)
        self.assertEqual(por_id.codigo, "HEL-001")
        self.assertEqual(por_id.precio_venta, 4500.0)

        por_codigo = self.service.obtener_producto_por_codigo("HEL-001")
        self.assertEqual(por_codigo.nombre, "Cono Simple Artesanal")

    def test_obtener_producto_inexistente_lanza_excepcion(self) -> None:
        with self.assertRaises(ProductoNoEncontradoError):
            self.service.obtener_producto_por_id(99999)

        with self.assertRaises(ProductoNoEncontradoError):
            self.service.obtener_producto_por_codigo("NO-EXISTE")

    def test_actualizar_producto(self) -> None:
        prod = self.service.registrar_producto(
            codigo="HEL-002",
            nombre="Copa Especial",
            precio_venta=8000.0,
            id_categoria=1,
        )
        actualizado = self.service.actualizar_producto(
            id_producto=prod.id_producto,
            codigo="HEL-002-MOD",
            nombre="Copa Especial Gigante",
            precio_venta=9500.0,
            id_categoria=1,
            estado=1,
        )
        self.assertEqual(actualizado.nombre, "Copa Especial Gigante")
        self.assertEqual(actualizado.precio_venta, 9500.0)

    def test_desactivar_y_activar_producto(self) -> None:
        prod = self.service.registrar_producto(
            codigo="HEL-003",
            nombre="Malteada Fresa",
            precio_venta=7000.0,
            id_categoria=2,
        )
        self.service.desactivar_producto(prod.id_producto)
        activos = self.service.listar_productos_activos()
        self.assertFalse(any(p.id_producto == prod.id_producto for p in activos))

        self.service.activar_producto(prod.id_producto)
        activos_recuperados = self.service.listar_productos_activos()
        self.assertTrue(any(p.id_producto == prod.id_producto for p in activos_recuperados))


if __name__ == "__main__":
    unittest.main()
