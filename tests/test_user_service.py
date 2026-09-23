from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.core.exceptions import (
    CredencialInvalidaError,
    ReglaNegocioError,
    RolInvalidoError,
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
)
from src.domain.user import Administrador, Empleado
from src.services.auth_service import AuthService
from src.services.user_service import UserService


class TestUserService(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_rf13.db"
        inicializar_base_de_datos(self.db_path)
        self.user_service = UserService(db_path=self.db_path)
        self.auth_service = AuthService(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_crear_usuario_empleado_y_administrador_exitoso(self) -> None:
        emp = self.user_service.crear_usuario(
            nombre="Laura Gómez",
            username="laurag",
            password="password123",
            id_rol=2,
            id_operador=1,
        )
        self.assertIsInstance(emp, Empleado)
        self.assertEqual(emp.nombre, "Laura Gómez")
        self.assertEqual(emp.username, "laurag")
        self.assertEqual(emp.id_rol, 2)
        self.assertFalse(emp.es_administrador())

        admin = self.user_service.crear_usuario(
            nombre="Carlos Ruiz",
            username="carlosr",
            password="adminpassword",
            id_rol=1,
            id_operador=1,
        )
        self.assertIsInstance(admin, Administrador)
        self.assertEqual(admin.id_rol, 1)
        self.assertTrue(admin.es_administrador())

    def test_crear_usuario_duplicado_lanza_excepcion(self) -> None:
        self.user_service.crear_usuario(
            nombre="Pedro Perez",
            username="pedrop",
            password="clave1234",
            id_rol=2,
        )
        with self.assertRaises(UsuarioDuplicadoError):
            self.user_service.crear_usuario(
                nombre="Otro Pedro",
                username="pedrop",
                password="otraclave1234",
                id_rol=2,
            )

    def test_crear_usuario_con_username_existente_admin_lanza_excepcion(self) -> None:
        with self.assertRaises(UsuarioDuplicadoError):
            self.user_service.crear_usuario(
                nombre="Nuevo Admin",
                username="admin",
                password="clave1234",
                id_rol=1,
            )

    def test_validaciones_de_formato_credenciales(self) -> None:
        with self.assertRaises(CredencialInvalidaError):
            self.user_service.crear_usuario(
                nombre="   ",
                username="user1",
                password="clave1234",
                id_rol=2,
            )

        with self.assertRaises(CredencialInvalidaError):
            self.user_service.crear_usuario(
                nombre="Valido",
                username="ab",
                password="clave1234",
                id_rol=2,
            )

        with self.assertRaises(CredencialInvalidaError):
            self.user_service.crear_usuario(
                nombre="Valido",
                username="usuario1",
                password="12",
                id_rol=2,
            )

    def test_rol_invalido_lanza_excepcion(self) -> None:
        with self.assertRaises(RolInvalidoError):
            self.user_service.crear_usuario(
                nombre="Test",
                username="testuser",
                password="clave1234",
                id_rol=99,
            )

    def test_modificar_password_exitoso(self) -> None:
        user = self.user_service.crear_usuario(
            nombre="Marta Sanchez",
            username="martas",
            password="claveOriginal1",
            id_rol=2,
        )

        modificado = self.user_service.modificar_password(user.id_usuario, "claveNueva99")
        self.assertTrue(modificado)

        auth_vieja = self.auth_service.autenticar("martas", "claveOriginal1")
        self.assertIsNone(auth_vieja)

        auth_nueva = self.auth_service.autenticar("martas", "claveNueva99")
        self.assertIsNotNone(auth_nueva)
        self.assertEqual(auth_nueva.id_usuario, user.id_usuario)

    def test_cambiar_estado_activar_desactivar(self) -> None:
        user = self.user_service.crear_usuario(
            nombre="Operador Caja",
            username="cajero1",
            password="cajeroPass1",
            id_rol=2,
            estado=1,
        )

        self.user_service.cambiar_estado(user.id_usuario, nuevo_estado=0, id_operador=1)
        actualizado = self.user_service.obtener_usuario_por_id(user.id_usuario)
        self.assertIsNotNone(actualizado)
        self.assertEqual(actualizado.estado, 0)
        self.assertFalse(actualizado.esta_activo())

        login_inactivo = self.auth_service.autenticar("cajero1", "cajeroPass1")
        self.assertIsNone(login_inactivo)

        self.user_service.cambiar_estado(user.id_usuario, nuevo_estado=1, id_operador=1)
        login_activo = self.auth_service.autenticar("cajero1", "cajeroPass1")
        self.assertIsNotNone(login_activo)

    def test_actualizar_datos_usuario(self) -> None:
        user = self.user_service.crear_usuario(
            nombre="Nombre Inicial",
            username="userinicial",
            password="clave1234",
            id_rol=2,
        )

        actualizado = self.user_service.actualizar_datos(
            id_usuario=user.id_usuario,
            nombre="Nombre Actualizado",
            username="usernuevo",
            id_rol=1,
            id_operador=1,
        )
        self.assertEqual(actualizado.nombre, "Nombre Actualizado")
        self.assertEqual(actualizado.username, "usernuevo")
        self.assertEqual(actualizado.id_rol, 1)
        self.assertTrue(actualizado.es_administrador())

    def test_actualizar_datos_con_username_duplicado_falla(self) -> None:
        self.user_service.crear_usuario(
            nombre="Usuario A",
            username="usera",
            password="clave1234",
            id_rol=2,
        )
        user_b = self.user_service.crear_usuario(
            nombre="Usuario B",
            username="userb",
            password="clave1234",
            id_rol=2,
        )
        with self.assertRaises(UsuarioDuplicadoError):
            self.user_service.actualizar_datos(
                id_usuario=user_b.id_usuario,
                username="usera",
            )

    def test_listar_usuarios_filtro_activos(self) -> None:
        self.user_service.crear_usuario("Activo 1", "activo1", "pass1234", id_rol=2, estado=1)
        self.user_service.crear_usuario("Inactivo 1", "inactivo1", "pass1234", id_rol=2, estado=0)

        todos = self.user_service.listar_usuarios(solo_activos=False)
        self.assertGreaterEqual(len(todos), 3)

        activos = self.user_service.listar_usuarios(solo_activos=True)
        for u in activos:
            self.assertEqual(u.estado, 1)

    def test_auditoria_registrada_para_operaciones(self) -> None:
        user = self.user_service.crear_usuario("Audit User", "auduser", "clave1234", id_rol=2, id_operador=1)
        self.user_service.modificar_password(user.id_usuario, "clave12345", id_operador=1)
        self.user_service.cambiar_estado(user.id_usuario, 0, id_operador=1)

        logs = self.user_service.audit_service.obtener_logs(limite=10, modulo="USUARIOS")
        acciones = [log.accion for log in logs]
        self.assertIn("USUARIO_CREADO", acciones)
        self.assertIn("PASSWORD_MODIFICADA", acciones)
        self.assertIn("USUARIO_DESACTIVADO", acciones)


if __name__ == "__main__":
    unittest.main()
