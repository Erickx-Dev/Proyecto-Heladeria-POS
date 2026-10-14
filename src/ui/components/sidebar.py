from __future__ import annotations

from typing import Callable, Dict, List, Optional
import customtkinter as ctk

from src.domain.user import Permiso, Usuario
from src.ui.theme import (
    COLOR_ACENTO_CYAN,
    COLOR_BORDE_SUAVE,
    COLOR_DORADO_PREMIUM,
    COLOR_PELIGRO,
    COLOR_PELIGRO_HOVER,
    COLOR_SIDEBAR,
    COLOR_SUPERFICIE,
    COLOR_SUPERFICIE_HOVER,
    COLOR_TEXTO_CUERPO,
    COLOR_TEXTO_MUTED,
    COLOR_TEXTO_TITULO,
    FUENTE_BOTON,
    FUENTE_FAMILIA,
    FUENTE_MUTED,
    FUENTE_TITULO_MEDIO,
    RADIO_BOTON,
)


class SidebarNavigation(ctk.CTkFrame):

    ITEMS_MENU: List[tuple[str, str, str, Optional[Permiso]]] = [
        ("pos", "🛒 Punto de Venta", "POS", Permiso.VENTAS),
        ("caja", "💵 Caja y Turno", "CAJA", Permiso.CAJA),
        ("catalogo", "🏷️ Catálogo", "CATALOGO", Permiso.CATALOGO),
        ("inventario", "📦 Inventario", "INVENTARIO", Permiso.INVENTARIO),
        ("mermas", "📉 Mermas", "MERMAS", Permiso.MERMAS),
        ("gastos", "💸 Gastos Menores", "GASTOS", Permiso.GASTOS),
        ("reportes", "📊 Reportes", "REPORTES", Permiso.REPORTES),
        ("usuarios", "👥 Personal", "USUARIOS", Permiso.GESTIONAR_USUARIOS),
        ("backup", "💾 Respaldo BD", "BACKUP", Permiso.BACKUP),
    ]

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        on_navigate: Callable[[str], None],
        on_logout: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLOR_SIDEBAR,
            corner_radius=0,
            width=220,
            border_width=1,
            border_color=COLOR_BORDE_SUAVE,
            **kwargs,
        )
        self._usuario: Usuario = usuario
        self._on_navigate: Callable[[str], None] = on_navigate
        self._on_logout: Callable[[], None] = on_logout
        self._botones: Dict[str, ctk.CTkButton] = {}
        self._vista_activa: str = "pos"

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._crear_encabezado()
        self._crear_menu()
        self._crear_pie_usuario()

    def _crear_encabezado(self) -> None:
        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.grid(row=0, column=0, padx=16, pady=(18, 12), sticky="ew")

        lbl_logo = ctk.CTkLabel(
            encabezado,
            text="🍨 HELA-POS",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_DORADO_PREMIUM,
        )
        lbl_logo.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            encabezado,
            text="Heladería Artesanal",
            font=FUENTE_MUTED,
            text_color=COLOR_TEXTO_MUTED,
        )
        lbl_sub.pack(anchor="w")

        divisor = ctk.CTkFrame(self, fg_color=COLOR_BORDE_SUAVE, height=1)
        divisor.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")

    def _crear_menu(self) -> None:
        scroll_menu = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_menu.grid(row=2, column=0, padx=8, pady=0, sticky="nsew")
        scroll_menu.grid_columnconfigure(0, weight=1)

        fila: int = 0
        for clave, etiqueta, _, permiso_req in self.ITEMS_MENU:
            if permiso_req is not None and not self._usuario.has_permission(permiso_req):
                continue

            btn = ctk.CTkButton(
                scroll_menu,
                text=etiqueta,
                font=FUENTE_BOTON,
                anchor="w",
                corner_radius=RADIO_BOTON,
                height=38,
                fg_color="transparent",
                text_color=COLOR_TEXTO_CUERPO,
                hover_color=COLOR_SUPERFICIE_HOVER,
                command=lambda k=clave: self._seleccionar(k),
            )
            btn.grid(row=fila, column=0, padx=6, pady=3, sticky="ew")
            self._botones[clave] = btn
            fila += 1

    def _crear_pie_usuario(self) -> None:
        pie = ctk.CTkFrame(
            self,
            fg_color="#F8FAFC",
            corner_radius=RADIO_BOTON,
            border_width=1,
            border_color=COLOR_BORDE_SUAVE,
        )
        pie.grid(row=3, column=0, padx=10, pady=12, sticky="ew")

        rol_txt = "Administrador" if self._usuario.es_administrador() else "Empleado"
        lbl_user = ctk.CTkLabel(
            pie,
            text=f"👤 {self._usuario.nombre}",
            font=(FUENTE_FAMILIA, 11, "bold"),
            text_color=COLOR_TEXTO_TITULO,
            anchor="w",
        )
        lbl_user.pack(padx=10, pady=(8, 0), anchor="w")

        lbl_rol = ctk.CTkLabel(
            pie,
            text=rol_txt,
            font=FUENTE_MUTED,
            text_color=COLOR_DORADO_PREMIUM,
            anchor="w",
        )
        lbl_rol.pack(padx=10, pady=(0, 6), anchor="w")

        btn_salir = ctk.CTkButton(
            pie,
            text="Cerrar Sesión",
            font=(FUENTE_FAMILIA, 11, "bold"),
            height=28,
            corner_radius=8,
            fg_color=COLOR_PELIGRO,
            hover_color=COLOR_PELIGRO_HOVER,
            command=self._on_logout,
        )
        btn_salir.pack(padx=10, pady=(0, 8), fill="x")

    def _seleccionar(self, clave: str) -> None:
        self.establecer_activo(clave)
        self._on_navigate(clave)

    def establecer_activo(self, clave: str) -> None:
        self._vista_activa = clave
        for k, btn in self._botones.items():
            if k == clave:
                btn.configure(
                    fg_color="#FEF3C7",
                    text_color=COLOR_DORADO_PREMIUM,
                    border_width=1,
                    border_color=COLOR_DORADO_PREMIUM,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLOR_TEXTO_CUERPO,
                    border_width=0,
                )
