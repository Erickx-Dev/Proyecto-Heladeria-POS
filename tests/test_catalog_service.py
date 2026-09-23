"""
Suite de Pruebas Unitarias para el Módulo de Catálogo, Insumos y Recetas.

Valida las entidades de dominio (Categoria, Insumo, Producto, ProductoSimple, ProductoCompuesto),
los repositorios de datos y el servicio de aplicación CatalogService.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import (
    CategoriaNoEncontradaError,
    EntidadDuplicadaError,
    InsumoNoEncontradoError,
    ProductoNoEncontradoError,
    ReglaNegocioError,
)
from src.domain.category import Categoria
from src.domain.product import Producto, ProductoCompuesto, ProductoSimple
from src.domain.supply import Insumo
from src.repositories.category_repository import CategoryRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.supply_repository import SupplyRepository
from src.services.catalog_service import CatalogService


class TestDomainEntities(unittest.TestCase):
    """Pruebas unitarias de las entidades puras de dominio."""

    def test_categoria_creacion_y_validaciones(self) -> None:
        cat = Categoria(nombre_categoria="  Helados de Agua  ", descripcion="Paletas y nieves")
        self.assertEqual(cat.nombre_categoria, "Helados de Agua")
        self.assertEqual(cat.descripcion, "Paletas y nieves")

        with self.assertRaises(ValueError):
            Categoria(nombre_categoria="   ")

    def test_insumo_creacion_y_control_de_stock(self) -> None:
        insumo = Insumo(
            nombre="Helado Vainilla",
            unidad_medida="Litros",
            stock_actual=10.0,
            stock_minimo=5.0,
        )
        self.assertFalse(insumo.esta_en_stock_minimo())

        # Consumo de stock
        insumo.deducir_stock(6.0)
        self.assertEqual(insumo.stock_actual, 4.0)
        self.assertTrue(insumo.esta_en_stock_minimo())

        # Abastecimiento
        insumo.asentar_abastecimiento(15.0)
        self.assertEqual(insumo.stock_actual, 19.0)
        self.assertFalse(insumo.esta_en_stock_minimo())

        # Excepciones de validación
        with self.assertRaises(ValueError):
            insumo.deducir_stock(50.0)

        with self.assertRaises(ValueError):
            insumo.asentar_abastecimiento(-2.0)

        with self.assertRaises(ValueError):
            Insumo(nombre="", unidad_medida="Litros")

    def test_producto_simple_y_compuesto(self) -> None:
        # Producto simple
        prod_simple = ProductoSimple(
            codigo="PAL-001",
            nombre="Paleta de Fresa",
            precio_venta=25.0,
            id_categoria=1,
        )
        self.assertTrue(prod_simple.esta_activo())
        prod_simple.suspender()
        self.assertFalse(prod_simple.esta_activo())
        prod_simple.activar()
        self.assertTrue(prod_simple.esta_activo())

        prod_simple.actualizar_precio(30.0)
        self.assertEqual(prod_simple.precio_venta, 30.0)

        with self.assertRaises(ValueError):
            prod_simple.actualizar_precio(-5.0)

        # Producto compuesto con receta
        prod_compuesto = ProductoCompuesto(
            codigo="CONO-002",
            nombre="Cono Doble Artesanal",
            precio_venta=45.0,
            id_categoria=1,
            receta={1: 2.0, 2: 1.0},
        )
        self.assertEqual(prod_compuesto.obtener_receta(), {1: 2.0, 2: 1.0})
        prod_compuesto.agregar_insumo_receta(3, 0.5)
        self.assertIn(3, prod_compuesto.obtener_receta())
        prod_compuesto.quitar_insumo_receta(3)
        self.assertNotIn(3, prod_compuesto.obtener_receta())


class TestCatalogServiceIntegration(unittest.TestCase):
    """Pruebas de integración del servicio CatalogService con la base de datos."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_catalogo.db"
        inicializar_base_de_datos(self.db_path)

        self.category_repo = CategoryRepository(self.db_path)
        self.supply_repo = SupplyRepository(self.db_path)
        self.product_repo = ProductRepository(self.db_path)

        self.service = CatalogService(
            category_repo=self.category_repo,
            supply_repo=self.supply_repo,
            product_repo=self.product_repo,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # --- Pruebas de Categorías ---

    def test_crud_categorias(self) -> None:
        # 1. Crear
        cat = self.service.crear_categoria("Postres Fríos", "Tartas y copas heladas")
        self.assertIsNotNone(cat.id_categoria)
        self.assertEqual(cat.nombre_categoria, "Postres Fríos")

        # 2. Consultar
        recuperada = self.service.obtener_categoria(cat.id_categoria)
        self.assertEqual(recuperada.nombre_categoria, "Postres Fríos")

        # 3. Listar (incluye las 3 semillas + la nueva)
        lista = self.service.listar_categorias()
        self.assertGreaterEqual(len(lista), 4)

        # 4. Actualizar
        actualizada = self.service.actualizar_categoria(
            cat.id_categoria, "Postres Gourmet", "Copas y tartas especiales"
        )
        self.assertEqual(actualizada.nombre_categoria, "Postres Gourmet")

        # 5. Duplicada
        with self.assertRaises(EntidadDuplicadaError):
            self.service.crear_categoria("Postres Gourmet")

        # 6. Eliminar
        self.assertTrue(self.service.eliminar_categoria(cat.id_categoria))
        with self.assertRaises(CategoriaNoEncontradaError):
            self.service.obtener_categoria(cat.id_categoria)

    # --- Pruebas de Insumos ---

    def test_crud_insumos_y_abastecimiento(self) -> None:
        # 1. Crear insumos de bodega
        insumo1 = self.service.crear_insumo("Helado Chocolate", "Litros", 5.0, 10.0)
        insumo2 = self.service.crear_insumo("Conos Barquillo", "Unidades", 100.0, 30.0)
        self.assertIsNotNone(insumo1.id_insumo)

        # 2. Consultar
        recuperado = self.service.obtener_insumo(insumo1.id_insumo)
        self.assertEqual(recuperado.nombre, "Helado Chocolate")

        # 3. Alertas de stock mínimo
        # insumo1 tiene 5.0 <= 10.0 -> debe disparar alerta
        # insumo2 tiene 100.0 > 30.0 -> no dispara alerta
        alertas = self.service.listar_insumos_en_alerta()
        ids_alerta = [i.id_insumo for i in alertas]
        self.assertIn(insumo1.id_insumo, ids_alerta)
        self.assertNotIn(insumo2.id_insumo, ids_alerta)

        # 4. Abastecimiento de mercancía
        abastecido = self.service.asentar_abastecimiento(insumo1.id_insumo, 20.0, costo_unitario=12.5)
        self.assertEqual(abastecido.stock_actual, 25.0)

        # Ya no debe estar en alerta
        alertas_post = self.service.listar_insumos_en_alerta()
        ids_alerta_post = [i.id_insumo for i in alertas_post]
        self.assertNotIn(insumo1.id_insumo, ids_alerta_post)

        # 5. Actualizar insumo
        actualizado = self.service.actualizar_insumo(
            insumo1.id_insumo, "Helado Chocolate Belga", "Litros", 15.0
        )
        self.assertEqual(actualizado.nombre, "Helado Chocolate Belga")
        self.assertEqual(actualizado.stock_minimo, 15.0)

        # 6. Eliminar insumo
        self.assertTrue(self.service.eliminar_insumo(insumo2.id_insumo))
        with self.assertRaises(InsumoNoEncontradoError):
            self.service.obtener_insumo(insumo2.id_insumo)

    # --- Pruebas de Productos ---

    def test_crud_productos_simples_y_compuestos(self) -> None:
        # Insumos base
        insumo_base = self.service.crear_insumo("Base Chocolate", "Litros", 10.0, 2.0)

        # 1. Crear producto simple
        p_simple = self.service.crear_producto_simple(
            codigo="AGUA-01",
            nombre="Agua Mineral 500ml",
            precio_venta=15.0,
            id_categoria=2,
        )
        self.assertIsNotNone(p_simple.id_producto)
        self.assertTrue(p_simple.esta_activo())

        # 2. Crear producto compuesto con receta
        p_comp = self.service.crear_producto_compuesto(
            codigo="MAL-CHOC",
            nombre="Malteada de Chocolate",
            precio_venta=65.0,
            id_categoria=2,
            receta={insumo_base.id_insumo: 0.3},
        )
        self.assertIsNotNone(p_comp.id_producto)
        self.assertEqual(p_comp.obtener_receta()[insumo_base.id_insumo], 0.3)

        # 3. Consultar por código
        p_rec = self.service.obtener_producto_por_codigo("MAL-CHOC")
        self.assertEqual(p_rec.nombre, "Malteada de Chocolate")

        # 4. Actualizar precio de venta
        self.service.actualizar_precio_producto(p_simple.id_producto, 18.0)
        p_actualizado = self.service.obtener_producto(p_simple.id_producto)
        self.assertEqual(p_actualizado.precio_venta, 18.0)

        # 5. Suspender y activar producto
        self.service.suspender_producto(p_simple.id_producto)
        p_suspendido = self.service.obtener_producto(p_simple.id_producto)
        self.assertFalse(p_suspendido.esta_activo())

        # Listar solo activos no debe incluirlo
        activos = self.service.listar_productos(solo_activos=True)
        codigos_activos = [p.codigo for p in activos]
        self.assertNotIn("AGUA-01", codigos_activos)

        # Reactivar
        self.service.activar_producto(p_simple.id_producto)
        p_activo = self.service.obtener_producto(p_simple.id_producto)
        self.assertTrue(p_activo.esta_activo())

        # 6. Intentar registrar código duplicado
        with self.assertRaises(EntidadDuplicadaError):
            self.service.crear_producto_simple(
                codigo="AGUA-01",
                nombre="Agua Duplicada",
                precio_venta=20.0,
                id_categoria=2,
            )

        # 7. No se puede eliminar categoría si tiene productos asignados
        with self.assertRaises(ReglaNegocioError):
            self.service.eliminar_categoria(2)


if __name__ == "__main__":
    unittest.main()
