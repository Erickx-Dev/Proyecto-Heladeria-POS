from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.migrations import inicializar_base_de_datos
from src.domain.user import Usuario
from src.ui.app import HeladeriaApp
from src.ui.views.backup_view import BackupView
from src.ui.views.cash_turn_view import CashTurnView
from src.ui.views.catalog_view import CatalogView
from src.ui.views.expense_view import ExpenseView
from src.ui.views.inventory_view import InventoryView
from src.ui.views.loss_view import LossView
from src.ui.views.pos_view import POSView
from src.ui.views.reports_view import ReportsView
from src.ui.views.users_view import UsersView


class TestHeladeriaApp(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_ui.db"
        inicializar_base_de_datos(self.db_path)

        self.admin = Usuario(
            id_usuario=1,
            nombre="Admin Test",
            username="admin",
            password_hash="x" * 60,
            id_rol=1,
        )
        self.empleado = Usuario(
            id_usuario=2,
            nombre="Empleado Test",
            username="empleado",
            password_hash="x" * 60,
            id_rol=2,
        )

        self.app = HeladeriaApp(db_path=self.db_path)
        self.app.withdraw()

    def tearDown(self) -> None:
        try:
            self.app.destroy()
        except Exception:
            pass
        self.temp_dir.cleanup()

    def test_inicio_en_login(self) -> None:
        self.assertIsNotNone(self.app._login_frame)
        self.assertIsNone(self.app._usuario_actual)
        self.assertIsNone(self.app._sidebar)
        self.assertIsNone(self.app._contenedor_principal)

    def test_login_exitoso_y_navegacion_admin(self) -> None:
        self.app._on_login_success(self.admin)

        self.assertIsNone(self.app._login_frame)
        self.assertEqual(self.app._usuario_actual, self.admin)
        self.assertIsNotNone(self.app._sidebar)
        self.assertIsNotNone(self.app._contenedor_principal)
        self.assertIsInstance(self.app._vista_activa_frame, POSView)

        vistas_y_clases = [
            ("caja", CashTurnView),
            ("catalogo", CatalogView),
            ("inventario", InventoryView),
            ("mermas", LossView),
            ("gastos", ExpenseView),
            ("reportes", ReportsView),
            ("usuarios", UsersView),
            ("backup", BackupView),
            ("pos", POSView),
        ]

        for clave, clase_esperada in vistas_y_clases:
            self.app.navigate_to(clave)
            self.assertIsInstance(
                self.app._vista_activa_frame,
                clase_esperada,
                f"Fallo al navegar a {clave}",
            )

    def test_logout_regresa_a_login(self) -> None:
        self.app._on_login_success(self.admin)
        self.assertIsNotNone(self.app._sidebar)

        self.app.logout()

        self.assertIsNone(self.app._usuario_actual)
        self.assertIsNone(self.app._sidebar)
        self.assertIsNone(self.app._contenedor_principal)
        self.assertIsNone(self.app._vista_activa_frame)
        self.assertIsNotNone(self.app._login_frame)


if __name__ == "__main__":
    unittest.main()
