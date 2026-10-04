from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import AutorizacionError, StockInsuficienteError, ValidacionError
from src.domain.loss import Merma
from src.domain.supply import Insumo
from src.domain.user import Usuario
from src.repositories.loss_repository import LossRepository
from src.repositories.supply_repository import SupplyRepository
from src.repositories.user_repository import UserRepository
from src.services.loss_service import LossService


class TestLossRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_loss_repo.db"
        inicializar_base_de_datos(self.db_path)
        self.sup_repo = SupplyRepository(db_path=self.db_path)
        self.loss_repo = LossRepository(db_path=self.db_path)
        self.id_insumo = self.sup_repo.crear_insumo(
            Insumo(nombre="Fresa", unidad_medida="Kg", stock_actual=20.0, stock_minimo=2.0)
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_registrar_y_obtener_merma(self) -> None:
        merma = Merma(
            id_insumo=self.id_insumo,
            cantidad=2.5,
            motivo="Fruta descompuesta por corte de energía",
            fecha_hora="2026-10-03 12:00:00",
            id_usuario=1,
        )
        id_merma = self.loss_repo.registrar_merma(merma)
        self.assertGreater(id_merma, 0)

        recuperada = self.loss_repo.obtener_por_id(id_merma)
        self.assertIsNotNone(recuperada)
        self.assertEqual(recuperada.id_insumo, self.id_insumo)
        self.assertEqual(recuperada.cantidad, 2.5)
        self.assertEqual(recuperada.motivo, "Fruta descompuesta por corte de energía")

    def test_listar_mermas(self) -> None:
        id_ins2 = self.sup_repo.crear_insumo(
            Insumo(nombre="Leche", unidad_medida="L", stock_actual=10.0, stock_minimo=1.0)
        )
        m1 = Merma(id_insumo=self.id_insumo, cantidad=1.0, motivo="Vencimiento", fecha_hora="2026-10-03 10:00:00", id_usuario=1)
        m2 = Merma(id_insumo=id_ins2, cantidad=2.0, motivo="Derrame", fecha_hora="2026-10-03 11:00:00", id_usuario=1)
        self.loss_repo.registrar_merma(m1)
        self.loss_repo.registrar_merma(m2)

        todas = self.loss_repo.listar_mermas()
        self.assertEqual(len(todas), 2)

        filtradas = self.loss_repo.listar_mermas(id_insumo=self.id_insumo)
        self.assertEqual(len(filtradas), 1)
        self.assertEqual(filtradas[0].motivo, "Vencimiento")


class TestLossService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_loss_svc.db"
        inicializar_base_de_datos(self.db_path)
        self.sup_repo = SupplyRepository(db_path=self.db_path)
        self.loss_repo = LossRepository(db_path=self.db_path)
        self.user_repo = UserRepository(db_path=self.db_path)
        self.service = LossService(
            loss_repository=self.loss_repo,
            supply_repository=self.sup_repo,
            db_path=self.db_path,
        )
        self.admin = self.user_repo.obtener_por_id(1)

        emp = Usuario(nombre="Empleado", username="empleado", password_hash="$2b$12$e1nKqYF6B8rG2I0wNu1dTuwR1iWdK3aB7T/Y4B5YdCqD8E6F7G8H9", id_rol=2, estado=1)
        id_emp = self.user_repo.crear_usuario(emp)
        self.empleado = self.user_repo.obtener_por_id(id_emp)

        inac = Usuario(nombre="Inactivo", username="inactivo", password_hash="$2b$12$e1nKqYF6B8rG2I0wNu1dTuwR1iWdK3aB7T/Y4B5YdCqD8E6F7G8H9", id_rol=2, estado=0)
        id_inac = self.user_repo.crear_usuario(inac)
        self.inactivo = self.user_repo.obtener_por_id(id_inac)

        self.id_insumo = self.sup_repo.crear_insumo(
            Insumo(nombre="Crema Chantilly", unidad_medida="Litros", stock_actual=15.0, stock_minimo=3.0)
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_admin_puede_registrar_merma(self) -> None:
        merma = self.service.registrar_merma(self.admin, self.id_insumo, 2.0, "Envase dañado")
        self.assertIsNotNone(merma.id_merma)
        self.assertEqual(merma.cantidad, 2.0)
        self.assertEqual(merma.motivo, "Envase dañado")

    def test_empleado_puede_registrar_merma(self) -> None:
        merma = self.service.registrar_merma(self.empleado, self.id_insumo, 1.0, "Derrame accidental en mostrador")
        self.assertIsNotNone(merma.id_merma)
        self.assertEqual(merma.id_usuario, self.empleado.id_usuario)

    def test_usuario_inactivo_rechazado(self) -> None:
        with self.assertRaises(AutorizacionError):
            self.service.registrar_merma(self.inactivo, self.id_insumo, 1.0, "Intento inactivo")

    def test_merma_descuenta_stock_inmediatamente(self) -> None:
        self.service.registrar_merma(self.admin, self.id_insumo, 5.0, "Prueba descuento")
        insumo = self.sup_repo.obtener_por_id(self.id_insumo)
        self.assertEqual(insumo.stock_actual, 10.0)

    def test_merma_excede_stock_insuficiente(self) -> None:
        with self.assertRaises(StockInsuficienteError):
            self.service.registrar_merma(self.admin, self.id_insumo, 25.0, "Mayor al stock disponible")

        insumo = self.sup_repo.obtener_por_id(self.id_insumo)
        self.assertEqual(insumo.stock_actual, 15.0)

    def test_merma_cantidad_cero_invalida(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.registrar_merma(self.admin, self.id_insumo, 0.0, "Cantidad cero")

    def test_merma_cantidad_negativa_invalida(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.registrar_merma(self.admin, self.id_insumo, -2.0, "Cantidad negativa")

    def test_merma_motivo_vacio_invalido(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.registrar_merma(self.admin, self.id_insumo, 1.0, "   ")

    def test_merma_insumo_inexistente(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.registrar_merma(self.admin, 9999, 1.0, "Insumo fantasma")

    def test_listar_mermas(self) -> None:
        self.service.registrar_merma(self.admin, self.id_insumo, 1.0, "Motivo 1")
        self.service.registrar_merma(self.empleado, self.id_insumo, 2.0, "Motivo 2")
        lista = self.service.listar_mermas(self.id_insumo)
        self.assertEqual(len(lista), 2)


if __name__ == "__main__":
    unittest.main()
