"""
Suite de Pruebas Unitarias para la Infraestructura de Persistencia (database/).

Verifica la correcta creación del esquema DDL, cumplimiento de claves foráneas,
restricciones CHECK, transacciones ACID y utilidades de respaldo.
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.connection import get_connection, get_db_cursor, get_db_transaction
from database.migrations import (
    TABLAS_REQUERIDAS,
    crear_respaldo_db,
    inicializar_base_de_datos,
    obtener_tablas_existentes,
    verificar_integridad_referencial,
)


class TestDatabaseInfrastructure(unittest.TestCase):
    def setUp(self) -> None:
        """Crea un archivo de base de datos temporal aislado para cada prueba."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_heladeria.db"
        inicializar_base_de_datos(self.db_path)

    def tearDown(self) -> None:
        """Limpia los archivos temporales."""
        self.temp_dir.cleanup()

    def test_todas_las_tablas_requeridas_existen(self) -> None:
        """Verifica que las 11 entidades relacionales existan en sqlite_master."""
        tablas = obtener_tablas_existentes(self.db_path)
        for tabla in TABLAS_REQUERIDAS:
            with self.subTest(tabla=tabla):
                self.assertIn(tabla, tablas, f"La tabla {tabla} debe existir en el esquema.")

    def test_datos_semilla_cargados_correctamente(self) -> None:
        """Verifica la carga de roles y el usuario administrador por defecto."""
        conn = get_connection(self.db_path)
        try:
            # Validar roles
            cursor = conn.cursor()
            cursor.execute("SELECT id_rol, nombre_rol FROM Rol ORDER BY id_rol ASC;")
            roles = cursor.fetchall()
            self.assertEqual(len(roles), 2)
            self.assertEqual(roles[0]["nombre_rol"], "Administrador")
            self.assertEqual(roles[1]["nombre_rol"], "Empleado")

            # Validar usuario admin
            cursor.execute("SELECT username, password_hash, id_rol, estado FROM Usuario WHERE username = 'admin';")
            admin = cursor.fetchone()
            self.assertIsNotNone(admin)
            self.assertEqual(admin["username"], "admin")
            self.assertEqual(
                admin["password_hash"],
                "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
            )
            self.assertEqual(admin["id_rol"], 1)
            self.assertEqual(admin["estado"], 1)
        finally:
            conn.close()

    def test_integridad_referencial_sin_violaciones_iniciales(self) -> None:
        """Comprueba que los datos iniciales no violen claves foráneas."""
        violaciones = verificar_integridad_referencial(self.db_path)
        self.assertEqual(len(violaciones), 0, "No debe haber violaciones de FK iniciales.")

    def test_claves_foraneas_activadas_y_restringidas(self) -> None:
        """Verifica que intentar insertar un registro con FK inexistente falle con IntegrityError."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            # Intentar insertar un usuario con id_rol = 999 (inexistente)
            with self.assertRaises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO Usuario (nombre, username, password_hash, id_rol, estado)
                    VALUES ('Usuario Prueba', 'test_user', 'a' * 64, 999, 1);
                    """
                )
        finally:
            conn.close()

    def test_restricciones_check_precios_y_cantidades(self) -> None:
        """Valida que los valores negativos sean rechazados por las restricciones CHECK."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            # Precio de producto negativo
            with self.assertRaises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO Producto (codigo, nombre, precio_venta, id_categoria, estado)
                    VALUES ('PROD-NEG', 'Helado Inválido', -15.0, 1, 1);
                    """
                )

            # Stock de insumo negativo
            with self.assertRaises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO Insumo (nombre, unidad_medida, stock_actual, stock_minimo)
                    VALUES ('Leche', 'Litros', -5.0, 10.0);
                    """
                )

            # Método de pago no permitido en Venta
            with self.assertRaises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO Venta (id_caja, fecha_hora, total, metodo_pago)
                    VALUES (1, '2026-09-16 12:00:00', 50.0, 'BITCOIN');
                    """
                )
        finally:
            conn.close()

    def test_transacciones_acid_commit_exitoso(self) -> None:
        """Verifica que las operaciones dentro de get_db_transaction se persistan correctamente."""
        with get_db_transaction(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO Insumo (nombre, unidad_medida, stock_actual, stock_minimo)
                VALUES ('Vainilla Esencia', 'ml', 500.0, 100.0);
                """
            )

        # Verificar lectura en una nueva conexión
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute("SELECT stock_actual FROM Insumo WHERE nombre = 'Vainilla Esencia';")
            fila = cursor.fetchone()
            self.assertIsNotNone(fila)
            self.assertEqual(fila["stock_actual"], 500.0)

    def test_transacciones_acid_rollback_ante_excepcion(self) -> None:
        """Verifica que una excepción dentro del bloque transaccional revierta todas las operaciones."""
        with self.assertRaises(ValueError):
            with get_db_transaction(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO Insumo (nombre, unidad_medida, stock_actual, stock_minimo)
                    VALUES ('Chocolate Amargo', 'kg', 20.0, 5.0);
                    """
                )
                # Forzar un error no controlado de Python
                raise ValueError("Falla forzada durante la transacción")

        # Verificar que el registro NO fue insertado (Rollback exitoso)
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute("SELECT id_insumo FROM Insumo WHERE nombre = 'Chocolate Amargo';")
            self.assertIsNone(cursor.fetchone(), "El rollback debe evitar que se persista el insumo.")

    def test_cascada_en_detalle_venta(self) -> None:
        """Verifica que eliminar una Venta elimine sus DetalleVenta asociados en cascada."""
        with get_db_transaction(self.db_path) as conn:
            # 1. Crear producto
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Producto (codigo, nombre, precio_venta, id_categoria) VALUES ('P1', 'Cono Simple', 25.0, 1);"
            )
            id_prod = cursor.lastrowid

            # 2. Crear turno de caja
            cursor.execute(
                "INSERT INTO Caja (id_usuario, fecha_apertura, monto_inicial) VALUES (1, '2026-09-16 10:00:00', 200.0);"
            )
            id_caja = cursor.lastrowid

            # 3. Crear venta
            cursor.execute(
                "INSERT INTO Venta (id_caja, fecha_hora, total, metodo_pago) VALUES (?, '2026-09-16 11:00:00', 50.0, 'EFECTIVO');",
                (id_caja,),
            )
            id_venta = cursor.lastrowid

            # 4. Crear detalle
            cursor.execute(
                "INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario, subtotal) VALUES (?, ?, 2, 25.0, 50.0);",
                (id_venta, id_prod),
            )

        # Verificar que existen
        with get_db_cursor(self.db_path) as cursor:
            cursor.execute("SELECT count(*) FROM DetalleVenta WHERE id_venta = ?;", (id_venta,))
            self.assertEqual(cursor.fetchone()[0], 1)

            # Eliminar la venta directamente
            cursor.execute("DELETE FROM Venta WHERE id_venta = ?;", (id_venta,))

            # DetalleVenta debe haber sido eliminado en cascada
            cursor.execute("SELECT count(*) FROM DetalleVenta WHERE id_venta = ?;", (id_venta,))
            self.assertEqual(cursor.fetchone()[0], 0, "DetalleVenta debe eliminarse automáticamente al borrar la Venta.")

    def test_crear_respaldo_db_exitoso(self) -> None:
        """Verifica la generación de una copia de respaldo íntegra."""
        backup_dir = Path(self.temp_dir.name) / "backups_test"
        backup_file = crear_respaldo_db(self.db_path, backup_dir)

        self.assertTrue(backup_file.exists(), "El archivo de respaldo debe existir.")
        tablas_backup = obtener_tablas_existentes(backup_file)
        self.assertEqual(set(tablas_backup), set(obtener_tablas_existentes(self.db_path)))


if __name__ == "__main__":
    unittest.main()
