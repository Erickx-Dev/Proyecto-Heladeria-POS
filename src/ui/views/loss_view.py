from __future__ import annotations

import tkinter.messagebox as msgbox
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.user import Usuario
from src.services.inventory_service import InventoryService
from src.services.loss_service import LossService
from src.ui.theme import (
    COLOR_ADVERTENCIA,
    COLOR_BORDE_SUAVE,
    COLOR_BOTON_SECUNDARIO,
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


class LossView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        loss_service: LossService,
        inventory_service: InventoryService,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._usuario: Usuario = usuario
        self._loss_service: LossService = loss_service
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
            text="📉 Registro de Mermas y Descartes",
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

        self._form = ctk.CTkFrame(cuerpo, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        self._form.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        ctk.CTkLabel(self._form, text="Registrar Descarte de Materia Prima", font=FUENTE_SUBTITULO, text_color=COLOR_TEXTO_TITULO).pack(padx=16, pady=(16, 12), anchor="w")

        ctk.CTkLabel(self._form, text="Insumo Afectado:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=16)
        insumos = self._inventory_service.listar_insumos()
        self._insumos_dict = {i.nombre: i for i in insumos}
        nombres = list(self._insumos_dict.keys()) or ["Sin insumos"]

        self._cb_insumo = ctk.CTkComboBox(self._form, values=nombres, font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        self._cb_insumo.pack(fill="x", padx=16, pady=(2, 10))

        ctk.CTkLabel(self._form, text="Cantidad Descartada:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=16)
        self._e_cant = ctk.CTkEntry(self._form, placeholder_text="Ej: 1.5", font=(FUENTE_FAMILIA, 14, "bold"), corner_radius=RADIO_ENTRY)
        self._e_cant.pack(fill="x", padx=16, pady=(2, 10))

        ctk.CTkLabel(self._form, text="Motivo / Justificación:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=16)
        self._e_motivo = ctk.CTkEntry(self._form, placeholder_text="Ej: Fecha de caducidad superada", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        self._e_motivo.pack(fill="x", padx=16, pady=(2, 16))

        btn_guardar = ctk.CTkButton(
            self._form,
            text="Registrar Merma",
            font=FUENTE_BOTON,
            height=38,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_PELIGRO,
            hover_color=COLOR_PELIGRO_HOVER,
            command=self._registrar_merma,
        )
        btn_guardar.pack(fill="x", padx=16, pady=(0, 16))

        panel_lista = ctk.CTkFrame(cuerpo, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        panel_lista.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        panel_lista.grid_rowconfigure(1, weight=1)
        panel_lista.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel_lista, text="Historial de Mermas Registradas", font=FUENTE_SUBTITULO, text_color=COLOR_TEXTO_TITULO).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        self._scroll_mermas = ctk.CTkScrollableFrame(panel_lista, fg_color="transparent")
        self._scroll_mermas.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._scroll_mermas.grid_columnconfigure(0, weight=1)

    def _cargar_datos(self) -> None:
        for w in self._scroll_mermas.winfo_children():
            w.destroy()

        mermas = self._loss_service.listar_mermas()
        mapa_insumos = {i.id_insumo: i for i in self._inventory_service.listar_insumos() if i.id_insumo}

        if not mermas:
            ctk.CTkLabel(
                self._scroll_mermas,
                text="No hay mermas registradas en el sistema.",
                font=FUENTE_TEXTO,
                text_color=COLOR_TEXTO_MUTED,
            ).pack(pady=40)
            return

        for m in mermas:
            fila = ctk.CTkFrame(self._scroll_mermas, fg_color=COLOR_SUPERFICIE_HOVER, corner_radius=RADIO_TARJETA)
            fila.pack(fill="x", pady=4)
            fila.grid_columnconfigure(0, weight=1)

            ins_obj = mapa_insumos.get(m.id_insumo)
            ins_txt = f"{ins_obj.nombre} ({m.cantidad} {ins_obj.unidad_medida})" if ins_obj else f"Insumo #{m.id_insumo}: {m.cantidad}"

            ctk.CTkLabel(fila, text=ins_txt, font=FUENTE_BOTON, text_color=COLOR_DORADO_PREMIUM, anchor="w").grid(row=0, column=0, padx=12, pady=(6, 2), sticky="w")
            ctk.CTkLabel(fila, text=f"Motivo: {m.motivo}", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_CUERPO, anchor="w").grid(row=1, column=0, padx=12, pady=1, sticky="w")
            ctk.CTkLabel(fila, text=m.fecha_hora, font=FUENTE_MUTED, text_color=COLOR_TEXTO_MUTED, anchor="w").grid(row=2, column=0, padx=12, pady=(1, 6), sticky="w")

    def _registrar_merma(self) -> None:
        sel_nombre = self._cb_insumo.get()
        ins_obj = self._insumos_dict.get(sel_nombre)
        if not ins_obj or not ins_obj.id_insumo:
            msgbox.showerror("Error", "Seleccione un insumo válido.")
            return

        txt_cant = self._e_cant.get().strip().replace(",", ".")
        motivo = self._e_motivo.get().strip()

        try:
            cant = float(txt_cant)
            self._loss_service.registrar_merma(
                autor=self._usuario,
                id_insumo=ins_obj.id_insumo,
                cantidad=cant,
                motivo=motivo,
            )
            msgbox.showinfo("Merma Registrada", f"Se descontaron {cant} {ins_obj.unidad_medida} de bodega por merma.")
            self._e_cant.delete(0, "end")
            self._e_motivo.delete(0, "end")
            self._cargar_datos()
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)
        except ValueError:
            msgbox.showerror("Error", "La cantidad debe ser un valor numérico.")
