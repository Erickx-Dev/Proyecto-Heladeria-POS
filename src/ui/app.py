from __future__ import annotations

from pathlib import Path
from typing import Optional, Union
import customtkinter as ctk

from src.domain.user import Permiso, Usuario
from src.services.auth_service import AuthService
from src.services.backup_service import BackupService
from src.services.cash_service import CashService
from src.services.catalog_service import CatalogService
from src.services.expense_service import ExpenseService
from src.services.inventory_service import InventoryService
from src.services.loss_service import LossService
from src.services.pos_service import POSService
from src.services.report_service import ReportService
from src.services.user_service import UserService
from src.ui.components.sidebar import SidebarNavigation
from src.ui.theme import COLOR_FONDO_VENTANA
from src.ui.views.backup_view import BackupView
from src.ui.views.cash_turn_view import CashTurnView
from src.ui.views.catalog_view import CatalogView
from src.ui.views.expense_view import ExpenseView
from src.ui.views.inventory_view import InventoryView
from src.ui.views.login_view import LoginView
from src.ui.views.loss_view import LossView
from src.ui.views.pos_view import POSView
from src.ui.views.reports_view import ReportsView
from src.ui.views.users_view import UsersView


class HeladeriaApp(ctk.CTk):

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._db_path: Optional[Union[str, Path]] = db_path

        self.title("HELA-POS - Heladería Artesanal")
        self.geometry("1200x750")
        self.minsize(1024, 600)
        self.configure(fg_color=COLOR_FONDO_VENTANA)

        self.auth_service: AuthService = AuthService(db_path=db_path)
        self.cash_service: CashService = CashService(db_path=db_path)
        self.catalog_service: CatalogService = CatalogService(db_path=db_path)
        self.inventory_service: InventoryService = InventoryService(db_path=db_path)
        self.pos_service: POSService = POSService(db_path=db_path)
        self.expense_service: ExpenseService = ExpenseService(
            cash_service=self.cash_service, db_path=db_path
        )
        self.loss_service: LossService = LossService(db_path=db_path)
        self.report_service: ReportService = ReportService(db_path=db_path)
        self.user_service: UserService = UserService(db_path=db_path)
        self.backup_service: BackupService = BackupService(db_path=db_path)

        self._usuario_actual: Optional[Usuario] = None
        self._sidebar: Optional[SidebarNavigation] = None
        self._contenedor_principal: Optional[ctk.CTkFrame] = None
        self._vista_activa_frame: Optional[ctk.CTkFrame] = None
        self._login_frame: Optional[LoginView] = None

        self.mostrar_login()

    def mostrar_login(self) -> None:
        if self._vista_activa_frame is not None:
            self._vista_activa_frame.destroy()
            self._vista_activa_frame = None

        if self._contenedor_principal is not None:
            self._contenedor_principal.destroy()
            self._contenedor_principal = None

        if self._sidebar is not None:
            self._sidebar.destroy()
            self._sidebar = None

        self._usuario_actual = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self._login_frame = LoginView(
            master=self,
            auth_service=self.auth_service,
            on_login_success=self._on_login_success,
        )
        self._login_frame.grid(row=0, column=0, sticky="nsew")

    def _on_login_success(self, usuario: Usuario) -> None:
        if self._login_frame is not None:
            self._login_frame.destroy()
            self._login_frame = None

        self._usuario_actual = usuario

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = SidebarNavigation(
            master=self,
            usuario=usuario,
            on_navigate=self.navigate_to,
            on_logout=self.logout,
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        self._contenedor_principal = ctk.CTkFrame(
            master=self,
            fg_color=COLOR_FONDO_VENTANA,
            corner_radius=0,
        )
        self._contenedor_principal.grid(row=0, column=1, sticky="nsew")

        vista_inicial = "pos"
        if usuario.has_permission(Permiso.VENTAS):
            vista_inicial = "pos"
        elif usuario.has_permission(Permiso.CAJA):
            vista_inicial = "caja"
        elif usuario.has_permission(Permiso.REPORTES):
            vista_inicial = "reportes"
        else:
            for clave, _, _, permiso in SidebarNavigation.ITEMS_MENU:
                if permiso is None or usuario.has_permission(permiso):
                    vista_inicial = clave
                    break

        self.navigate_to(vista_inicial)

    def navigate_to(self, view_name: str) -> None:
        if self._contenedor_principal is None or self._usuario_actual is None:
            return

        if self._vista_activa_frame is not None:
            self._vista_activa_frame.destroy()
            self._vista_activa_frame = None

        if self._sidebar is not None:
            self._sidebar.establecer_activo(view_name)

        if view_name == "pos":
            self._vista_activa_frame = POSView(
                master=self._contenedor_principal,
                usuario=self._usuario_actual,
                pos_service=self.pos_service,
                catalog_service=self.catalog_service,
                cash_service=self.cash_service,
                on_ir_a_caja=lambda: self.navigate_to("caja"),
            )
        elif view_name == "caja":
            self._vista_activa_frame = CashTurnView(
                master=self._contenedor_principal,
                usuario=self._usuario_actual,
                cash_service=self.cash_service,
            )
        elif view_name == "catalogo":
            self._vista_activa_frame = CatalogView(
                master=self._contenedor_principal,
                usuario=self._usuario_actual,
                catalog_service=self.catalog_service,
            )
        elif view_name == "inventario":
            self._vista_activa_frame = InventoryView(
                master=self._contenedor_principal,
                usuario=self._usuario_actual,
                inventory_service=self.inventory_service,
            )
        elif view_name == "mermas":
            self._vista_activa_frame = LossView(
                master=self._contenedor_principal,
                usuario=self._usuario_actual,
                loss_service=self.loss_service,
                inventory_service=self.inventory_service,
            )
        elif view_name == "gastos":
            self._vista_activa_frame = ExpenseView(
                master=self._contenedor_principal,
                usuario=self._usuario_actual,
                expense_service=self.expense_service,
            )
        elif view_name == "reportes":
            self._vista_activa_frame = ReportsView(
                master=self._contenedor_principal,
                usuario=self._usuario_actual,
                report_service=self.report_service,
            )
        elif view_name == "usuarios":
            self._vista_activa_frame = UsersView(
                master=self._contenedor_principal,
                usuario=self._usuario_actual,
                user_service=self.user_service,
            )
        elif view_name == "backup":
            self._vista_activa_frame = BackupView(
                master=self._contenedor_principal,
                usuario=self._usuario_actual,
                backup_service=self.backup_service,
            )
        else:
            return

        self._vista_activa_frame.pack(fill="both", expand=True)

    def logout(self) -> None:
        self.auth_service.cerrar_sesion()
        self.mostrar_login()
