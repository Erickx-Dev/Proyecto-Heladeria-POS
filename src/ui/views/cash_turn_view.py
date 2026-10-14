from __future__ import annotations

from typing import Optional
import tkinter.messagebox as msgbox
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.cash_register import TurnoCaja
from src.domain.user import Usuario
from src.services.cash_service import CashService
from src.ui.theme import (
    COLOR_ACENTO_CYAN,
    COLOR_ADVERTENCIA,
    COLOR_BORDE_SUAVE,
    COLOR_BOTON_SECUNDARIO,
    COLOR_BOTON_SECUNDARIO_HOVER,
    COLOR_COBRO_FRAMBUESA,
    COLOR_COBRO_HOVER,
    COLOR_DORADO_PREMIUM,
    COLOR_EXITO,
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
    FUENTE_TOTAL_POS,
    RADIO_BOTON,
    RADIO_ENTRY,
    RADIO_PANEL,
    RADIO_TARJETA,
)


class CashTurnView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        cash_service: CashService,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._usuario: Usuario = usuario
        self._cash_service: CashService = cash_service

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._crear_encabezado()
        self._contenedor_principal = ctk.CTkFrame(self, fg_color="transparent")
        self._contenedor_principal.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._contenedor_principal.grid_rowconfigure(0, weight=1)
        self._contenedor_principal.grid_columnconfigure(0, weight=1)

        self._refrescar_vista()

    def _crear_encabezado(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL, height=54)
        bar.grid(row=0, column=0, padx=16, pady=12, sticky="ew")

        lbl_tit = ctk.CTkLabel(
            bar,
            text="💵 Control de Caja y Turnos",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_tit.pack(side="left", padx=16, pady=10)

        btn_refrescar = ctk.CTkButton(
            bar,
            text="🔄 Actualizar",
            width=90,
            height=32,
            font=FUENTE_BOTON,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLOR_BORDE_SUAVE,
            border_width=1,
            border_color=COLOR_BORDE_SUAVE,
            command=self._refrescar_vista,
        )
        btn_refrescar.pack(side="right", padx=16)

    def _refrescar_vista(self) -> None:
        for w in self._contenedor_principal.winfo_children():
            w.destroy()

        try:
            caja = self._cash_service.obtener_turno_activo()
            self._construir_caja_abierta(caja)
        except Exception:
            self._construir_caja_cerrada()

    def _construir_caja_cerrada(self) -> None:
        tarjeta = ctk.CTkFrame(
            self._contenedor_principal,
            fg_color=COLOR_SUPERFICIE,
            corner_radius=RADIO_PANEL,
            border_width=1,
            border_color=COLOR_BORDE_SUAVE,
            width=420,
        )
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")

        lbl_icon = ctk.CTkLabel(
            tarjeta,
            text="🔒",
            font=(FUENTE_FAMILIA, 42),
        )
        lbl_icon.pack(pady=(24, 6))

        lbl_tit = ctk.CTkLabel(
            tarjeta,
            text="No Hay Turno de Caja Abierto",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_tit.pack(pady=4)

        lbl_desc = ctk.CTkLabel(
            tarjeta,
            text="Ingresa el monto de fondo base para abrir el turno e iniciar ventas:",
            font=FUENTE_TEXTO,
            text_color=COLOR_TEXTO_MUTED,
            wraplength=340,
            justify="center",
        )
        lbl_desc.pack(padx=24, pady=8)

        self._entry_base = ctk.CTkEntry(
            tarjeta,
            placeholder_text="Ej: 50000",
            font=(FUENTE_FAMILIA, 16, "bold"),
            height=40,
            corner_radius=RADIO_ENTRY,
            fg_color=COLOR_FONDO_VENTANA,
            border_color=COLOR_BORDE_SUAVE,
            text_color=COLOR_TEXTO_TITULO,
        )
        self._entry_base.pack(fill="x", padx=36, pady=8)
        self._entry_base.insert(0, "50000")

        btn_abrir = ctk.CTkButton(
            tarjeta,
            text="🔓 Abrir Turno de Caja",
            font=FUENTE_BOTON,
            height=42,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_EXITO,
            hover_color=COLOR_SUPERFICIE_HOVER,
            command=self._abrir_caja,
        )
        btn_abrir.pack(fill="x", padx=36, pady=(12, 28))

    def _construir_caja_abierta(self, caja: TurnoCaja) -> None:
        contenedor = ctk.CTkScrollableFrame(self._contenedor_principal, fg_color="transparent")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_columnconfigure((0, 1, 2, 3), weight=1)

        saldo_disp = self._cash_service.obtener_saldo_disponible(caja.id_caja)
        ventas_efectivo = round(saldo_disp - caja.monto_inicial, 2)

        tarjetas_info = [
            ("Monto Base Inicial", f"${caja.monto_inicial:,.2f}", COLOR_TEXTO_TITULO),
            ("Apertura", caja.fecha_apertura, COLOR_ACENTO_CELESTE),
            ("Saldo Disponible", f"${saldo_disp:,.2f}", COLOR_DORADO_PREMIUM),
            ("Estado", "🟢 ABIERTA", COLOR_EXITO),
        ]

        for idx, (tit, val, col) in enumerate(tarjetas_info):
            card = ctk.CTkFrame(contenedor, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_TARJETA)
            card.grid(row=0, column=idx, padx=6, pady=6, sticky="ew")
            ctk.CTkLabel(card, text=tit, font=FUENTE_MUTED, text_color=COLOR_TEXTO_MUTED).pack(padx=12, pady=(10, 2), anchor="w")
            ctk.CTkLabel(card, text=val, font=FUENTE_SUBTITULO, text_color=col).pack(padx=12, pady=(0, 10), anchor="w")

        panel_arqueo = ctk.CTkFrame(
            contenedor,
            fg_color=COLOR_SUPERFICIE,
            corner_radius=RADIO_PANEL,
            border_width=1,
            border_color=COLOR_DORADO_PREMIUM,
        )
        panel_arqueo.grid(row=1, column=0, columnspan=4, padx=6, pady=16, sticky="ew")

        ctk.CTkLabel(
            panel_arqueo,
            text="Cierre de Turno y Arqueo Físico",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        ).pack(padx=20, pady=(18, 4), anchor="w")

        ctk.CTkLabel(
            panel_arqueo,
            text=f"Saldo esperado en gaveta según sistema: ${saldo_disp:,.2f}",
            font=FUENTE_TEXTO,
            text_color=COLOR_DORADO_PREMIUM,
        ).pack(padx=20, pady=(0, 12), anchor="w")

        ctk.CTkLabel(
            panel_arqueo,
            text="Dinero Físico Real Contado en Gaveta ($):",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
        ).pack(padx=20, pady=(4, 2), anchor="w")

        self._entry_real = ctk.CTkEntry(
            panel_arqueo,
            font=(FUENTE_FAMILIA, 16, "bold"),
            height=40,
            corner_radius=RADIO_ENTRY,
            fg_color=COLOR_FONDO_VENTANA,
            border_color=COLOR_BORDE_SUAVE,
            text_color=COLOR_TEXTO_TITULO,
        )
        self._entry_real.pack(fill="x", padx=20, pady=4)
        self._entry_real.insert(0, str(int(saldo_disp)))

        btn_cerrar = ctk.CTkButton(
            panel_arqueo,
            text="🔒 Conciliar Arqueo y Cerrar Turno",
            font=(FUENTE_FAMILIA, 14, "bold"),
            height=44,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_PELIGRO,
            hover_color=COLOR_PELIGRO_HOVER,
            command=self._cerrar_caja,
        )
        btn_cerrar.pack(fill="x", padx=20, pady=(16, 22))

    def _abrir_caja(self) -> None:
        txt = self._entry_base.get().strip().replace(",", ".")
        try:
            monto = float(txt)
            self._cash_service.abrir_turno(self._usuario.id_usuario or 1, monto)
            msgbox.showinfo("Caja Abierta", f"Turno abierto exitosamente con fondo de ${monto:,.2f}.")
            self._refrescar_vista()
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)
        except Exception as exc:
            msgbox.showerror("Error", f"Error al abrir caja: {exc}")

    def _cerrar_caja(self) -> None:
        txt = self._entry_real.get().strip().replace(",", ".")
        try:
            monto_real = float(txt)
            if not msgbox.askyesno("Confirmar Cierre", "¿Está seguro de conciliar el arqueo y cerrar el turno?"):
                return
            arqueo = self._cash_service.cerrar_turno(self._usuario.id_usuario or 1, monto_real)
            msgbox.showinfo(
                "Turno Cerrado",
                f"✅ Turno cerrado con éxito.\n\n"
                f"Saldo Esperado: ${arqueo.saldo_esperado:,.2f}\n"
                f"Físico Declarado: ${arqueo.monto_fisico_real:,.2f}\n"
                f"Diferencia: ${arqueo.diferencia:,.2f} ({arqueo.tipo_diferencia})",
            )
            self._refrescar_vista()
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)
        except Exception as exc:
            msgbox.showerror("Error", f"Error al cerrar caja: {exc}")
