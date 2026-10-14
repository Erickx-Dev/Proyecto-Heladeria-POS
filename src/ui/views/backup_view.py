from __future__ import annotations

import os
from pathlib import Path
from tkinter import filedialog
import tkinter.messagebox as msgbox
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.user import Usuario
from src.services.backup_service import BackupService
from src.ui.theme import (
    COLOR_ACENTO_CYAN,
    COLOR_BORDE_SUAVE,
    COLOR_BOTON_SECUNDARIO,
    COLOR_BOTON_SECUNDARIO_HOVER,
    COLOR_DORADO_PREMIUM,
    COLOR_EXITO,
    COLOR_FONDO_VENTANA,
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
    RADIO_PANEL,
    RADIO_TARJETA,
)


class BackupView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        backup_service: BackupService,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._usuario: Usuario = usuario
        self._backup_service: BackupService = backup_service

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
            text="💾 Respaldo y Copia de Seguridad Física (SQLite)",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_tit.pack(side="left", padx=16, pady=10)

    def _crear_cuerpo(self) -> None:
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(0, weight=4)
        cuerpo.grid_columnconfigure(1, weight=6)

        panel_accion = ctk.CTkFrame(cuerpo, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        panel_accion.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        ctk.CTkLabel(panel_accion, text="Generar Copia de Seguridad", font=FUENTE_SUBTITULO, text_color=COLOR_TEXTO_TITULO).pack(padx=16, pady=(16, 8), anchor="w")

        ctk.CTkLabel(
            panel_accion,
            text="Crea una copia física íntegra de la base de datos (ventas, stock, usuarios) sellada en tiempo. "
            "Puedes guardarla en la carpeta local o en una memoria USB.",
            font=FUENTE_TEXTO,
            text_color=COLOR_TEXTO_MUTED,
            wraplength=280,
            justify="left",
        ).pack(padx=16, pady=4, anchor="w")

        btn_backup_auto = ctk.CTkButton(
            panel_accion,
            text="⚡ Respaldo en Carpeta Local",
            font=FUENTE_BOTON,
            height=40,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_ACENTO_CYAN,
            text_color="#141B24",
            command=self._generar_respaldo_defecto,
        )
        btn_backup_auto.pack(fill="x", padx=16, pady=(16, 6))

        btn_backup_usb = ctk.CTkButton(
            panel_accion,
            text="📁 Exportar a Carpeta / USB...",
            font=FUENTE_BOTON,
            height=40,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_BOTON_SECUNDARIO,
            hover_color=COLOR_BOTON_SECUNDARIO_HOVER,
            command=self._generar_respaldo_usb,
        )
        btn_backup_usb.pack(fill="x", padx=16, pady=(0, 16))

        panel_lista = ctk.CTkFrame(cuerpo, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        panel_lista.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        panel_lista.grid_rowconfigure(1, weight=1)
        panel_lista.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel_lista, text="Respaldos Disponibles en Carpeta Local", font=FUENTE_SUBTITULO, text_color=COLOR_TEXTO_TITULO).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        self._scroll = ctk.CTkScrollableFrame(panel_lista, fg_color="transparent")
        self._scroll.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def _cargar_datos(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        try:
            respaldos = self._backup_service.listar_respaldos(self._usuario)
        except Exception:
            respaldos = []

        if not respaldos:
            ctk.CTkLabel(
                self._scroll,
                text="No hay respaldos generados aún en la carpeta local.",
                font=FUENTE_TEXTO,
                text_color=COLOR_TEXTO_MUTED,
            ).pack(pady=40)
            return

        for p in respaldos:
            fila = ctk.CTkFrame(self._scroll, fg_color=COLOR_SUPERFICIE_HOVER, corner_radius=RADIO_TARJETA)
            fila.pack(fill="x", pady=4)
            fila.grid_columnconfigure(0, weight=1)

            peso_kb = round(p.stat().st_size / 1024, 1)
            ctk.CTkLabel(fila, text=f"💾 {p.name}", font=FUENTE_BOTON, text_color=COLOR_TEXTO_TITULO, anchor="w").grid(row=0, column=0, padx=12, pady=8, sticky="w")
            ctk.CTkLabel(fila, text=f"{peso_kb} KB", font=FUENTE_MUTED, text_color=COLOR_DORADO_PREMIUM).grid(row=0, column=1, padx=12, pady=8)

    def _generar_respaldo_defecto(self) -> None:
        try:
            ruta = self._backup_service.crear_respaldo(self._usuario)
            msgbox.showinfo("Respaldo Creado", f"✅ Copia de seguridad física creada exitosamente:\n\n{ruta.name}")
            self._cargar_datos()
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)
        except Exception as exc:
            msgbox.showerror("Error", f"Fallo al crear respaldo: {exc}")

    def _generar_respaldo_usb(self) -> None:
        carpeta = filedialog.askdirectory(title="Selecciona la carpeta o memoria USB de destino")
        if not carpeta:
            return
        try:
            ruta = self._backup_service.crear_respaldo(self._usuario, destino_dir=carpeta)
            msgbox.showinfo("Respaldo Creado", f"✅ Copia de seguridad guardada exitosamente en:\n\n{ruta}")
            self._cargar_datos()
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)
        except Exception as exc:
            msgbox.showerror("Error", f"Fallo al exportar respaldo: {exc}")
