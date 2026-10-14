from __future__ import annotations

import tkinter.messagebox as msgbox
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.user import Usuario
from src.services.expense_service import ExpenseService
from src.ui.theme import (
    COLOR_ADVERTENCIA,
    COLOR_BORDE_SUAVE,
    COLOR_DORADO_PREMIUM,
    COLOR_FONDO_VENTANA,
    COLOR_PELIGRO,
    COLOR_PELIGRO_HOVER,
    COLOR_SUPERFICIE,
    COLOR_SUPERFICIE_HOVER,
    COLOR_TEXTO_CUERPO,
    COLOR_TEXTO_MUTED,
    COLOR_TEXTO_TITULO,
    FUENTE_BOTON,
    FUENTE_FAMILIA,
    FUENTE_MUTED,
    FUENTE_SUBTITULO,
    FUENTE_TEXTO,
    FUENTE_TITULO_MEDIO,
    RADIO_BOTON,
    RADIO_ENTRY,
    RADIO_PANEL,
    RADIO_TARJETA,
)


class ExpenseView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        expense_service: ExpenseService,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._usuario: Usuario = usuario
        self._expense_service: ExpenseService = expense_service

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
            text="💸 Gastos Menores de Caja",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_tit.pack(side="left", padx=16, pady=10)

        self._lbl_total_gastos = ctk.CTkLabel(
            bar,
            text="",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_ADVERTENCIA,
        )
        self._lbl_total_gastos.pack(side="right", padx=16)

    def _crear_cuerpo(self) -> None:
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(0, weight=4)
        cuerpo.grid_columnconfigure(1, weight=6)

        self._form = ctk.CTkFrame(cuerpo, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        self._form.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        ctk.CTkLabel(self._form, text="Registrar Egreso Menor", font=FUENTE_SUBTITULO, text_color=COLOR_TEXTO_TITULO).pack(padx=16, pady=(16, 12), anchor="w")

        ctk.CTkLabel(self._form, text="Monto del Gasto ($):", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=16)
        self._e_monto = ctk.CTkEntry(self._form, placeholder_text="Ej: 8000", font=(FUENTE_FAMILIA, 14, "bold"), corner_radius=RADIO_ENTRY)
        self._e_monto.pack(fill="x", padx=16, pady=(2, 10))

        ctk.CTkLabel(self._form, text="Justificación / Motivo:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=16)
        self._e_desc = ctk.CTkEntry(self._form, placeholder_text="Ej: Bolsa de hielo para nevera", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        self._e_desc.pack(fill="x", padx=16, pady=(2, 16))

        btn_guardar = ctk.CTkButton(
            self._form,
            text="Registrar Egreso",
            font=FUENTE_BOTON,
            height=38,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_PELIGRO,
            hover_color=COLOR_PELIGRO_HOVER,
            command=self._registrar_gasto,
        )
        btn_guardar.pack(fill="x", padx=16, pady=(0, 16))

        panel_lista = ctk.CTkFrame(cuerpo, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        panel_lista.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        panel_lista.grid_rowconfigure(1, weight=1)
        panel_lista.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel_lista, text="Gastos Registrados en Turno Activo", font=FUENTE_SUBTITULO, text_color=COLOR_TEXTO_TITULO).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        self._scroll_gastos = ctk.CTkScrollableFrame(panel_lista, fg_color="transparent")
        self._scroll_gastos.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._scroll_gastos.grid_columnconfigure(0, weight=1)

    def _cargar_datos(self) -> None:
        for w in self._scroll_gastos.winfo_children():
            w.destroy()

        try:
            gastos = self._expense_service.listar_gastos_turno_activo()
            total = self._expense_service.obtener_total_gastos_turno_activo()
            self._lbl_total_gastos.configure(text=f"Total Turno: ${total:,.2f}")
        except Exception:
            self._lbl_total_gastos.configure(text="")
            ctk.CTkLabel(
                self._scroll_gastos,
                text="No hay un turno de caja abierto para registrar o ver gastos.",
                font=FUENTE_TEXTO,
                text_color=COLOR_TEXTO_MUTED,
            ).pack(pady=40)
            return

        if not gastos:
            ctk.CTkLabel(
                self._scroll_gastos,
                text="No se han registrado gastos en este turno.",
                font=FUENTE_TEXTO,
                text_color=COLOR_TEXTO_MUTED,
            ).pack(pady=40)
            return

        for g in gastos:
            fila = ctk.CTkFrame(self._scroll_gastos, fg_color=COLOR_SUPERFICIE_HOVER, corner_radius=RADIO_TARJETA)
            fila.pack(fill="x", pady=4)
            fila.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(fila, text=g.descripcion, font=FUENTE_BOTON, text_color=COLOR_TEXTO_TITULO, anchor="w").grid(row=0, column=0, padx=12, pady=(8, 2), sticky="w")
            ctk.CTkLabel(fila, text=g.fecha_hora, font=FUENTE_MUTED, text_color=COLOR_TEXTO_MUTED, anchor="w").grid(row=1, column=0, padx=12, pady=(0, 8), sticky="w")
            ctk.CTkLabel(fila, text=f"-${g.monto:,.2f}", font=FUENTE_SUBTITULO, text_color=COLOR_PELIGRO).grid(row=0, column=1, rowspan=2, padx=14, pady=8)

    def _registrar_gasto(self) -> None:
        txt_monto = self._e_monto.get().strip().replace(",", ".")
        desc = self._e_desc.get().strip()
        try:
            monto = float(txt_monto)
            self._expense_service.registrar_gasto(self._usuario.id_usuario or 1, monto, desc)
            msgbox.showinfo("Gasto Registrado", f"Egreso de ${monto:,.2f} registrado correctamente.")
            self._e_monto.delete(0, "end")
            self._e_desc.delete(0, "end")
            self._cargar_datos()
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)
        except ValueError:
            msgbox.showerror("Error", "El monto debe ser un valor numérico.")
