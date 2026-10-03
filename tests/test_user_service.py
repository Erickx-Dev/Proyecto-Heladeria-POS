from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.connection import get_db_cursor
from database.migrations import inicializar_base_de_datos
from src.core.exceptions import AutorizacionError, ValidacionError
from src.core.security import hash_password
from src.domain.user import Permiso, Usuario
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService


class TestUserService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_user_service.db"
        inicializar_base_de_datos(self.db_path)
        self.repo = UserRepository(db_path=self.db_path)
        self.service = UserService(user_repository=self.repo, db_path=self.db_path)
        self.admin = self.repo.obtener_por_username("admin")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _crear_empleado(self, username: str = "empleado1") -> Usuario:
        return self.service.crear_usuario(
            autor=self.admin,
            nombre="Empleado de Prueba",
            username=username,
            password_plana="clave123segura",
            id_rol=2,
        )

    def test_crear_usuario_exitoso_por_admin(self) -> None:
        nuevo = self.service.crear_usuario(
            autor=self.admin,
            nombre="Carlos López",
            username="carlos",
            password_plana="password123",
            id_rol=2,
        )
        self.assertIsNotNone(nuevo.id_usuario)
        self.assertEqual(nuevo.nombre, "Carlos López")
        self.assertEqual(nuevo.username, "carlos")
        self.assertEqual(nuevo.id_rol, 2)
        self.assertEqual(nuevo.estado, 1)

    def test_crear_usuario_admin_por_admin(self) -> None:
        nuevo = self.service.crear_usuario(
            autor=self.admin,
            nombre="Segundo Admin",
            username="admin2",
            password_plana="password123",
            id_rol=1,
        )
        self.assertEqual(nuevo.id_rol, 1)
        self.assertTrue(nuevo.es_administrador())

    def test_crear_usuario_rechazado_por_empleado_sin_permiso(self) -> None:
        empleado = self._crear_empleado()
        with self.assertRaises(AutorizacionError):
            self.service.crear_usuario(
                autor=empleado,
                nombre="Intruso",
                username="intruso",
                password_plana="password123",
                id_rol=2,
            )

    def test_crear_usuario_username_duplicado(self) -> None:
        self._crear_empleado("duplicado")
        with self.assertRaises(ValidacionError) as ctx:
            self.service.crear_usuario(
                autor=self.admin,
                nombre="Otro",
                username="duplicado",
                password_plana="password123",
                id_rol=2,
            )
        self.assertIn("ya está en uso", ctx.exception.mensaje)

    def test_crear_usuario_password_corta(self) -> None:
        with self.assertRaises(ValidacionError) as ctx:
            self.service.crear_usuario(
                autor=self.admin,
                nombre="Corto",
                username="corto",
                password_plana="abc",
                id_rol=2,
            )
        self.assertIn("al menos", ctx.exception.mensaje)

    def test_crear_usuario_nombre_vacio(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.crear_usuario(
                autor=self.admin,
                nombre="",
                username="vacio",
                password_plana="password123",
                id_rol=2,
            )

    def test_crear_usuario_username_corto(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.crear_usuario(
                autor=self.admin,
                nombre="Nombre Válido",
                username="ab",
                password_plana="password123",
                id_rol=2,
            )

    def test_crear_usuario_rol_invalido(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.crear_usuario(
                autor=self.admin,
                nombre="Nombre Válido",
                username="rolmal",
                password_plana="password123",
                id_rol=99,
            )

    def test_actualizar_usuario_exitoso(self) -> None:
        empleado = self._crear_empleado()
        actualizado = self.service.actualizar_usuario(
            autor=self.admin,
            id_usuario=empleado.id_usuario,
            nombre="Nombre Actualizado",
            id_rol=2,
            estado=1,
        )
        self.assertEqual(actualizado.nombre, "Nombre Actualizado")

    def test_actualizar_usuario_sin_permisos(self) -> None:
        empleado = self._crear_empleado()
        with self.assertRaises(AutorizacionError):
            self.service.actualizar_usuario(
                autor=empleado,
                id_usuario=self.admin.id_usuario,
                nombre="Hackeado",
                id_rol=1,
                estado=1,
            )

    def test_actualizar_usuario_inexistente(self) -> None:
        with self.assertRaises(ValidacionError) as ctx:
            self.service.actualizar_usuario(
                autor=self.admin,
                id_usuario=9999,
                nombre="Fantasma",
                id_rol=2,
                estado=1,
            )
        self.assertIn("no existe", ctx.exception.mensaje)

    def test_impedir_desactivar_ultimo_administrador(self) -> None:
        with self.assertRaises(ValidacionError) as ctx:
            self.service.actualizar_usuario(
                autor=self.admin,
                id_usuario=self.admin.id_usuario,
                nombre=self.admin.nombre,
                id_rol=1,
                estado=0,
            )
        self.assertIn("único administrador", ctx.exception.mensaje)

    def test_impedir_degradar_ultimo_administrador(self) -> None:
        with self.assertRaises(ValidacionError) as ctx:
            self.service.actualizar_usuario(
                autor=self.admin,
                id_usuario=self.admin.id_usuario,
                nombre=self.admin.nombre,
                id_rol=2,
                estado=1,
            )
        self.assertIn("único administrador", ctx.exception.mensaje)

    def test_permitir_degradar_admin_si_hay_otro(self) -> None:
        self.service.crear_usuario(
            autor=self.admin,
            nombre="Admin Respaldo",
            username="admin_respaldo",
            password_plana="password123",
            id_rol=1,
        )
        resultado = self.service.actualizar_usuario(
            autor=self.admin,
            id_usuario=self.admin.id_usuario,
            nombre=self.admin.nombre,
            id_rol=2,
            estado=1,
        )
        self.assertEqual(resultado.id_rol, 2)

    def test_cambiar_password_por_admin(self) -> None:
        empleado = self._crear_empleado()
        resultado = self.service.cambiar_password(
            autor=self.admin,
            id_usuario=empleado.id_usuario,
            nueva_password_plana="nueva_clave_segura",
        )
        self.assertTrue(resultado)

    def test_cambiar_password_propia_por_empleado(self) -> None:
        empleado = self._crear_empleado()
        resultado = self.service.cambiar_password(
            autor=empleado,
            id_usuario=empleado.id_usuario,
            nueva_password_plana="mi_nueva_clave",
        )
        self.assertTrue(resultado)

    def test_cambiar_password_ajena_por_empleado_rechazado(self) -> None:
        empleado = self._crear_empleado()
        with self.assertRaises(AutorizacionError):
            self.service.cambiar_password(
                autor=empleado,
                id_usuario=self.admin.id_usuario,
                nueva_password_plana="intento_hackeo",
            )

    def test_cambiar_password_corta(self) -> None:
        empleado = self._crear_empleado()
        with self.assertRaises(ValidacionError):
            self.service.cambiar_password(
                autor=self.admin,
                id_usuario=empleado.id_usuario,
                nueva_password_plana="abc",
            )

    def test_cambiar_password_usuario_inexistente(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.cambiar_password(
                autor=self.admin,
                id_usuario=9999,
                nueva_password_plana="password123",
            )

    def test_cambiar_estado_usuario(self) -> None:
        empleado = self._crear_empleado()
        resultado = self.service.cambiar_estado(
            autor=self.admin,
            id_usuario=empleado.id_usuario,
            nuevo_estado=0,
        )
        self.assertTrue(resultado)
        desactivado = self.service.obtener_por_id(empleado.id_usuario)
        self.assertEqual(desactivado.estado, 0)

    def test_cambiar_estado_sin_permisos(self) -> None:
        empleado = self._crear_empleado()
        with self.assertRaises(AutorizacionError):
            self.service.cambiar_estado(
                autor=empleado,
                id_usuario=self.admin.id_usuario,
                nuevo_estado=0,
            )

    def test_cambiar_estado_ultimo_admin_bloqueado(self) -> None:
        with self.assertRaises(ValidacionError):
            self.service.cambiar_estado(
                autor=self.admin,
                id_usuario=self.admin.id_usuario,
                nuevo_estado=0,
            )

    def test_cambiar_estado_invalido(self) -> None:
        empleado = self._crear_empleado()
        with self.assertRaises(ValidacionError):
            self.service.cambiar_estado(
                autor=self.admin,
                id_usuario=empleado.id_usuario,
                nuevo_estado=5,
            )

    def test_listar_usuarios_todos(self) -> None:
        self._crear_empleado("emp1")
        self._crear_empleado("emp2")
        todos = self.service.listar_usuarios(solo_activos=False)
        self.assertGreaterEqual(len(todos), 3)

    def test_listar_usuarios_solo_activos(self) -> None:
        empleado = self._crear_empleado()
        self.service.cambiar_estado(
            autor=self.admin,
            id_usuario=empleado.id_usuario,
            nuevo_estado=0,
        )
        activos = self.service.listar_usuarios(solo_activos=True)
        ids_activos = [u.id_usuario for u in activos]
        self.assertNotIn(empleado.id_usuario, ids_activos)

    def test_obtener_por_id(self) -> None:
        empleado = self._crear_empleado()
        recuperado = self.service.obtener_por_id(empleado.id_usuario)
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.username, "empleado1")

    def test_obtener_por_username(self) -> None:
        self._crear_empleado("buscar_user")
        recuperado = self.service.obtener_por_username("buscar_user")
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.nombre, "Empleado de Prueba")

    def test_obtener_por_id_inexistente(self) -> None:
        resultado = self.service.obtener_por_id(9999)
        self.assertIsNone(resultado)


class TestPermisosPorRol(unittest.TestCase):

    def test_admin_tiene_todos_los_permisos(self) -> None:
        admin = Usuario(
            id_usuario=1,
            nombre="Admin",
            username="admin",
            password_hash="x" * 60,
            id_rol=1,
            estado=1,
        )
        for permiso in Permiso:
            self.assertTrue(admin.has_permission(permiso))

    def test_empleado_tiene_permisos_basicos(self) -> None:
        empleado = Usuario(
            id_usuario=2,
            nombre="Empleado",
            username="emp",
            password_hash="x" * 60,
            id_rol=2,
            estado=1,
        )
        self.assertTrue(empleado.has_permission(Permiso.VENTAS))
        self.assertTrue(empleado.has_permission(Permiso.CAJA))
        self.assertTrue(empleado.has_permission(Permiso.GASTOS))
        self.assertTrue(empleado.has_permission(Permiso.MERMAS))

    def test_empleado_no_tiene_permisos_administrativos(self) -> None:
        empleado = Usuario(
            id_usuario=2,
            nombre="Empleado",
            username="emp",
            password_hash="x" * 60,
            id_rol=2,
            estado=1,
        )
        self.assertFalse(empleado.has_permission(Permiso.GESTIONAR_USUARIOS))
        self.assertFalse(empleado.has_permission(Permiso.REPORTES))
        self.assertFalse(empleado.has_permission(Permiso.AUDITORIA))
        self.assertFalse(empleado.has_permission(Permiso.BACKUP))
        self.assertFalse(empleado.has_permission(Permiso.CATALOGO))
        self.assertFalse(empleado.has_permission(Permiso.INVENTARIO))

    def test_usuario_inactivo_no_tiene_permisos(self) -> None:
        admin_inactivo = Usuario(
            id_usuario=1,
            nombre="Admin Inactivo",
            username="admin_off",
            password_hash="x" * 60,
            id_rol=1,
            estado=0,
        )
        for permiso in Permiso:
            self.assertFalse(admin_inactivo.has_permission(permiso))

    def test_tiene_permiso_alias_consistente(self) -> None:
        admin = Usuario(
            id_usuario=1,
            nombre="Admin",
            username="admin",
            password_hash="x" * 60,
            id_rol=1,
            estado=1,
        )
        for permiso in Permiso:
            self.assertEqual(
                admin.tiene_permiso(permiso),
                admin.has_permission(permiso),
            )


class TestAuditoriaUserService(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_audit_user.db"
        inicializar_base_de_datos(self.db_path)
        self.repo = UserRepository(db_path=self.db_path)
        self.service = UserService(user_repository=self.repo, db_path=self.db_path)
        self.admin = self.repo.obtener_por_username("admin")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _contar_logs_auditoria(self, modulo: str = "USUARIOS") -> int:
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM AuditoriaLog WHERE modulo = ?;",
                (modulo,),
            )
            return cursor.fetchone()[0]

    def test_auditoria_al_crear_usuario(self) -> None:
        antes = self._contar_logs_auditoria()
        self.service.crear_usuario(
            autor=self.admin,
            nombre="Auditado",
            username="auditado",
            password_plana="password123",
            id_rol=2,
        )
        despues = self._contar_logs_auditoria()
        self.assertGreater(despues, antes)

    def test_auditoria_al_actualizar_usuario(self) -> None:
        empleado = self.service.crear_usuario(
            autor=self.admin,
            nombre="Para Actualizar",
            username="actualizar",
            password_plana="password123",
            id_rol=2,
        )
        antes = self._contar_logs_auditoria()
        self.service.actualizar_usuario(
            autor=self.admin,
            id_usuario=empleado.id_usuario,
            nombre="Actualizado",
            id_rol=2,
            estado=1,
        )
        despues = self._contar_logs_auditoria()
        self.assertGreater(despues, antes)

    def test_auditoria_al_cambiar_password(self) -> None:
        empleado = self.service.crear_usuario(
            autor=self.admin,
            nombre="Para Password",
            username="password_test",
            password_plana="password123",
            id_rol=2,
        )
        antes = self._contar_logs_auditoria()
        self.service.cambiar_password(
            autor=self.admin,
            id_usuario=empleado.id_usuario,
            nueva_password_plana="nueva_segura_123",
        )
        despues = self._contar_logs_auditoria()
        self.assertGreater(despues, antes)

    def test_auditoria_al_cambiar_estado(self) -> None:
        empleado = self.service.crear_usuario(
            autor=self.admin,
            nombre="Para Estado",
            username="estado_test",
            password_plana="password123",
            id_rol=2,
        )
        antes = self._contar_logs_auditoria()
        self.service.cambiar_estado(
            autor=self.admin,
            id_usuario=empleado.id_usuario,
            nuevo_estado=0,
        )
        despues = self._contar_logs_auditoria()
        self.assertGreater(despues, antes)


if __name__ == "__main__":
    unittest.main()
