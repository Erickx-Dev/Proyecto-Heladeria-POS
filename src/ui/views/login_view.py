from __future__ import annotations

from typing import Callable, Optional
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.user import Usuario
from src.services.auth_service import AuthService
from src.ui.theme import (
    COLOR_BORDE_SUAVE,
    COLOR_COBRO_FRAMBUESA,
    COLOR_COBRO_HOVER,
    COLOR_DORADO_PREMIUM,
    COLOR_FONDO_VENTANA,
    COLOR_PELIGRO,
    COLOR_SUPERFICIE,
    COLOR_TEXTO_CUERPO,
    COLOR_TEXTO_MUTED,
    COLOR_TEXTO_TITULO,
    FUENTE_BOTON,
    FUENTE_MUTED,
    FUENTE_SUBTITULO,
    FUENTE_TEXTO,
    FUENTE_TITULO_GRANDE,
    RADIO_BOTON,
    RADIO_ENTRY,
    RADIO_PANEL,
)


class LoginView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        auth_service: AuthService,
        on_login_success: Callable[[Usuario], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._auth_service: AuthService = auth_service
        self._on_login_success: Callable[[Usuario], None] = on_login_success

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_formulario()

    def _construir_formulario(self) -> None:
        tarjeta = ctk.CTkFrame(
            self,
            fg_color=COLOR_SUPERFICIE,
            corner_radius=RADIO_PANEL,
            border_width=2,
            border_color=COLOR_DORADO_PREMIUM,
            width=380,
        )
        tarjeta.grid(row=0, column=0, padx=20, pady=20)
        tarjeta.grid_columnconfigure(0, weight=1)

        lbl_logo = ctk.CTkLabel(
            tarjeta,
            text="🍨 HELA-POS",
            font=FUENTE_TITULO_GRANDE,
            text_color=COLOR_DORADO_PREMIUM,
        )
        lbl_logo.pack(padx=24, pady=(28, 4))

        lbl_sub = ctk.CTkLabel(
            tarjeta,
            text="Sistema de Gestión y Punto de Venta",
            font=FUENTE_MUTED,
            text_color=COLOR_TEXTO_MUTED,
        )
        lbl_sub.pack(padx=24, pady=(0, 20))

        divisor = ctk.CTkFrame(tarjeta, fg_color=COLOR_BORDE_SUAVE, height=1)
        divisor.pack(fill="x", padx=24, pady=(0, 18))

        ctk.CTkLabel(
            tarjeta,
            text="Usuario:",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
            anchor="w",
        ).pack(fill="x", padx=28, pady=(4, 2))

        self._entry_user = ctk.CTkEntry(
            tarjeta,
            placeholder_text="Nombre de usuario",
            font=FUENTE_TEXTO,
            height=40,
            corner_radius=RADIO_ENTRY,
            fg_color=COLOR_FONDO_VENTANA,
            border_color=COLOR_BORDE_SUAVE,
            text_color=COLOR_TEXTO_TITULO,
        )
        self._entry_user.pack(fill="x", padx=28, pady=(0, 12))
        self._entry_user.bind("<Return>", lambda e: self._entry_pass.focus())

        ctk.CTkLabel(
            tarjeta,
            text="Contraseña:",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
            anchor="w",
        ).pack(fill="x", padx=28, pady=(4, 2))

        self._entry_pass = ctk.CTkEntry(
            tarjeta,
            placeholder_text="••••••••",
            show="•",
            font=FUENTE_TEXTO,
            height=40,
            corner_radius=RADIO_ENTRY,
            fg_color=COLOR_FONDO_VENTANA,
            border_color=COLOR_BORDE_SUAVE,
            text_color=COLOR_TEXTO_TITULO,
        )
        self._entry_pass.pack(fill="x", padx=28, pady=(0, 8))
        self._entry_pass.bind("<Return>", lambda e: self._iniciar_sesion())

        self._lbl_error = ctk.CTkLabel(
            tarjeta,
            text="",
            font=FUENTE_TEXTO,
            text_color=COLOR_PELIGRO,
            wraplength=320,
        )
        self._lbl_error.pack(padx=24, pady=(4, 8))

        btn_login = ctk.CTkButton(
            tarjeta,
            text="Iniciar Sesión",
            font=FUENTE_BOTON,
            height=44,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_COBRO_FRAMBUESA,
            hover_color=COLOR_COBRO_HOVER,
            text_color=COLOR_TEXTO_TITULO,
            command=self._iniciar_sesion,
        )
        btn_login.pack(fill="x", padx=28, pady=(4, 28))

    def _iniciar_sesion(self) -> None:
        username = self._entry_user.get().strip()
        password = self._entry_pass.get()

        self._lbl_error.configure(text="")
        try:
            usuario = self._auth_service.autenticar(username, password)
            self._on_login_success(usuario)
        except HeladeriaPOSException as exc:
            self._lbl_error.configure(text=exc.mensaje)
        except Exception as exc:
            self._lbl_error.configure(text=f"Error inesperado: {exc}")
