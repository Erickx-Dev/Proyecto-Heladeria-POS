from __future__ import annotations

from typing import List, Optional
import tkinter.messagebox as msgbox
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.category import Categoria
from src.domain.product import Producto
from src.domain.user import Usuario
from src.services.catalog_service import CatalogService
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


class CatalogView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        catalog_service: CatalogService,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._usuario: Usuario = usuario
        self._catalog_service: CatalogService = catalog_service

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
            text="🏷️ Catálogo Comercial de Productos",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_tit.pack(side="left", padx=16, pady=10)

        btn_nuevo = ctk.CTkButton(
            bar,
            text="+ Nuevo Producto",
            font=FUENTE_BOTON,
            height=32,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_ACENTO_CYAN,
            text_color="#141B24",
            command=self._modal_nuevo_producto,
        )
        btn_nuevo.pack(side="right", padx=16)

    def _crear_cuerpo(self) -> None:
        self._scroll_tabla = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll_tabla.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll_tabla.grid_columnconfigure(0, weight=1)

    def _cargar_datos(self) -> None:
        for w in self._scroll_tabla.winfo_children():
            w.destroy()

        productos = self._catalog_service.listar_productos(solo_activos=False)
        categorias = {c.id_categoria: c.nombre_categoria for c in self._catalog_service.listar_categorias() if c.id_categoria}

        if not productos:
            ctk.CTkLabel(
                self._scroll_tabla,
                text="No hay productos registrados.",
                font=FUENTE_TEXTO,
                text_color=COLOR_TEXTO_MUTED,
            ).pack(pady=30)
            return

        for p in productos:
            fila = ctk.CTkFrame(self._scroll_tabla, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_TARJETA)
            fila.pack(fill="x", pady=4)
            fila.grid_columnconfigure(1, weight=1)

            lbl_cod = ctk.CTkLabel(fila, text=p.codigo, font=FUENTE_BOTON, text_color=COLOR_DORADO_PREMIUM, width=80)
            lbl_cod.grid(row=0, column=0, padx=10, pady=8, sticky="w")

            cat_txt = categorias.get(p.id_categoria, "General")
            lbl_info = ctk.CTkLabel(
                fila,
                text=f"{p.nombre}  ({cat_txt})",
                font=FUENTE_SUBTITULO,
                text_color=COLOR_TEXTO_TITULO,
                anchor="w",
            )
            lbl_info.grid(row=0, column=1, padx=8, pady=8, sticky="w")

            lbl_precio = ctk.CTkLabel(
                fila,
                text=f"${p.precio_venta:,.2f}",
                font=FUENTE_BOTON,
                text_color=COLOR_ACENTO_CYAN,
                width=100,
            )
            lbl_precio.grid(row=0, column=2, padx=10, pady=8)

            estado_txt = "🟢 Activo" if p.es_activo() else "🔴 Inactivo"
            lbl_est = ctk.CTkLabel(
                fila,
                text=estado_txt,
                font=FUENTE_MUTED,
                text_color=COLOR_EXITO if p.es_activo() else COLOR_PELIGRO,
                width=80,
            )
            lbl_est.grid(row=0, column=3, padx=6, pady=8)

            btn_toggle = ctk.CTkButton(
                fila,
                text="Suspender" if p.es_activo() else "Activar",
                width=85,
                height=28,
                font=FUENTE_MUTED,
                corner_radius=8,
                fg_color=COLOR_BOTON_SECUNDARIO,
                hover_color=COLOR_SUPERFICIE_HOVER,
                command=lambda prod=p: self._toggle_estado(prod),
            )
            btn_toggle.grid(row=0, column=4, padx=10, pady=8)

    def _toggle_estado(self, prod: Producto) -> None:
        nuevo = 0 if prod.es_activo() else 1
        try:
            self._catalog_service.cambiar_estado_producto(self._usuario, prod.id_producto or 0, nuevo)
            self._cargar_datos()
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)

    def _modal_nuevo_producto(self) -> None:
        cats = self._catalog_service.listar_categorias()
        if not cats:
            msgbox.showwarning("Sin Categorías", "Debe existir al menos una categoría registrada.")
            return

        modal = ctk.CTkToplevel(self.winfo_toplevel())
        modal.title("Nuevo Producto")
        modal.geometry("420x460")
        modal.resizable(False, False)
        modal.configure(fg_color=COLOR_FONDO_VENTANA)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        contenedor = ctk.CTkFrame(modal, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(contenedor, text="Crear Producto Comercial", font=FUENTE_TITULO_MEDIO, text_color=COLOR_TEXTO_TITULO).pack(pady=(16, 12))

        ctk.CTkLabel(contenedor, text="Código Único:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_cod = ctk.CTkEntry(contenedor, placeholder_text="Ej: HEL-05", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_cod.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(contenedor, text="Nombre del Producto:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_nom = ctk.CTkEntry(contenedor, placeholder_text="Ej: Helado de Arequipe", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_nom.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(contenedor, text="Precio de Venta ($):", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        e_pre = ctk.CTkEntry(contenedor, placeholder_text="Ej: 5500", font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        e_pre.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(contenedor, text="Categoría:", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_MUTED, anchor="w").pack(fill="x", padx=20)
        nombres_cats = [c.nombre_categoria for c in cats]
        cb_cat = ctk.CTkComboBox(contenedor, values=nombres_cats, font=FUENTE_TEXTO, corner_radius=RADIO_ENTRY)
        cb_cat.pack(fill="x", padx=20, pady=(2, 16))

        def guardar():
            cod = e_cod.get().strip()
            nom = e_nom.get().strip()
            pre_txt = e_pre.get().strip().replace(",", ".")
            sel_cat_nom = cb_cat.get()
            cat_obj = next((c for c in cats if c.nombre_categoria == sel_cat_nom), cats[0])
            try:
                pre = float(pre_txt)
                self._catalog_service.crear_producto(
                    autor=self._usuario,
                    codigo=cod,
                    nombre=nom,
                    precio_venta=pre,
                    id_categoria=cat_obj.id_categoria or 1,
                )
                modal.grab_release()
                modal.destroy()
                self._cargar_datos()
            except HeladeriaPOSException as exc:
                msgbox.showerror("Error", exc.mensaje)
            except ValueError:
                msgbox.showerror("Error", "El precio debe ser un número válido.")

        ctk.CTkButton(contenedor, text="Guardar Producto", font=FUENTE_BOTON, height=38, corner_radius=RADIO_BOTON, fg_color=COLOR_COBRO_FRAMBUESA, command=guardar).pack(fill="x", padx=20, pady=(0, 16))
