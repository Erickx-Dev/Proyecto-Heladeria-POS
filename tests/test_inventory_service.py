from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import AutorizacionError, StockInsuficienteError, ValidacionError
from src.domain.product import Producto
from src.domain.supply import Insumo
from src.domain.user import Usuario
from src.repositories.product_repository import ProductRepository
from src.repositories.recipe_repository import RecipeRepository
from src.repositories.supply_repository import SupplyRepository
from src.services.inventory_service import InventoryService


class TestSupplyRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_sup_repo.db"
        inicializar_base_de_datos(self.db_path)
        self.repo = SupplyRepository(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_crear_y_obtener_insumo(self) -> None:
        insumo = Insumo(nombre="Leche Entera", unidad_medida="Litros", stock_actual=50.0, stock_minimo=10.0)
        id_ins = self.repo.crear_insumo(insumo)
        self.assertGreater(id_ins, 0)

        recuperado = self.repo.obtener_por_id(id_ins)
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.nombre, "Leche Entera")
        self.assertEqual(recuperado.unidad_medida, "Litros")
        self.assertEqual(recuperado.stock_actual, 50.0)
        self.assertEqual(recuperado.stock_minimo, 10.0)

    def test_obtener_por_nombre(self) -> None:
        insumo = Insumo(nombre="Azúcar Refinada", unidad_medida="Kilogramos", stock_actual=30.0, stock_minimo=5.0)
        self.repo.crear_insumo(insumo)

        recuperado = self.repo.obtener_por_nombre("azúcar refinada")
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.nombre, "Azúcar Refinada")

    def test_actualizar_insumo(self) -> None:
        insumo = Insumo(nombre="Cacao", unidad_medida="Gramos", stock_actual=1000.0, stock_minimo=200.0)
        id_ins = self.repo.crear_insumo(insumo)

        editado = Insumo(id_insumo=id_ins, nombre="Cacao Puro", unidad_medida="Gramos", stock_actual=1000.0, stock_minimo=250.0)
        self.assertTrue(self.repo.actualizar_insumo(editado))

        recuperado = self.repo.obtener_por_id(id_ins)
        self.assertEqual(recuperado.nombre, "Cacao Puro")
        self.assertEqual(recuperado.stock_minimo, 250.0)

    def test_descontar_stock_exitoso(self) -> None:
        insumo = Insumo(nombre="Crema de Leche", unidad_medida="Litros", stock_actual=20.0, stock_minimo=5.0)
        id_ins = self.repo.crear_insumo(insumo)

        self.assertTrue(self.repo.descontar_stock(id_ins, 5.5))
        recuperado = self.repo.obtener_por_id(id_ins)
        self.assertEqual(recuperado.stock_actual, 14.5)

    def test_descontar_stock_insuficiente(self) -> None:
        insumo = Insumo(nombre="Vainilla Natural", unidad_medida="Mililitros", stock_actual=10.0, stock_minimo=2.0)
        id_ins = self.repo.crear_insumo(insumo)

        with self.assertRaises(StockInsuficienteError):
            self.repo.descontar_stock(id_ins, 15.0)

    def test_aumentar_stock_exitoso(self) -> None:
        insumo = Insumo(nombre="Fresa Congelada", unidad_medida="Kilogramos", stock_actual=8.0, stock_minimo=3.0)
        id_ins = self.repo.crear_insumo(insumo)

        self.assertTrue(self.repo.aumentar_stock(id_ins, 12.0))
        recuperado = self.repo.obtener_por_id(id_ins)
        self.assertEqual(recuperado.stock_actual, 20.0)

    def test_obtener_insumos_en_alerta(self) -> None:
        i1 = Insumo(nombre="Insumo Ok", unidad_medida="U", stock_actual=15.0, stock_minimo=5.0)
        i2 = Insumo(nombre="Insumo Alerta 1", unidad_medida="U", stock_actual=4.0, stock_minimo=5.0)
        i3 = Insumo(nombre="Insumo Alerta 2", unidad_medida="U", stock_actual=5.0, stock_minimo=5.0)
        self.repo.crear_insumo(i1)
        self.repo.crear_insumo(i2)
        self.repo.crear_insumo(i3)

        alertas = self.repo.obtener_insumos_en_alerta()
        self.assertEqual(len(alertas), 2)
        nombres = [a.nombre for a in alertas]
        self.assertIn("Insumo Alerta 1", nombres)
        self.assertIn("Insumo Alerta 2", nombres)


class TestRecipeRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_rec_repo.db"
        inicializar_base_de_datos(self.db_path)
        self.prod_repo = ProductRepository(db_path=self.db_path)
        self.sup_repo = SupplyRepository(db_path=self.db_path)
        self.recipe_repo = RecipeRepository(db_path=self.db_path)

        self.id_prod = self.prod_repo.crear_producto(
            Producto(codigo="TEST-01", nombre="Helado Test", precio_venta=3000.0, id_categoria=1)
        )
        self.id_ins1 = self.sup_repo.crear_insumo(
            Insumo(nombre="Leche", unidad_medida="L", stock_actual=20.0, stock_minimo=2.0)
        )
        self.id_ins2 = self.sup_repo.crear_insumo(
            Insumo(nombre="Azúcar", unidad_medida="Kg", stock_actual=10.0, stock_minimo=1.0)
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_asociar_insumo_a_producto(self) -> None:
        id_rec = self.recipe_repo.asociar_insumo_a_producto(self.id_prod, self.id_ins1, 0.25)
        self.assertGreater(id_rec, 0)

        recetas = self.recipe_repo.obtener_receta_por_producto(self.id_prod)
        self.assertEqual(len(recetas), 1)
        self.assertEqual(recetas[0].id_insumo, self.id_ins1)
        self.assertEqual(recetas[0].cantidad_necesaria, 0.25)

    def test_asociar_mismo_insumo_actualiza_cantidad(self) -> None:
        id_1 = self.recipe_repo.asociar_insumo_a_producto(self.id_prod, self.id_ins1, 0.25)
        id_2 = self.recipe_repo.asociar_insumo_a_producto(self.id_prod, self.id_ins1, 0.50)
        self.assertEqual(id_1, id_2)

        recetas = self.recipe_repo.obtener_receta_por_producto(self.id_prod)
        self.assertEqual(len(recetas), 1)
        self.assertEqual(recetas[0].cantidad_necesaria, 0.50)

    def test_eliminar_insumo_de_receta(self) -> None:
        id_rec = self.recipe_repo.asociar_insumo_a_producto(self.id_prod, self.id_ins1, 0.25)
        self.assertTrue(self.recipe_repo.eliminar_insumo_de_receta(id_rec))
        self.assertEqual(len(self.recipe_repo.obtener_receta_por_producto(self.id_prod)), 0)

    def test_eliminar_receta_por_producto(self) -> None:
        self.recipe_repo.asociar_insumo_a_producto(self.id_prod, self.id_ins1, 0.25)
        self.recipe_repo.asociar_insumo_a_producto(self.id_prod, self.id_ins2, 0.05)
        self.assertEqual(len(self.recipe_repo.obtener_receta_por_producto(self.id_prod)), 2)

        self.assertTrue(self.recipe_repo.eliminar_receta_por_producto(self.id_prod))
        self.assertEqual(len(self.recipe_repo.obtener_receta_por_producto(self.id_prod)), 0)


class TestInventoryService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_inv_svc.db"
        inicializar_base_de_datos(self.db_path)
        self.sup_repo = SupplyRepository(db_path=self.db_path)
        self.rec_repo = RecipeRepository(db_path=self.db_path)
        self.prod_repo = ProductRepository(db_path=self.db_path)
        self.service = InventoryService(
            supply_repository=self.sup_repo,
            recipe_repository=self.rec_repo,
            product_repository=self.prod_repo,
            db_path=self.db_path,
        )
        self.admin = Usuario(id_usuario=1, username="admin", nombre="Admin", id_rol=1, estado=1)
        self.empleado = Usuario(id_usuario=2, username="empleado", nombre="Empleado", id_rol=2, estado=1)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_admin_puede_crear_insumo(self) -> None:
        ins = self.service.crear_insumo(self.admin, "Base Helado", "Litros", 40.0, 10.0)
        self.assertIsNotNone(ins.id_insumo)
        self.assertEqual(ins.nombre, "Base Helado")

    def test_empleado_rechazado_crear_insumo(self) -> None:
        with self.assertRaises(AutorizacionError):
            self.service.crear_insumo(self.empleado, "Sin Permiso", "Kg", 10.0, 2.0)

    def test_crear_insumo_duplicado(self) -> None:
        self.service.crear_insumo(self.admin, "Mora", "Kg", 5.0, 1.0)
        with self.assertRaises(ValidacionError):
            self.service.crear_insumo(self.admin, "mora", "Kg", 10.0, 2.0)

    def test_actualizar_insumo(self) -> None:
        ins = self.service.crear_insumo(self.admin, "Arequipe", "Kg", 15.0, 3.0)
        actualizado = self.service.actualizar_insumo(self.admin, ins.id_insumo, "Dulce de Leche", "Kg", 5.0)
        self.assertEqual(actualizado.nombre, "Dulce de Leche")
        self.assertEqual(actualizado.stock_minimo, 5.0)

    def test_reabastecer_stock(self) -> None:
        ins = self.service.crear_insumo(self.admin, "Chispas", "Kg", 5.0, 1.0)
        self.assertTrue(self.service.reabastecer_stock(self.admin, ins.id_insumo, 10.0))
        recuperado = self.service.obtener_insumo_por_id(ins.id_insumo)
        self.assertEqual(recuperado.stock_actual, 15.0)

    def test_descontar_stock_exitoso(self) -> None:
        ins = self.service.crear_insumo(self.admin, "Conos Vacíos", "Unidades", 100.0, 20.0)
        self.assertTrue(self.service.descontar_stock(self.admin, ins.id_insumo, 25.0))
        recuperado = self.service.obtener_insumo_por_id(ins.id_insumo)
        self.assertEqual(recuperado.stock_actual, 75.0)

    def test_descontar_stock_insuficiente(self) -> None:
        ins = self.service.crear_insumo(self.admin, "Vasos", "Unidades", 10.0, 5.0)
        with self.assertRaises(StockInsuficienteError):
            self.service.descontar_stock(self.admin, ins.id_insumo, 20.0)

    def test_obtener_alertas_stock(self) -> None:
        self.service.crear_insumo(self.admin, "Insumo Critico", "Kg", 2.0, 5.0)
        self.service.crear_insumo(self.admin, "Insumo Normal", "Kg", 20.0, 5.0)
        alertas = self.service.obtener_alertas_stock()
        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0].nombre, "Insumo Critico")

    def test_asociar_receta_a_producto(self) -> None:
        id_prod = self.prod_repo.crear_producto(
            Producto(codigo="P-REC", nombre="Copa Helada", precio_venta=5000.0, id_categoria=1)
        )
        ins = self.service.crear_insumo(self.admin, "Topping Maní", "Gramos", 500.0, 50.0)

        id_rec = self.service.asociar_insumo_a_producto(self.admin, id_prod, ins.id_insumo, 30.0)
        self.assertGreater(id_rec, 0)

        recetas = self.service.obtener_receta_por_producto(id_prod)
        self.assertEqual(len(recetas), 1)
        self.assertEqual(recetas[0].cantidad_necesaria, 30.0)

    def test_asociar_receta_producto_inexistente(self) -> None:
        ins = self.service.crear_insumo(self.admin, "Insumo X", "Kg", 10.0, 1.0)
        with self.assertRaises(ValidacionError):
            self.service.asociar_insumo_a_producto(self.admin, 9999, ins.id_insumo, 1.0)

    def test_asociar_receta_insumo_inexistente(self) -> None:
        id_prod = self.prod_repo.crear_producto(
            Producto(codigo="P-Y", nombre="Prod Y", precio_venta=1000.0, id_categoria=1)
        )
        with self.assertRaises(ValidacionError):
            self.service.asociar_insumo_a_producto(self.admin, id_prod, 9999, 1.0)

    def test_eliminar_insumo_de_receta(self) -> None:
        id_prod = self.prod_repo.crear_producto(
            Producto(codigo="P-DEL", nombre="Prod Del", precio_venta=2000.0, id_categoria=1)
        )
        ins = self.service.crear_insumo(self.admin, "Insumo Del", "Kg", 10.0, 1.0)
        id_rec = self.service.asociar_insumo_a_producto(self.admin, id_prod, ins.id_insumo, 2.0)

        self.assertTrue(self.service.eliminar_insumo_de_receta(self.admin, id_rec))
        self.assertEqual(len(self.service.obtener_receta_por_producto(id_prod)), 0)


if __name__ == "__main__":
    unittest.main()
