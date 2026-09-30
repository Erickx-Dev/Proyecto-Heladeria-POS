from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.connection import get_db_cursor, get_db_transaction
from database.migrations import inicializar_base_de_datos
from src.core.exceptions import AutenticacionError, ValidacionError
from src.core.security import hash_password
from src.domain.user import Usuario
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService


class TestAuthService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_auth.db"
        inicializar_base_de_datos(self.db_path)
        self.repo = UserRepository(db_path=self.db_path)
        self.auth = AuthService(user_repository=self.repo, db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_autenticacion_exitosa_admin(self) -> None:
        usuario = self.auth.autenticar("admin", "admin123")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.username, "admin")
        self.assertEqual(usuario.id_rol, 1)
        self.assertTrue(usuario.es_administrador())

    def test_usuario_actual_tras_login(self) -> None:
        self.assertIsNone(self.auth.obtener_usuario_actual())
        self.auth.autenticar("admin", "admin123")
        actual = self.auth.obtener_usuario_actual()
        self.assertIsNotNone(actual)
        self.assertEqual(actual.username, "admin")

    def test_autenticacion_usuario_inexistente(self) -> None:
        with self.assertRaises(AutenticacionError):
            self.auth.autenticar("fantasma", "cualquier_clave")

    def test_autenticacion_password_incorrecta(self) -> None:
        with self.assertRaises(AutenticacionError):
            self.auth.autenticar("admin", "clave_erronea")

    def test_autenticacion_usuario_inactivo(self) -> None:
        self.repo.cambiar_estado(1, 0)
        with self.assertRaises(AutenticacionError) as ctx:
            self.auth.autenticar("admin", "admin123")
        self.assertIn("inactivo", ctx.exception.mensaje.lower())

    def test_autenticacion_username_vacio(self) -> None:
        with self.assertRaises(ValidacionError):
            self.auth.autenticar("", "clave")

    def test_autenticacion_password_vacia(self) -> None:
        with self.assertRaises(ValidacionError):
            self.auth.autenticar("admin", "")

    def test_cerrar_sesion(self) -> None:
        self.auth.autenticar("admin", "admin123")
        self.assertIsNotNone(self.auth.obtener_usuario_actual())
        self.auth.cerrar_sesion()
        self.assertIsNone(self.auth.obtener_usuario_actual())

    def test_cerrar_sesion_sin_usuario_no_falla(self) -> None:
        self.auth.cerrar_sesion()
        self.assertIsNone(self.auth.obtener_usuario_actual())

    def test_auditoria_login_exitoso(self) -> None:
        self.auth.autenticar("admin", "admin123")
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(
                "SELECT accion, modulo, detalles FROM AuditoriaLog "
                "WHERE accion = 'LOGIN_EXITOSO' ORDER BY id_log DESC LIMIT 1;",
            )
            log = cursor.fetchone()
            self.assertIsNotNone(log)
            self.assertEqual(log["accion"], "LOGIN_EXITOSO")
            self.assertEqual(log["modulo"], "AUTH")

    def test_auditoria_login_fallido_password(self) -> None:
        with self.assertRaises(AutenticacionError):
            self.auth.autenticar("admin", "clave_erronea")

        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(
                "SELECT accion, modulo FROM AuditoriaLog "
                "WHERE accion = 'LOGIN_FALLIDO' ORDER BY id_log DESC LIMIT 1;",
            )
            log = cursor.fetchone()
            self.assertIsNotNone(log)
            self.assertEqual(log["accion"], "LOGIN_FALLIDO")

    def test_auditoria_login_fallido_inexistente(self) -> None:
        with self.assertRaises(AutenticacionError):
            self.auth.autenticar("no_existe", "clave")

        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(
                "SELECT accion, detalles FROM AuditoriaLog "
                "WHERE accion = 'LOGIN_FALLIDO' ORDER BY id_log DESC LIMIT 1;",
            )
            log = cursor.fetchone()
            self.assertIsNotNone(log)
            self.assertIn("inexistente", log["detalles"])

    def test_auditoria_logout(self) -> None:
        self.auth.autenticar("admin", "admin123")
        self.auth.cerrar_sesion()

        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(
                "SELECT accion, modulo FROM AuditoriaLog "
                "WHERE accion = 'LOGOUT' ORDER BY id_log DESC LIMIT 1;",
            )
            log = cursor.fetchone()
            self.assertIsNotNone(log)
            self.assertEqual(log["accion"], "LOGOUT")

    def test_autenticacion_empleado(self) -> None:
        nuevo_hash = hash_password("empleado_clave")
        empleado = Usuario(
            nombre="Pedro Cajero",
            username="pedro_cajero",
            password_hash=nuevo_hash,
            id_rol=2,
            estado=1,
        )
        self.repo.crear_usuario(empleado)

        usuario = self.auth.autenticar("pedro_cajero", "empleado_clave")
        self.assertFalse(usuario.es_administrador())
        self.assertTrue(usuario.es_activo())


if __name__ == "__main__":
    unittest.main()
