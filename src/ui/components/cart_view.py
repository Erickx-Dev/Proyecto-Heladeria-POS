from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List
import customtkinter as ctk

from src.domain.product import Producto
from src.ui.theme import (
    COLOR_BORDE_SUAVE,
    COLOR_BOTON_SECUNDARIO,
    COLOR_BOTON_SECUNDARIO_HOVER,
    COLOR_COBRO_FRAMBUESA,
    COLOR_COBRO_HOVER,
    COLOR_DORADO_PREMIUM,
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
    FUENTE_TOTAL_POS,
    RADIO_BOTON,
    RADIO_PANEL,
    RADIO_TARJETA,
)


@dataclass
class LineaComanda:
    producto: Producto
    cantidad: int = 1

    @property
    def subtotal(self) -> float:
        return round(self.producto.precio_venta * self.cantidad, 2)


class CartView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_checkout: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLOR_SUPERFICIE,
            corner_radius=RADIO_PANEL,
            border_width=1,
            border_color=COLOR_BORDE_SUAVE,
            width=320,
            **kwargs,
        )
        self._on_checkout: Callable[[], None] = on_checkout
        self._lineas: Dict[int, LineaComanda] = {}

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._crear_encabezado()
        self._crear_lista_scroll()
        self._crear_pie_totales()
        self._actualizar_vista()

    def _crear_encabezado(self) -> None:
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        frame_header.grid_columnconfigure(0, weight=1)

        lbl_titulo = ctk.CTkLabel(
            frame_header,
            text="🧾 Comanda Actual",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
            anchor="w",
        )
        lbl_titulo.grid(row=0, column=0, sticky="w")

        self._lbl_contador = ctk.CTkLabel(
            frame_header,
            text="0 ítems",
            font=FUENTE_MUTED,
            text_color=COLOR_TEXTO_MUTED,
            anchor="e",
        )
        self._lbl_contador.grid(row=0, column=1, sticky="e")

        divisor = ctk.CTkFrame(self, fg_color=COLOR_BORDE_SUAVE, height=1)
        divisor.grid(row=0, column=0, padx=16, pady=(45, 0), sticky="ew")

    def _crear_lista_scroll(self) -> None:
        self._scroll_items = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
        )
        self._scroll_items.grid(row=1, column=0, padx=10, pady=8, sticky="nsew")
        self._scroll_items.grid_columnconfigure(0, weight=1)

    def _crear_pie_totales(self) -> None:
        frame_pie = ctk.CTkFrame(self, fg_color="transparent")
        frame_pie.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="ew")
        frame_pie.grid_columnconfigure(0, weight=1)

        divisor = ctk.CTkFrame(frame_pie, fg_color=COLOR_BORDE_SUAVE, height=1)
        divisor.pack(fill="x", pady=(0, 10))

        frame_sub = ctk.CTkFrame(frame_pie, fg_color="transparent")
        frame_sub.pack(fill="x", pady=2)
        ctk.CTkLabel(
            frame_sub,
            text="Subtotal:",
            font=FUENTE_TEXTO,
            text_color=COLOR_TEXTO_MUTED,
        ).pack(side="left")
        self._lbl_subtotal = ctk.CTkLabel(
            frame_sub,
            text="$0.00",
            font=FUENTE_TEXTO,
            text_color=COLOR_TEXTO_CUERPO,
        )
        self._lbl_subtotal.pack(side="right")

        frame_total = ctk.CTkFrame(frame_pie, fg_color="transparent")
        frame_total.pack(fill="x", pady=(4, 12))
        ctk.CTkLabel(
            frame_total,
            text="TOTAL:",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
        ).pack(side="left")
        self._lbl_total = ctk.CTkLabel(
            frame_total,
            text="$0.00",
            font=FUENTE_TOTAL_POS,
            text_color=COLOR_DORADO_PREMIUM,
        )
        self._lbl_total.pack(side="right")

        self._btn_cobrar = ctk.CTkButton(
            frame_pie,
            text="🍓 COBRAR VENTA",
            font=(FUENTE_FAMILIA, 15, "bold"),
            height=46,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_COBRO_FRAMBUESA,
            hover_color=COLOR_COBRO_HOVER,
            text_color=COLOR_TEXTO_TITULO,
            command=self._on_checkout,
        )
        self._btn_cobrar.pack(fill="x", pady=(0, 6))

        self._btn_vaciar = ctk.CTkButton(
            frame_pie,
            text="Vaciar Comanda",
            font=FUENTE_MUTED,
            height=28,
            corner_radius=RADIO_BOTON,
            fg_color="transparent",
            hover_color=COLOR_SUPERFICIE_HOVER,
            text_color=COLOR_TEXTO_MUTED,
            command=self.vaciar,
        )
        self._btn_vaciar.pack(fill="x")

    def agregar_producto(self, producto: Producto, cantidad: int = 1) -> None:
        if not producto.id_producto:
            return
        pid = producto.id_producto
        if pid in self._lineas:
            self._lineas[pid].cantidad += cantidad
        else:
            self._lineas[pid] = LineaComanda(producto=producto, cantidad=cantidad)
        self._actualizar_vista()

    def modificar_cantidad(self, id_producto: int, delta: int) -> None:
        if id_producto in self._lineas:
            nueva = self._lineas[id_producto].cantidad + delta
            if nueva <= 0:
                del self._lineas[id_producto]
            else:
                self._lineas[id_producto].cantidad = nueva
            self._actualizar_vista()

    def eliminar_linea(self, id_producto: int) -> None:
        if id_producto in self._lineas:
            del self._lineas[id_producto]
            self._actualizar_vista()

    def vaciar(self) -> None:
        self._lineas.clear()
        self._actualizar_vista()

    def obtener_items(self) -> List[tuple[int, int]]:
        return [(l.producto.id_producto, l.cantidad) for l in self._lineas.values() if l.producto.id_producto]

    @property
    def total(self) -> float:
        return round(sum(l.subtotal for l in self._lineas.values()), 2)

    def _actualizar_vista(self) -> None:
        for widget in self._scroll_items.winfo_children():
            widget.destroy()

        total_items: int = sum(l.cantidad for l in self._lineas.values())
        self._lbl_contador.configure(text=f"{total_items} ítem{'s' if total_items != 1 else ''}")

        if not self._lineas:
            lbl_vacio = ctk.CTkLabel(
                self._scroll_items,
                text="Comanda vacía\nAgrega productos del catálogo",
                font=FUENTE_TEXTO,
                text_color=COLOR_TEXTO_MUTED,
                justify="center",
            )
            lbl_vacio.pack(pady=40)
            self._btn_cobrar.configure(state="disabled")
            self._btn_vaciar.configure(state="disabled")
            self._lbl_subtotal.configure(text="$0.00")
            self._lbl_total.configure(text="$0.00")
            return

        self._btn_cobrar.configure(state="normal")
        self._btn_vaciar.configure(state="normal")

        for pid, linea in self._lineas.items():
            fila = ctk.CTkFrame(
                self._scroll_items,
                fg_color=COLOR_SUPERFICIE_HOVER,
                corner_radius=RADIO_TARJETA,
                border_width=1,
                border_color=COLOR_BORDE_SUAVE,
            )
            fila.pack(fill="x", pady=4)
            fila.grid_columnconfigure(0, weight=1)

            lbl_nombre = ctk.CTkLabel(
                fila,
                text=linea.producto.nombre,
                font=FUENTE_BOTON,
                text_color=COLOR_TEXTO_TITULO,
                anchor="w",
            )
            lbl_nombre.grid(row=0, column=0, padx=10, pady=(6, 2), sticky="w")

            controles = ctk.CTkFrame(fila, fg_color="transparent")
            controles.grid(row=1, column=0, padx=8, pady=(0, 6), sticky="ew")
            controles.grid_columnconfigure(3, weight=1)

            btn_menos = ctk.CTkButton(
                controles,
                text="-",
                width=24,
                height=24,
                corner_radius=6,
                font=FUENTE_BOTON,
                fg_color=COLOR_BOTON_SECUNDARIO,
                hover_color=COLOR_BOTON_SECUNDARIO_HOVER,
                text_color=COLOR_TEXTO_TITULO,
                command=lambda p=pid: self.modificar_cantidad(p, -1),
            )
            btn_menos.pack(side="left", padx=2)

            lbl_cant = ctk.CTkLabel(
                controles,
                text=str(linea.cantidad),
                font=(FUENTE_FAMILIA, 12, "bold"),
                width=30,
                text_color=COLOR_TEXTO_TITULO,
            )
            lbl_cant.pack(side="left", padx=2)

            btn_mas = ctk.CTkButton(
                controles,
                text="+",
                width=24,
                height=24,
                corner_radius=6,
                font=FUENTE_BOTON,
                fg_color=COLOR_BOTON_SECUNDARIO,
                hover_color=COLOR_BOTON_SECUNDARIO_HOVER,
                text_color=COLOR_TEXTO_TITULO,
                command=lambda p=pid: self.modificar_cantidad(p, 1),
            )
            btn_mas.pack(side="left", padx=2)

            lbl_sub = ctk.CTkLabel(
                controles,
                text=f"${linea.subtotal:,.2f}",
                font=FUENTE_BOTON,
                text_color=COLOR_DORADO_PREMIUM,
            )
            lbl_sub.pack(side="left", padx=(10, 0))

            btn_borrar = ctk.CTkButton(
                controles,
                text="🗑️",
                width=26,
                height=24,
                corner_radius=6,
                font=FUENTE_MUTED,
                fg_color="transparent",
                hover_color=COLOR_PELIGRO,
                command=lambda p=pid: self.eliminar_linea(p),
            )
            btn_borrar.pack(side="right")

        total_fmt = f"${self.total:,.2f}"
        self._lbl_subtotal.configure(text=total_fmt)
        self._lbl_total.configure(text=total_fmt)
