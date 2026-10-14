from __future__ import annotations

from typing import List
import tkinter.messagebox as msgbox
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.supply import Insumo
from src.domain.user import Usuario
from src.services.inventory_service import InventoryService
from src.ui.theme import (
    COLOR_ACENTO_CYAN,
    COLOR_ADVERTENCIA,
    COLOR_BORDE_SUAVE,
    COLOR_BOTON_SECUNDARIO,
    COLOR_COBRO_FRAMBUESA,
    COLOR_DORADO_PREMIUM,
    COLOR_EXITO,
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
    FUENTE_TITULO_MEDIO,
    RADIO_BOTON,
    RADIO_ENTRY,
    RADIO_PANEL,
    RADIO_TARJETA,
)


class InventoryView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        inventory_service: InventoryService,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._usuario: Usuario = usuario
        self._inventory_service: InventoryService = inventory_service

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
            text="📦 Control de Insumos y Bodega",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_tit.pack(side="left", padx=16, pady=10)

        btn_nuevo = ctk.CTkButton(
            bar,
            text="+ Nuevo Insumo",
            font=FUENTE_BOTON,
            height=32,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_ACENTO_CYAN,
            text_color="#141B24",
            command=self._modal_nuevo_insumo,
        )
        btn_nuevo.pack(side="right", padx=16)

    def _crear_cuerpo(self) -> None:
        self._scroll_tabla = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll_tabla.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll_tabla.grid_columnconfigure(0, weight=1)

    def _cargar_datos(self) -> None:
        for w in self._scroll_tabla.winfo_children():
            w.destroy()

        insumos = self._inventory_service.listar_insumos()
        alertas = {i.id_insumo for i in self._inventory_service.obtener_alertas_stock()}

        if not insumos:
            ctk.CTkLabel(
                self._scroll_tabla,
                text="No hay materias primas o insumos registrados.",
                font=FUENTE_TEXTO,
                text_color=COLOR_TEXTO_MUTED,
            ).pack(pady=30)
            return

        for ins in insumos:
            fila = ctk.CTkFrame(self._scroll_tabla, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_TARJETA)
            fila.pack(fill="x", pady=4)
            fila.grid_columnconfigure(0, weight=1)

            en_alerta = ins.id_insumo in alertas
            color_stock = COLOR_PELIGRO if en_alerta else COLOR_EXITO
            icono_alerta = "⚠️ ALERTA" if en_alerta else "🟢 OK"

            lbl_nom = ctk.CTkLabel(
                fila,
                text=f"{ins.nombre} ({ins.unidad_medida})",
                font=FUENTE_SUBTITULO,
                text_color=COLOR_TEXTO_TITULO,
                anchor="w",
            )
            lbl_nom.grid(row=0, column=0, padx=14, pady=10, sticky="w")

            lbl_cant = ctk.CTkLabel(
                fila,
                text=f"Stock: {ins.stock_actual} / Mín: {ins.stock_minimo}",
                font=FUENTE_BOTON,
                text_color=color_stock,
                width=160,
            )
            lbl_cant.grid(row=0, column=1, padx=8, pady=10)

            lbl_estado = ctk.CTkLabel(
                fila,
                text=icono_alerta,
                font=FUENTE_MUTED,
                text_color=color_stock,
                width=90,
            )
            lbl_estado.grid(row=0, column=2, padx=6, pady=10)

            btn_reabastecer = ctk.CTkButton(
                fila,
                text="+ Reabastecer",
                width=100,
                height=28,
                font=FUENTE_MUTED,
                corner_radius=8,
                fg_color=COLOR_BOTON_SECUNDARIO,
                hover_color=COLOR_BORDE_SUAVE,
                command=lambda item=ins: self._modal_reabastecer(item),
            )
            btn_reabastecer.grid(row=0, column=3, padx=12, pady=10)

    def _modal_nuevo_insumo(self) -> None:
        modal = ctk.CTkToplevel(self.winfo_toplevel())
        modal.title("Nuevo Insumo")
        modal.geometry("380x420")
        modal.resizable(False, False)
        modal.configure(fg_color=COLOR_FONDO_VENTANA)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        contenedor = ctk.CTkFrame(modal, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(contenedor, text="Registrar Insumo / Materia Prima", font=FUENTE_TITULO_MEDIO, text_color=COLOR_TEXTO_TITULO).pack(pady=(16, 12))

        ctk.CTkLabel(contenedor, text="Nombre:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_nom = ctk.CTkEntry(contenedor, placeholder_text="Ej: Leche Entera", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_nom.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(contenedor, text="Unidad de Medida:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_uni = ctk.CTkEntry(contenedor, placeholder_text="Ej: L, kg, unidades", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_uni.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(contenedor, text="Stock Inicial:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_ini = ctk.CTkEntry(contenedor, placeholder_text="Ej: 20.0", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_ini.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(contenedor, text="Stock Mínimo (Alerta):", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_min = ctk.CTkEntry(contenedor, placeholder_text="Ej: 5.0", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_min.pack(fill="x", padx=20, pady=(2, 16))

        def guardar():
            nom = e_nom.get().strip()
            uni = e_uni.get().strip()
            try:
                ini = float(e_ini.get().strip() or "0")
                smin = float(e_min.get().strip() or "0")
                self._inventory_service.crear_insumo(
                    autor=self._usuario,
                    nombre=nom,
                    unidad_medida=uni,
                    stock_inicial=ini,
                    stock_minimo=smin,
                )
                modal.grab_release()
                modal.destroy()
                self._cargar_datos()
            except HeladeriaPOSException as exc:
                msgbox.showerror("Error", exc.mensaje)
            except ValueError:
                msgbox.showerror("Error", "Los valores de stock deben ser numéricos.")

        ctk.CTkButton(contenedor, text="Guardar Insumo", font=FUENTE_BOTON, height=38, corner_radius=RADIO_BOTON, fg_color=COLOR_COBRO_FRAMBUESA, command=guardar).pack(fill="x", padx=20, pady=(0, 16))

    def _modal_reabastecer(self, insumo: Insumo) -> None:
        modal = ctk.CTkToplevel(self.winfo_toplevel())
        modal.title(f"Reabastecer {insumo.nombre}")
        modal.geometry("340x260")
        modal.resizable(False, False)
        modal.configure(fg_color=COLOR_FONDO_VENTANA)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        contenedor = ctk.CTkFrame(modal, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(contenedor, text=f"Reabastecer {insumo.nombre}", font=FUENTE_SUBTITULO, text_color=COLOR_TEXTO_TITULO).pack(pady=(16, 6))
        ctk.CTkLabel(contenedor, text=f"Stock Actual: {insumo.stock_actual} {insumo.unidad_medida}", font=FUENTE_TEXTO, text_color=COLOR_ACENTO_CYAN).pack(pady=(0, 10))

        e_cant = ctk.CTkEntry(contenedor, placeholder_text=f"Cantidad a sumar en {insumo.unidad_medida}", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_cant.pack(fill="x", padx=20, pady=8)

        def reabastecer():
            try:
                cant = float(e_cant.get().strip().replace(",", "."))
                self._inventory_service.reabastecer_stock(self._usuario, insumo.id_insumo or 0, cant)
                modal.grab_release()
                modal.destroy()
                self._cargar_datos()
            except HeladeriaPOSException as exc:
                msgbox.showerror("Error", exc.mensaje)
            except ValueError:
                msgbox.showerror("Error", "La cantidad debe ser numérica.")

        ctk.CTkButton(contenedor, text="Sumar a Bodega", font=FUENTE_BOTON, height=36, corner_radius=RADIO_BOTON, fg_color=COLOR_EXITO, command=reabastecer).pack(fill="x", padx=20, pady=12)
