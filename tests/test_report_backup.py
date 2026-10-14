from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from database.backup import crear_respaldo, listar_respaldos, verificar_integridad_respaldo
from database.connection import get_connection
from database.migrations import inicializar_base_de_datos
from src.core.exceptions import AutorizacionError, ValidacionError
from src.domain.user import Usuario
from src.services.backup_service import BackupService
from src.services.report_service import ReportService

ADMIN = Usuario(id_usuario=1, nombre="Administrador", username="admin", password_hash="x" * 60, id_rol=1)
EMPLEADO = Usuario(id_usuario=None, nombre="Empleado", username="empleado", password_hash="x" * 60, id_rol=2)


class BaseOla6(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_ola6.db"
        inicializar_base_de_datos(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def ejecutar(self, sql: str, parametros: tuple = ()) -> int:
        conn = get_connection(self.db_path)
        try:
            with conn:
                return conn.execute(sql, parametros).lastrowid
        finally:
            conn.close()

    def contar_auditoria(self, accion: str) -> int:
        conn = get_connection(self.db_path)
        try:
            return conn.execute("SELECT COUNT(*) FROM AuditoriaLog WHERE accion = ?;", (accion,)).fetchone()[0]
        finally:
            conn.close()


class TestReportService(BaseOla6):

    def setUp(self) -> None:
        super().setUp()
        self.reportes = ReportService(db_path=self.db_path)
        self.id_caja = self.ejecutar(
            "INSERT INTO Caja (id_usuario, fecha_apertura, monto_inicial) VALUES (1, '2026-10-05 08:00:00', 50000);"
        )
        self.id_fresa = self.ejecutar(
            "INSERT INTO Producto (codigo, nombre, precio_venta, id_categoria) VALUES ('HEL-01', 'Helado Fresa', 5000, 1);"
        )
        self.id_vainilla = self.ejecutar(
            "INSERT INTO Producto (codigo, nombre, precio_venta, id_categoria) VALUES ('HEL-02', 'Helado Vainilla', 4000, 1);"
        )
        self.id_malteada = self.ejecutar(
            "INSERT INTO Producto (codigo, nombre, precio_venta, id_categoria) VALUES ('MAL-01', 'Malteada', 8000, 2);"
        )

        self.venta("2026-10-05 10:00:00", "EFECTIVO", [(self.id_fresa, 2, 5000), (self.id_malteada, 1, 8000)])
        self.venta("2026-10-05 15:30:00", "TRANSFERENCIA", [(self.id_vainilla, 3, 4000)])
        self.venta("2026-10-07 11:00:00", "EFECTIVO", [(self.id_fresa, 1, 5000)])
        self.venta("2026-10-20 12:00:00", "TARJETA", [(self.id_malteada, 2, 8000)])
        self.venta("2026-11-02 09:00:00", "EFECTIVO", [(self.id_vainilla, 10, 4000)])

        self.gasto("2026-10-05 12:00:00", 3000)
        self.gasto("2026-10-07 12:00:00", 2000)

    def venta(self, fecha_hora: str, metodo: str, lineas: list) -> None:
        total = sum(c * p for _, c, p in lineas)
        id_venta = self.ejecutar(
            "INSERT INTO Venta (id_caja, fecha_hora, total, metodo_pago, dinero_recibido, cambio) VALUES (?, ?, ?, ?, ?, 0);",
            (self.id_caja, fecha_hora, total, metodo, total),
        )
        for id_producto, cantidad, precio in lineas:
            self.ejecutar(
                "INSERT INTO DetalleVenta (id_venta, id_producto, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?);",
                (id_venta, id_producto, cantidad, precio, cantidad * precio),
            )

    def gasto(self, fecha_hora: str, monto: float) -> None:
        self.ejecutar(
            "INSERT INTO Gasto (id_caja, fecha_hora, monto, descripcion, id_usuario) VALUES (?, ?, ?, 'Hielo', 1);",
            (self.id_caja, fecha_hora, monto),
        )

    def test_empleado_sin_permiso(self) -> None:
        with self.assertRaises(AutorizacionError):
            self.reportes.reporte_diario(EMPLEADO, date(2026, 10, 5))
        with self.assertRaises(AutorizacionError):
            self.reportes.productos_mas_vendidos(EMPLEADO, "2026-10-01", "2026-10-31")

    def test_reporte_diario(self) -> None:
        r = self.reportes.reporte_diario(ADMIN, date(2026, 10, 5))
        self.assertEqual(r.ventas_brutas, 30000.0)
        self.assertEqual(r.total_gastos, 3000.0)
        self.assertEqual(r.ganancia_neta, 27000.0)
        self.assertEqual(r.cantidad_ventas, 2)
        self.assertEqual(r.ticket_promedio, 15000.0)
        self.assertEqual(r.ventas_por_metodo, {"EFECTIVO": 18000.0, "TRANSFERENCIA": 12000.0})

    def test_reporte_dia_sin_movimientos(self) -> None:
        r = self.reportes.reporte_diario(ADMIN, date(2026, 10, 6))
        self.assertEqual(r.ventas_brutas, 0.0)
        self.assertEqual(r.cantidad_ventas, 0)
        self.assertEqual(r.ticket_promedio, 0.0)
        self.assertEqual(r.ventas_por_metodo, {})

    def test_reporte_semanal_lunes_a_domingo(self) -> None:
        r = self.reportes.reporte_semanal(ADMIN, date(2026, 10, 7))
        self.assertEqual(r.fecha_desde, "2026-10-05")
        self.assertEqual(r.fecha_hasta, "2026-10-11")
        self.assertEqual(r.ventas_brutas, 35000.0)
        self.assertEqual(r.total_gastos, 5000.0)
        self.assertEqual(r.ganancia_neta, 30000.0)

    def test_reporte_mensual(self) -> None:
        r = self.reportes.reporte_mensual(ADMIN, 2026, 10)
        self.assertEqual(r.fecha_desde, "2026-10-01")
        self.assertEqual(r.fecha_hasta, "2026-10-31")
        self.assertEqual(r.ventas_brutas, 51000.0)
        self.assertEqual(r.cantidad_ventas, 4)

    def test_reporte_mensual_mes_invalido(self) -> None:
        with self.assertRaises(ValidacionError):
            self.reportes.reporte_mensual(ADMIN, 2026, 13)

    def test_rango_invertido_o_formato_invalido(self) -> None:
        with self.assertRaises(ValidacionError):
            self.reportes.resumen_financiero(ADMIN, "2026-10-31", "2026-10-01")
        with self.assertRaises(ValidacionError):
            self.reportes.resumen_financiero(ADMIN, "05/10/2026", "2026-10-31")

    def test_ranking_desempate_por_ingresos(self) -> None:
        ranking = self.reportes.productos_mas_vendidos(ADMIN, "2026-10-01", "2026-10-31")
        self.assertEqual([p.codigo for p in ranking], ["MAL-01", "HEL-01", "HEL-02"])
        self.assertEqual([p.cantidad_vendida for p in ranking], [3, 3, 3])
        self.assertEqual([p.ingresos for p in ranking], [24000.0, 15000.0, 12000.0])

    def test_ranking_ordena_por_cantidad(self) -> None:
        ranking = self.reportes.productos_mas_vendidos(ADMIN, "2026-10-01", "2026-11-30")
        self.assertEqual(ranking[0].codigo, "HEL-02")
        self.assertEqual(ranking[0].cantidad_vendida, 13)

    def test_ranking_sabores_por_categoria_y_limite(self) -> None:
        ranking = self.reportes.productos_mas_vendidos(ADMIN, "2026-10-01", "2026-11-30", limite=1, id_categoria=1)
        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0].nombre, "Helado Vainilla")
        self.assertEqual(ranking[0].cantidad_vendida, 13)
        self.assertEqual(ranking[0].nombre_categoria, "Helados Tradicionales")

    def test_ranking_limite_invalido(self) -> None:
        with self.assertRaises(ValidacionError):
            self.reportes.productos_mas_vendidos(ADMIN, "2026-10-01", "2026-10-31", limite=0)

    def test_ventas_por_dia(self) -> None:
        serie = self.reportes.ventas_por_dia(ADMIN, "2026-10-01", "2026-10-10")
        self.assertEqual([(d.fecha, d.cantidad_ventas, d.ventas_brutas) for d in serie], [
            ("2026-10-05", 2, 30000.0),
            ("2026-10-07", 1, 5000.0),
        ])


class TestBackupModule(BaseOla6):

    def test_crear_respaldo_valido(self) -> None:
        destino = Path(self.temp_dir.name) / "usb"
        ruta = crear_respaldo(self.db_path, destino)
        self.assertTrue(ruta.exists())
        self.assertTrue(ruta.name.startswith("heladeria_backup_"))
        self.assertTrue(verificar_integridad_respaldo(ruta))

        conn = sqlite3.connect(str(ruta))
        try:
            usuarios = conn.execute("SELECT username FROM Usuario;").fetchall()
        finally:
            conn.close()
        self.assertEqual(usuarios[0][0], "admin")

    def test_crear_respaldo_origen_inexistente(self) -> None:
        with self.assertRaises(FileNotFoundError):
            crear_respaldo(Path(self.temp_dir.name) / "no_existe.db", Path(self.temp_dir.name) / "usb")

    def test_destino_que_es_archivo(self) -> None:
        archivo = Path(self.temp_dir.name) / "archivo.txt"
        archivo.write_text("x")
        with self.assertRaises(NotADirectoryError):
            crear_respaldo(self.db_path, archivo)

    def test_integridad_archivo_corrupto(self) -> None:
        corrupto = Path(self.temp_dir.name) / "corrupto.db"
        corrupto.write_bytes(b"esto no es sqlite" * 100)
        self.assertFalse(verificar_integridad_respaldo(corrupto))
        self.assertFalse(verificar_integridad_respaldo(Path(self.temp_dir.name) / "nada.db"))

    def test_listar_respaldos_ordenados(self) -> None:
        carpeta = Path(self.temp_dir.name) / "backups"
        carpeta.mkdir()
        for nombre in ("heladeria_backup_20261001_100000.db", "heladeria_backup_20261005_100000.db", "otro.db"):
            (carpeta / nombre).write_bytes(b"")
        nombres = [p.name for p in listar_respaldos(carpeta)]
        self.assertEqual(nombres, ["heladeria_backup_20261005_100000.db", "heladeria_backup_20261001_100000.db"])
        self.assertEqual(listar_respaldos(Path(self.temp_dir.name) / "no_existe"), [])


class TestBackupService(BaseOla6):

    def setUp(self) -> None:
        super().setUp()
        self.servicio = BackupService(db_path=self.db_path)

    def test_admin_crea_respaldo_y_audita(self) -> None:
        destino = Path(self.temp_dir.name) / "usb"
        ruta = self.servicio.crear_respaldo(ADMIN, destino)
        self.assertTrue(ruta.exists())
        self.assertEqual(ruta.parent, destino)
        self.assertEqual(self.contar_auditoria("RESPALDO_CREADO"), 1)
        self.assertEqual(len(self.servicio.listar_respaldos(ADMIN, destino)), 1)

    def test_carpeta_por_defecto(self) -> None:
        ruta = self.servicio.crear_respaldo(ADMIN)
        self.assertEqual(ruta.parent, self.db_path.parent / "backups")

    def test_empleado_sin_permiso(self) -> None:
        with self.assertRaises(AutorizacionError):
            self.servicio.crear_respaldo(EMPLEADO)
        with self.assertRaises(AutorizacionError):
            self.servicio.listar_respaldos(EMPLEADO)

    def test_fallo_queda_auditado(self) -> None:
        archivo = Path(self.temp_dir.name) / "archivo.txt"
        archivo.write_text("x")
        with self.assertRaises(NotADirectoryError):
            self.servicio.crear_respaldo(ADMIN, archivo)
        self.assertEqual(self.contar_auditoria("RESPALDO_FALLIDO"), 1)


if __name__ == "__main__":
    unittest.main()
