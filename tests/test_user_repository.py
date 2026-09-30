from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import ValidacionError
from src.core.security import hash_password
from src.domain.user import Usuario
from src.repositories.user_repository import UserRepository


class TestUserRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_users.db"
        inicializar_base_de_datos(self.db_path)
        self.repo = UserRepository(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_obtener_usuario_admin_semilla(self) -> None:
        admin = self.repo.obtener_por_username("admin")
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, "admin")
        self.assertEqual(admin.id_rol, 1)
        self.assertEqual(admin.estado, 1)

    def test_obtener_por_id_existente(self) -> None:
        admin = self.repo.obtener_por_id(1)
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, "admin")

    def test_obtener_por_id_inexistente(self) -> None:
        resultado = self.repo.obtener_por_id(9999)
        self.assertIsNone(resultado)

    def test_obtener_por_username_inexistente(self) -> None:
        resultado = self.repo.obtener_por_username("fantasma")
        self.assertIsNone(resultado)

    def test_crear_usuario_exitoso(self) -> None:
        nuevo_hash = hash_password("clave_segura_2026")
        nuevo = Usuario(
            nombre="María Cajera",
            username="maria_cajera",
            password_hash=nuevo_hash,
            id_rol=2,
            estado=1,
        )
        id_creado = self.repo.crear_usuario(nuevo)
        self.assertIsInstance(id_creado, int)
        self.assertGreater(id_creado, 0)

        recuperado = self.repo.obtener_por_id(id_creado)
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.nombre, "María Cajera")
        self.assertEqual(recuperado.username, "maria_cajera")

    def test_crear_usuario_username_duplicado(self) -> None:
        hash_val = hash_password("clave123")
        duplicado = Usuario(
            nombre="Admin Duplicado",
            username="admin",
            password_hash=hash_val,
            id_rol=1,
            estado=1,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.crear_usuario(duplicado)

    def test_actualizar_usuario(self) -> None:
        admin = self.repo.obtener_por_id(1)
        admin.nombre = "Administrador Actualizado"
        resultado = self.repo.actualizar_usuario(admin)
        self.assertTrue(resultado)

        actualizado = self.repo.obtener_por_id(1)
        self.assertEqual(actualizado.nombre, "Administrador Actualizado")

    def test_actualizar_sin_id_lanza_error(self) -> None:
        usuario = Usuario(nombre="Sin ID", username="sinid", password_hash="a" * 60)
        with self.assertRaises(ValidacionError):
            self.repo.actualizar_usuario(usuario)

    def test_cambiar_password(self) -> None:
        nuevo_hash = hash_password("nueva_clave_admin")
        resultado = self.repo.cambiar_password(1, nuevo_hash)
        self.assertTrue(resultado)

        admin = self.repo.obtener_por_id(1)
        self.assertEqual(admin.password_hash, nuevo_hash)

    def test_cambiar_password_hash_invalido(self) -> None:
        with self.assertRaises(ValidacionError):
            self.repo.cambiar_password(1, "hash_corto")

    def test_cambiar_estado(self) -> None:
        resultado = self.repo.cambiar_estado(1, 0)
        self.assertTrue(resultado)

        admin = self.repo.obtener_por_id(1)
        self.assertEqual(admin.estado, 0)

    def test_cambiar_estado_invalido(self) -> None:
        with self.assertRaises(ValidacionError):
            self.repo.cambiar_estado(1, 5)

    def test_listar_usuarios_todos(self) -> None:
        usuarios = self.repo.listar_usuarios()
        self.assertGreaterEqual(len(usuarios), 1)

    def test_listar_usuarios_solo_activos(self) -> None:
        hash_val = hash_password("clave_inactivo")
        inactivo = Usuario(
            nombre="Empleado Inactivo",
            username="inactivo01",
            password_hash=hash_val,
            id_rol=2,
            estado=0,
        )
        self.repo.crear_usuario(inactivo)

        todos = self.repo.listar_usuarios(solo_activos=False)
        activos = self.repo.listar_usuarios(solo_activos=True)
        self.assertGreater(len(todos), len(activos))


if __name__ == "__main__":
    unittest.main()
