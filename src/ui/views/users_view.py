from __future__ import annotations

import tkinter.messagebox as msgbox
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.user import Usuario
from src.services.user_service import UserService
from src.ui.theme import (
    COLOR_ACENTO_CYAN,
    COLOR_BORDE_SUAVE,
    COLOR_BOTON_SECUNDARIO,
    COLOR_COBRO_FRAMBUESA,
    COLOR_DORADO_PREMIUM,
    COLOR_EXITO,
    COLOR_FONDO_VENTANA,
    COLOR_PELIGRO,
    COLOR_SUPERFICIE,
    COLOR_SUPERFICIE_HOVER,
    COLOR_TEXTO_CUERPO,
    COLOR_TEXTO_MUTED,
    COLOR_TEXTO_TITULO,
    FUENTE_BOTON,
    FUENTE_MUTED,
    FUENTE_SUBTITULO,
    FUENTE_TEXTO,
    FUENTE_TITULO_MEDIO,
    RADIO_BOTON,
    RADIO_ENTRY,
    RADIO_PANEL,
    RADIO_TARJETA,
)


class UsersView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        user_service: UserService,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._usuario: Usuario = usuario
        self._user_service: UserService = user_service

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._crear_encabezado()
        self._crear_cuerpo()
        self._cargar_datos()

    def _crear_encabezado(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL, height=54)
        bar.grid(row=0, column=0, padx=16, pady=12, sticky="ew")

        lbl_tit = ctk.CTkLabel(
            bar,
            text="👥 Gestión de Personal y Accesos",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_tit.pack(side="left", padx=16, pady=10)

        btn_nuevo = ctk.CTkButton(
            bar,
            text="+ Nuevo Empleado / Admin",
            font=FUENTE_BOTON,
            height=32,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_ACENTO_CYAN,
            text_color="#141B24",
            command=self._modal_nuevo_usuario,
        )
        btn_nuevo.pack(side="right", padx=16)

    def _crear_cuerpo(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def _cargar_datos(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        try:
            usuarios = self._user_service.listar_usuarios(self._usuario)
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)
            return

        for u in usuarios:
            fila = ctk.CTkFrame(self._scroll, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_TARJETA)
            fila.pack(fill="x", pady=4)
            fila.grid_columnconfigure(1, weight=1)

            lbl_id = ctk.CTkLabel(fila, text=f"#{u.id_usuario}", font=FUENTE_MUTED, text_color=COLOR_TEXTO_MUTED, width=40)
            lbl_id.grid(row=0, column=0, padx=8, pady=10)

            rol_txt = "👑 Administrador" if u.es_administrador() else "👤 Empleado"
            lbl_info = ctk.CTkLabel(
                fila,
                text=f"{u.nombre} (@{u.username})  —  {rol_txt}",
                font=FUENTE_SUBTITULO,
                text_color=COLOR_TEXTO_TITULO,
                anchor="w",
            )
            lbl_info.grid(row=0, column=1, padx=8, pady=10, sticky="w")

            estado_txt = "🟢 Activo" if u.es_activo() else "🔴 Inactivo"
            lbl_est = ctk.CTkLabel(
                fila,
                text=estado_txt,
                font=FUENTE_MUTED,
                text_color=COLOR_EXITO if u.es_activo() else COLOR_PELIGRO,
                width=80,
            )
            lbl_est.grid(row=0, column=2, padx=8, pady=10)

            btn_toggle = ctk.CTkButton(
                fila,
                text="Desactivar" if u.es_activo() else "Activar",
                width=85,
                height=28,
                font=FUENTE_MUTED,
                corner_radius=8,
                fg_color=COLOR_BOTON_SECUNDARIO,
                hover_color=COLOR_SUPERFICIE_HOVER,
                command=lambda user=u: self._toggle_estado(user),
            )
            btn_toggle.grid(row=0, column=3, padx=6, pady=10)

    def _toggle_estado(self, user: Usuario) -> None:
        nuevo = 0 if user.es_activo() else 1
        try:
            self._user_service.cambiar_estado(self._usuario, user.id_usuario or 0, nuevo)
            self._cargar_datos()
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)

    def _modal_nuevo_usuario(self) -> None:
        modal = ctk.CTkToplevel(self.winfo_toplevel())
        modal.title("Nuevo Usuario")
        modal.geometry("380x430")
        modal.resizable(False, False)
        modal.configure(fg_color=COLOR_FONDO_VENTANA)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        contenedor = ctk.CTkFrame(modal, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(contenedor, text="Registrar Personal", font=FUENTE_TITULO_MEDIO, text_color=COLOR_TEXTO_TITULO).pack(pady=(16, 12))

        ctk.CTkLabel(contenedor, text="Nombre Completo:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_nom = ctk.CTkEntry(contenedor, placeholder_text="Ej: Carlos Gómez", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_nom.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(contenedor, text="Nombre de Usuario:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_user = ctk.CTkEntry(contenedor, placeholder_text="Ej: carlos", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_user.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(contenedor, text="Contraseña:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_pass = ctk.CTkEntry(contenedor, placeholder_text="Mínimo 6 caracteres", show="•", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_pass.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(contenedor, text="Rol:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        cb_rol = ctk.CTkComboBox(contenedor, values=["Empleado (Solo POS/Caja)", "Administrador (Control Total)"], font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        cb_rol.pack(fill="x", padx=20, pady=(2, 16))

        def guardar():
            nom = e_nom.get().strip()
            username = e_user.get().strip()
            pwd = e_pass.get()
            rol_id = 1 if "Administrador" in cb_rol.get() else 2
            try:
                self._user_service.crear_usuario(
                    autor=self._usuario,
                    nombre=nom,
                    username=username,
                    password_plana=pwd,
                    id_rol=rol_id,
                )
                modal.grab_release()
                modal.destroy()
                self._cargar_datos()
            except HeladeriaPOSException as exc:
                msgbox.showerror("Error", exc.mensaje)

        ctk.CTkButton(contenedor, text="Crear Usuario", font=FUENTE_BOTON, height=38, corner_radius=RADIO_BOTON, fg_color=COLOR_COBRO_FRAMBUESA, command=guardar).pack(fill="x", padx=20, pady=(0, 16))
