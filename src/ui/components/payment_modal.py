from __future__ import annotations

from typing import Callable, Optional
import customtkinter as ctk

from src.ui.theme import (
    COLOR_ACENTO_CELESTE,
    COLOR_ACENTO_CYAN,
    COLOR_BORDE_SUAVE,
    COLOR_BOTON_SECUNDARIO,
    COLOR_BOTON_SECUNDARIO_HOVER,
    COLOR_COBRO_FRAMBUESA,
    COLOR_COBRO_HOVER,
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
    FUENTE_FAMILIA,
    FUENTE_MUTED,
    FUENTE_SUBTITULO,
    FUENTE_TEXTO,
    FUENTE_TITULO_MEDIO,
    FUENTE_TOTAL_POS,
    RADIO_BOTON,
    RADIO_ENTRY,
    RADIO_MODAL,
)


class PaymentModal(ctk.CTkToplevel):

    METODOS: list[tuple[str, str]] = [
        ("EFECTIVO", "💵 Efectivo"),
        ("TRANSFERENCIA", "📱 Nequi / Daviplata / QR"),
        ("TARJETA", "💳 Tarjeta Débito / Crédito"),
    ]

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        total: float,
        on_confirm: Callable[[str, float], None],
        on_cancel: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)
        self._total: float = round(total, 2)
        self._on_confirm: Callable[[str, float], None] = on_confirm
        self._on_cancel: Optional[Callable[[], None]] = on_cancel
        self._metodo_seleccionado: str = "EFECTIVO"
        self._botones_metodo: dict[str, ctk.CTkButton] = {}

        self.title("Cobro de Venta")
        self.geometry("480x540")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO_VENTANA)

        self.transient(parent)
        self.grab_set()

        self._centrar_ventana(parent)
        self._construir_interfaz()

    def _centrar_ventana(self, parent: ctk.CTkBaseClass) -> None:
        self.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + (pw - 480) // 2
            y = py + (ph - 540) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _construir_interfaz(self) -> None:
        contenedor = ctk.CTkFrame(
            self,
            fg_color=COLOR_SUPERFICIE,
            corner_radius=RADIO_MODAL,
            border_width=2,
            border_color=COLOR_DORADO_PREMIUM,
        )
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)

        lbl_titulo = ctk.CTkLabel(
            contenedor,
            text="Cobro de Comanda",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_titulo.pack(pady=(16, 4))

        frame_total = ctk.CTkFrame(contenedor, fg_color="transparent")
        frame_total.pack(pady=4)

        ctk.CTkLabel(
            frame_total,
            text="TOTAL A PAGAR",
            font=FUENTE_MUTED,
            text_color=COLOR_TEXTO_MUTED,
        ).pack()

        lbl_total = ctk.CTkLabel(
            frame_total,
            text=f"${self._total:,.2f}",
            font=FUENTE_TOTAL_POS,
            text_color=COLOR_DORADO_PREMIUM,
        )
        lbl_total.pack()

        divisor = ctk.CTkFrame(contenedor, fg_color=COLOR_BORDE_SUAVE, height=1)
        divisor.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(
            contenedor,
            text="Selecciona Método de Pago:",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(4, 6))

        frame_metodos = ctk.CTkFrame(contenedor, fg_color="transparent")
        frame_metodos.pack(fill="x", padx=20, pady=4)
        for clave, etiqueta in self.METODOS:
            btn = ctk.CTkButton(
                frame_metodos,
                text=etiqueta,
                font=FUENTE_BOTON,
                height=36,
                corner_radius=RADIO_BOTON,
                fg_color=COLOR_ACENTO_CYAN if clave == "EFECTIVO" else COLOR_BOTON_SECUNDARIO,
                text_color="#141B24" if clave == "EFECTIVO" else COLOR_TEXTO_CUERPO,
                hover_color=COLOR_ACENTO_CELESTE,
                command=lambda k=clave: self._seleccionar_metodo(k),
            )
            btn.pack(fill="x", pady=3)
            self._botones_metodo[clave] = btn

        self._frame_efectivo = ctk.CTkFrame(contenedor, fg_color="transparent")
        self._frame_efectivo.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(
            self._frame_efectivo,
            text="Dinero Recibido ($):",
            font=FUENTE_TEXTO,
            text_color=COLOR_TEXTO_CUERPO,
            anchor="w",
        ).pack(fill="x")

        self._entry_recibido = ctk.CTkEntry(
            self._frame_efectivo,
            font=(FUENTE_FAMILIA, 16, "bold"),
            height=38,
            corner_radius=RADIO_ENTRY,
            fg_color=COLOR_FONDO_VENTANA,
            border_color=COLOR_BORDE_SUAVE,
            text_color=COLOR_TEXTO_TITULO,
        )
        self._entry_recibido.pack(fill="x", pady=(2, 6))
        self._entry_recibido.insert(0, str(int(self._total)))
        self._entry_recibido.bind("<KeyRelease>", self._al_cambiar_recibido)

        frame_rapidos = ctk.CTkFrame(self._frame_efectivo, fg_color="transparent")
        frame_rapidos.pack(fill="x", pady=2)
        valores_rapidos = [
            ("Exacto", self._total),
            ("$20k", 20000.0),
            ("$50k", 50000.0),
            ("$100k", 100000.0),
        ]
        for txt, val in valores_rapidos:
            btn_rap = ctk.CTkButton(
                frame_rapidos,
                text=txt,
                width=64,
                height=26,
                font=FUENTE_MUTED,
                corner_radius=8,
                fg_color=COLOR_BOTON_SECUNDARIO,
                hover_color=COLOR_BOTON_SECUNDARIO_HOVER,
                command=lambda v=val: self._asignar_recibido(v),
            )
            btn_rap.pack(side="left", padx=2, expand=True)

        frame_cambio = ctk.CTkFrame(self._frame_efectivo, fg_color="transparent")
        frame_cambio.pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(
            frame_cambio,
            text="Cambio / Devuelta:",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
        ).pack(side="left")
        self._lbl_cambio = ctk.CTkLabel(
            frame_cambio,
            text="$0.00",
            font=(FUENTE_FAMILIA, 18, "bold"),
            text_color=COLOR_EXITO,
        )
        self._lbl_cambio.pack(side="right")

        self._lbl_error = ctk.CTkLabel(
            contenedor,
            text="",
            font=FUENTE_MUTED,
            text_color=COLOR_PELIGRO,
        )
        self._lbl_error.pack(pady=2)

        frame_acciones = ctk.CTkFrame(contenedor, fg_color="transparent")
        frame_acciones.pack(fill="x", padx=20, pady=(6, 12), side="bottom")

        btn_cancelar = ctk.CTkButton(
            frame_acciones,
            text="Cancelar",
            font=FUENTE_BOTON,
            height=40,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_BOTON_SECUNDARIO,
            hover_color=COLOR_BOTON_SECUNDARIO_HOVER,
            command=self._cancelar,
        )
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._btn_confirmar = ctk.CTkButton(
            frame_acciones,
            text="Confirmar Venta",
            font=(FUENTE_FAMILIA, 14, "bold"),
            height=40,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_COBRO_FRAMBUESA,
            hover_color=COLOR_COBRO_HOVER,
            command=self._confirmar,
        )
        self._btn_confirmar.pack(side="right", fill="x", expand=True, padx=(6, 0))

        self._calcular_cambio_actual()

    def _seleccionar_metodo(self, metodo: str) -> None:
        self._metodo_seleccionado = metodo
        for clave, btn in self._botones_metodo.items():
            if clave == metodo:
                btn.configure(
                    fg_color=COLOR_ACENTO_CYAN,
                    text_color="#141B24",
                )
            else:
                btn.configure(
                    fg_color=COLOR_BOTON_SECUNDARIO,
                    text_color=COLOR_TEXTO_CUERPO,
                )

        if metodo == "EFECTIVO":
            self._frame_efectivo.pack(fill="x", padx=20, pady=8)
            self._calcular_cambio_actual()
        else:
            self._frame_efectivo.pack_forget()
            self._lbl_error.configure(text="")
            self._btn_confirmar.configure(state="normal")

    def _asignar_recibido(self, valor: float) -> None:
        self._entry_recibido.delete(0, "end")
        self._entry_recibido.insert(0, str(int(valor)))
        self._calcular_cambio_actual()

    def _al_cambiar_recibido(self, event=None) -> None:
        self._calcular_cambio_actual()

    def _calcular_cambio_actual(self) -> None:
        if self._metodo_seleccionado != "EFECTIVO":
            return
        txt = self._entry_recibido.get().strip().replace(",", ".")
        try:
            recibido = float(txt) if txt else 0.0
        except ValueError:
            self._lbl_cambio.configure(text="---", text_color=COLOR_PELIGRO)
            self._lbl_error.configure(text="Monto recibido no numérico.")
            self._btn_confirmar.configure(state="disabled")
            return

        if recibido < self._total:
            faltante = self._total - recibido
            self._lbl_cambio.configure(text=f"Faltan ${faltante:,.2f}", text_color=COLOR_PELIGRO)
            self._lbl_error.configure(text="El dinero recibido es menor al total.")
            self._btn_confirmar.configure(state="disabled")
        else:
            cambio = recibido - self._total
            self._lbl_cambio.configure(text=f"${cambio:,.2f}", text_color=COLOR_EXITO)
            self._lbl_error.configure(text="")
            self._btn_confirmar.configure(state="normal")

    def _confirmar(self) -> None:
        if self._metodo_seleccionado == "EFECTIVO":
            try:
                recibido = float(self._entry_recibido.get().strip().replace(",", "."))
            except ValueError:
                return
            if recibido < self._total:
                return
        else:
            recibido = self._total

        self.grab_release()
        self.destroy()
        self._on_confirm(self._metodo_seleccionado, recibido)

    def _cancelar(self) -> None:
        self.grab_release()
        self.destroy()
        if self._on_cancel:
            self._on_cancel()
