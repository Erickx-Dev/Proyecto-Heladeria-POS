from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk
from PIL import Image, ImageEnhance

from src.core.exceptions import HeladeriaPOSException
from src.domain.user import Usuario
from src.services.auth_service import AuthService
from src.ui.theme import (
    COLOR_BORDE_SUAVE,
    COLOR_COBRO_FRAMBUESA,
    COLOR_COBRO_HOVER,
    COLOR_DORADO_PREMIUM,
    COLOR_PELIGRO,
    COLOR_TEXTO_MUTED,
    COLOR_TEXTO_TITULO,
    FUENTE_BOTON,
    FUENTE_FAMILIA,
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
        super().__init__(master, fg_color="#14171C", **kwargs)
        self._auth_service: AuthService = auth_service
        self._on_login_success: Callable[[Usuario], None] = on_login_success

        self._bg_path: Path = Path(__file__).resolve().parents[3] / "assets" / "login_bg.jpg"
        self._original_image: Optional[Image.Image] = None
        self._bg_ctk_image: Optional[ctk.CTkImage] = None
        self._last_w: int = 0
        self._last_h: int = 0

        self._bg_label = ctk.CTkLabel(self, text="", fg_color="transparent")
        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self._cargar_imagen_fondo()
        self._construir_formulario()

        self.bind("<Configure>", self._al_redimensionar)

    def _cargar_imagen_fondo(self) -> None:
        if self._bg_path.exists():
            try:
                raw_img = Image.open(self._bg_path)
                enhancer = ImageEnhance.Brightness(raw_img)
                self._original_image = enhancer.enhance(0.72)
            except Exception:
                self._original_image = None

    def _al_redimensionar(self, event=None) -> None:
        if self._original_image is None:
            return

        w = self.winfo_width()
        h = self.winfo_height()

        if w <= 100 or h <= 100:
            return

        if abs(w - self._last_w) < 40 and abs(h - self._last_h) < 40:
            return

        self._last_w = w
        self._last_h = h

        orig_w, orig_h = self._original_image.size
        scale = max(w / orig_w, h / orig_h)
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))

        resized = self._original_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max(0, (new_w - w) // 2)
        top = max(0, (new_h - h) // 2)
        cropped = resized.crop((left, top, left + w, top + h))

        self._bg_ctk_image = ctk.CTkImage(
            light_image=cropped,
            dark_image=cropped,
            size=(w, h),
        )
        self._bg_label.configure(image=self._bg_ctk_image)

    def _construir_formulario(self) -> None:
        tarjeta = ctk.CTkFrame(
            self,
            fg_color="#181B22",
            corner_radius=20,
            border_width=2,
            border_color=COLOR_DORADO_PREMIUM,
            width=400,
        )
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")
        tarjeta.grid_columnconfigure(0, weight=1)

        lbl_logo = ctk.CTkLabel(
            tarjeta,
            text="🍨 HELA-POS",
            font=FUENTE_TITULO_GRANDE,
            text_color=COLOR_DORADO_PREMIUM,
        )
        lbl_logo.pack(padx=28, pady=(32, 4))

        lbl_sub = ctk.CTkLabel(
            tarjeta,
            text="Heladería Artesanal • Sistema de Gestión y POS",
            font=FUENTE_MUTED,
            text_color=COLOR_TEXTO_MUTED,
        )
        lbl_sub.pack(padx=28, pady=(0, 20))

        divisor = ctk.CTkFrame(tarjeta, fg_color=COLOR_BORDE_SUAVE, height=1)
        divisor.pack(fill="x", padx=28, pady=(0, 18))

        ctk.CTkLabel(
            tarjeta,
            text="Usuario:",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
            anchor="w",
        ).pack(fill="x", padx=32, pady=(4, 2))

        self._entry_user = ctk.CTkEntry(
            tarjeta,
            placeholder_text="Nombre de usuario",
            font=FUENTE_TEXTO,
            height=42,
            corner_radius=RADIO_ENTRY,
            fg_color="#242832",
            border_color=COLOR_BORDE_SUAVE,
            text_color=COLOR_TEXTO_TITULO,
        )
        self._entry_user.pack(fill="x", padx=32, pady=(0, 12))
        self._entry_user.bind("<Return>", lambda e: self._entry_pass.focus())

        ctk.CTkLabel(
            tarjeta,
            text="Contraseña:",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
            anchor="w",
        ).pack(fill="x", padx=32, pady=(4, 2))

        self._entry_pass = ctk.CTkEntry(
            tarjeta,
            placeholder_text="••••••••",
            show="•",
            font=FUENTE_TEXTO,
            height=42,
            corner_radius=RADIO_ENTRY,
            fg_color="#242832",
            border_color=COLOR_BORDE_SUAVE,
            text_color=COLOR_TEXTO_TITULO,
        )
        self._entry_pass.pack(fill="x", padx=32, pady=(0, 8))
        self._entry_pass.bind("<Return>", lambda e: self._iniciar_sesion())

        self._lbl_error = ctk.CTkLabel(
            tarjeta,
            text="",
            font=FUENTE_TEXTO,
            text_color=COLOR_PELIGRO,
            wraplength=330,
        )
        self._lbl_error.pack(padx=28, pady=(4, 8))

        btn_login = ctk.CTkButton(
            tarjeta,
            text="🍓 Iniciar Sesión",
            font=(FUENTE_FAMILIA, 14, "bold"),
            height=46,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_COBRO_FRAMBUESA,
            hover_color=COLOR_COBRO_HOVER,
            text_color=COLOR_TEXTO_TITULO,
            command=self._iniciar_sesion,
        )
        btn_login.pack(fill="x", padx=32, pady=(4, 32))

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
