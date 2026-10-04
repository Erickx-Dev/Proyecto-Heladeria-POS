from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import AutorizacionError, ValidacionError
from src.domain.category import Categoria
from src.domain.product import Producto
from src.domain.user import Usuario
from src.repositories.category_repository import CategoryRepository
from src.repositories.product_repository import ProductRepository
from src.services.catalog_service import CatalogService


class TestCategoryRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cat_repo.db"
        inicializar_base_de_datos(self.db_path)
        self.repo = CategoryRepository(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_crear_y_obtener_categoria(self) -> None:
        cat = Categoria(nombre_categoria="Postres Especiales", descripcion="Tortas y copas")
        id_cat = self.repo.crear_categoria(cat)
        self.assertGreater(id_cat, 0)

        recuperada = self.repo.obtener_por_id(id_cat)
        self.assertIsNotNone(recuperada)
        self.assertEqual(recuperada.nombre_categoria, "Postres Especiales")
        self.assertEqual(recuperada.descripcion, "Tortas y copas")

    def test_obtener_por_nombre(self) -> None:
        cat = Categoria(nombre_categoria="Cafetería", descripcion="Cafés calientes")
        self.repo.crear_categoria(cat)

        recuperada = self.repo.obtener_por_nombre("cafetería")
        self.assertIsNotNone(recuperada)
        self.assertEqual(recuperada.nombre_categoria, "Cafetería")

    def test_obtener_por_id_inexistente(self) -> None:
        self.assertIsNone(self.repo.obtener_por_id(9999))

    def test_actualizar_categoria(self) -> None:
        cat = Categoria(nombre_categoria="Snacks", descripcion="Papas y nachos")
        id_cat = self.repo.crear_categoria(cat)

        cat_edit = Categoria(id_categoria=id_cat, nombre_categoria="Snacks Salados", descripcion="Snacks variados")
        exito = self.repo.actualizar_categoria(cat_edit)
        self.assertTrue(exito)

        actualizada = self.repo.obtener_por_id(id_cat)
        self.assertEqual(actualizada.nombre_categoria, "Snacks Salados")

    def test_actualizar_sin_id_error(self) -> None:
        cat = Categoria(nombre_categoria="Prueba")
        with self.assertRaises(ValidacionError):
            self.repo.actualizar_categoria(cat)

    def test_eliminar_categoria(self) -> None:
        cat = Categoria(nombre_categoria="Temporal")
        id_cat = self.repo.crear_categoria(cat)
        self.assertTrue(self.repo.eliminar_categoria(id_cat))
        self.assertIsNone(self.repo.obtener_por_id(id_cat))

    def test_categoria_duplicada_sqlite_error(self) -> None:
        cat1 = Categoria(nombre_categoria="Misma Categoria")
        self.repo.crear_categoria(cat1)
        cat2 = Categoria(nombre_categoria="Misma Categoria")
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.crear_categoria(cat2)

    def test_listar_categorias(self) -> None:
        lista = self.repo.listar_categorias()
        self.assertGreaterEqual(len(lista), 3)


class TestProductRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_prod_repo.db"
        inicializar_base_de_datos(self.db_path)
        self.repo = ProductRepository(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_crear_y_obtener_producto(self) -> None:
        prod = Producto(codigo="HEL-001", nombre="Cono Vainilla", precio_venta=3500.0, id_categoria=1, estado=1)
        id_prod = self.repo.crear_producto(prod)
        self.assertGreater(id_prod, 0)

        recuperado = self.repo.obtener_por_id(id_prod)
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.codigo, "HEL-001")
        self.assertEqual(recuperado.nombre, "Cono Vainilla")
        self.assertEqual(recuperado.precio_venta, 3500.0)

    def test_obtener_por_codigo(self) -> None:
        prod = Producto(codigo="BEB-001", nombre="Agua Mineral", precio_venta=2000.0, id_categoria=2)
        self.repo.crear_producto(prod)

        recuperado = self.repo.obtener_por_codigo("beb-001")
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.codigo, "BEB-001")

    def test_actualizar_producto(self) -> None:
        prod = Producto(codigo="HEL-002", nombre="Cono Fresa", precio_venta=3500.0, id_categoria=1)
        id_prod = self.repo.crear_producto(prod)

        prod_edit = Producto(id_producto=id_prod, codigo="HEL-002", nombre="Cono Fresa Silvestre", precio_venta=4000.0, id_categoria=1, estado=1)
        self.assertTrue(self.repo.actualizar_producto(prod_edit))

        actualizado = self.repo.obtener_por_id(id_prod)
        self.assertEqual(actualizado.nombre, "Cono Fresa Silvestre")
        self.assertEqual(actualizado.precio_venta, 4000.0)

    def test_cambiar_estado_producto(self) -> None:
        prod = Producto(codigo="HEL-003", nombre="Paleta Limón", precio_venta=2500.0, id_categoria=1)
        id_prod = self.repo.crear_producto(prod)

        self.assertTrue(self.repo.cambiar_estado(id_prod, 0))
        actualizado = self.repo.obtener_por_id(id_prod)
        self.assertEqual(actualizado.estado, 0)
        self.assertFalse(actualizado.es_activo())

    def test_cambiar_estado_invalido(self) -> None:
        with self.assertRaises(ValidacionError):
            self.repo.cambiar_estado(1, 9)

    def test_listar_productos_filtros(self) -> None:
        p1 = Producto(codigo="P-1", nombre="Prod 1", precio_venta=1000.0, id_categoria=1, estado=1)
        p2 = Producto(codigo="P-2", nombre="Prod 2", precio_venta=2000.0, id_categoria=1, estado=0)
        p3 = Producto(codigo="P-3", nombre="Prod 3", precio_venta=3000.0, id_categoria=2, estado=1)
        self.repo.crear_producto(p1)
        self.repo.crear_producto(p2)
        self.repo.crear_producto(p3)

        todos = self.repo.listar_productos()
        self.assertEqual(len(todos), 3)

        activos = self.repo.listar_productos(solo_activos=True)
        self.assertEqual(len(activos), 2)

        cat1 = self.repo.listar_productos(id_categoria=1)
        self.assertEqual(len(cat1), 2)

        cat1_activos = self.repo.listar_productos(solo_activos=True, id_categoria=1)
        self.assertEqual(len(cat1_activos), 1)


class TestCatalogService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cat_svc.db"
        inicializar_base_de_datos(self.db_path)
        self.cat_repo = CategoryRepository(db_path=self.db_path)
        self.prod_repo = ProductRepository(db_path=self.db_path)
        self.service = CatalogService(
            category_repository=self.cat_repo,
            product_repository=self.prod_repo,
            db_path=self.db_path,
        )
        self.admin = Usuario(id_usuario=1, username="admin", nombre="Admin", id_rol=1, estado=1)
        self.empleado = Usuario(id_usuario=2, username="empleado", nombre="Empleado", id_rol=2, estado=1)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_admin_puede_crear_categoria(self) -> None:
        cat = self.service.crear_categoria(self.admin, "Bebidas Calientes", "Café y té")
        self.assertIsNotNone(cat.id_categoria)
        self.assertEqual(cat.nombre_categoria, "Bebidas Calientes")

    def test_empleado_rechazado_crear_categoria(self) -> None:
        with self.assertRaises(AutorizacionError):
            self.service.crear_categoria(self.empleado, "Sin Permiso")

    def test_crear_categoria_nombre_vacio(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.crear_categoria(self.admin, "   ")

    def test_crear_categoria_nombre_duplicado(self) -> None:
        self.service.crear_categoria(self.admin, "Salsas")
        with self.assertRaises(ValidacionError):
            self.service.crear_categoria(self.admin, "salsas")

    def test_actualizar_categoria(self) -> None:
        cat = self.service.crear_categoria(self.admin, "Galletas")
        actualizada = self.service.actualizar_categoria(self.admin, cat.id_categoria, "Galletas Artesanales")
        self.assertEqual(actualizada.nombre_categoria, "Galletas Artesanales")

    def test_eliminar_categoria_sin_productos(self) -> None:
        cat = self.service.crear_categoria(self.admin, "Vacia")
        self.assertTrue(self.service.eliminar_categoria(self.admin, cat.id_categoria))
        self.assertIsNone(self.service.obtener_categoria_por_id(cat.id_categoria))

    def test_eliminar_categoria_con_productos_rechazado(self) -> None:
        cat = self.service.crear_categoria(self.admin, "Con Productos")
        self.service.crear_producto(self.admin, "CP-01", "Prod Con Cat", 1500.0, cat.id_categoria)

        with self.assertRaises(ValidacionError):
            self.service.eliminar_categoria(self.admin, cat.id_categoria)

    def test_admin_puede_crear_producto(self) -> None:
        prod = self.service.crear_producto(self.admin, "HEL-CHOCO", "Helado Chocolate", 4500.0, 1)
        self.assertIsNotNone(prod.id_producto)
        self.assertEqual(prod.codigo, "HEL-CHOCO")
        self.assertEqual(prod.nombre, "Helado Chocolate")

    def test_empleado_rechazado_crear_producto(self) -> None:
        with self.assertRaises(AutorizacionError):
            self.service.crear_producto(self.empleado, "EMP-01", "Helado Empleado", 3000.0, 1)

    def test_crear_producto_categoria_inexistente(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.crear_producto(self.admin, "XYZ-01", "Helado Fantasma", 3000.0, 9999)

    def test_crear_producto_codigo_duplicado(self) -> None:
        self.service.crear_producto(self.admin, "COD-01", "Primer Producto", 3000.0, 1)
        with self.assertRaises(ValidacionError):
            self.service.crear_producto(self.admin, "cod-01", "Segundo Producto", 3500.0, 1)

    def test_crear_producto_precio_negativo(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.crear_producto(self.admin, "COD-NEG", "Producto Negativo", -500.0, 1)

    def test_actualizar_producto(self) -> None:
        prod = self.service.crear_producto(self.admin, "ACT-01", "Helado Inicial", 3000.0, 1)
        actualizado = self.service.actualizar_producto(
            self.admin, prod.id_producto, "ACT-01", "Helado Modificado", 3800.0, 1, 1
        )
        self.assertEqual(actualizado.nombre, "Helado Modificado")
        self.assertEqual(actualizado.precio_venta, 3800.0)

    def test_cambiar_estado_producto(self) -> None:
        prod = self.service.crear_producto(self.admin, "DES-01", "Helado Para Suspender", 3000.0, 1)
        self.assertTrue(self.service.cambiar_estado_producto(self.admin, prod.id_producto, 0))
        recuperado = self.service.obtener_producto_por_id(prod.id_producto)
        self.assertEqual(recuperado.estado, 0)

    def test_listar_productos_y_filtros(self) -> None:
        self.service.crear_producto(self.admin, "L-1", "Prod L1", 1000.0, 1, estado=1)
        self.service.crear_producto(self.admin, "L-2", "Prod L2", 2000.0, 1, estado=0)
        self.service.crear_producto(self.admin, "L-3", "Prod L3", 3000.0, 2, estado=1)

        todos = self.service.listar_productos()
        self.assertEqual(len(todos), 3)

        activos = self.service.listar_productos(solo_activos=True)
        self.assertEqual(len(activos), 2)


if __name__ == "__main__":
    unittest.main()
