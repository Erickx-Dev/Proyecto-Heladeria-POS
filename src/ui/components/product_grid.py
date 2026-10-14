from __future__ import annotations

from typing import Callable, Dict, List, Optional
import customtkinter as ctk

from src.domain.category import Categoria
from src.domain.product import Producto
from src.ui.theme import (
    COLOR_BORDE_SUAVE,
    COLOR_BOTON_SECUNDARIO,
    COLOR_BOTON_SECUNDARIO_HOVER,
    COLOR_DORADO_HOVER,
    COLOR_DORADO_PREMIUM,
    COLOR_DORADO_TEXTO_OSCURO,
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
    RADIO_BOTON,
    RADIO_ENTRY,
    RADIO_TARJETA,
)


class ProductCard(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        producto: Producto,
        nombre_categoria: str,
        on_add: Callable[[Producto], None],
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLOR_SUPERFICIE,
            corner_radius=RADIO_TARJETA,
            border_width=1,
            border_color=COLOR_BORDE_SUAVE,
            **kwargs,
        )
        self._producto: Producto = producto
        self._on_add: Callable[[Producto], None] = on_add

        self.grid_columnconfigure(0, weight=1)

        lbl_cat = ctk.CTkLabel(
            self,
            text=nombre_categoria.upper(),
            font=FUENTE_MUTED,
            text_color=COLOR_TEXTO_MUTED,
            anchor="w",
        )
        lbl_cat.grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")

        lbl_nombre = ctk.CTkLabel(
            self,
            text=self._producto.nombre,
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
            anchor="w",
            wraplength=170,
            justify="left",
        )
        lbl_nombre.grid(row=1, column=0, padx=12, pady=2, sticky="w")

        lbl_precio = ctk.CTkLabel(
            self,
            text=f"${self._producto.precio_venta:,.2f}",
            font=(FUENTE_FAMILIA, 15, "bold"),
            text_color=COLOR_DORADO_PREMIUM,
            anchor="w",
        )
        lbl_precio.grid(row=2, column=0, padx=12, pady=(4, 8), sticky="w")

        btn_agregar = ctk.CTkButton(
            self,
            text="+ Agregar",
            font=FUENTE_BOTON,
            height=32,
            corner_radius=RADIO_BOTON,
            fg_color="#FFFBEB",
            hover_color="#FEF3C7",
            text_color="#B45309",
            border_width=1,
            border_color="#D97706",
            command=lambda: self._on_add(self._producto),
        )
        btn_agregar.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")


class ProductGrid(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        productos: List[Producto],
        categorias: List[Categoria],
        on_add_product: Callable[[Producto], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._todos_productos: List[Producto] = [p for p in productos if p.es_activo()]
        self._categorias: List[Categoria] = categorias
        self._on_add_product: Callable[[Producto], None] = on_add_product
        self._categoria_activa: Optional[int] = None
        self._texto_filtro: str = ""
        self._botones_cat: Dict[Optional[int], ctk.CTkButton] = {}

        self._mapa_categorias: Dict[int, str] = {
            c.id_categoria: c.nombre_categoria for c in categorias if c.id_categoria
        }

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._crear_barra_busqueda()
        self._crear_barra_categorias()
        self._crear_area_tarjetas()
        self._renderizar_tarjetas()

    def _crear_barra_busqueda(self) -> None:
        frame_busqueda = ctk.CTkFrame(self, fg_color="transparent")
        frame_busqueda.grid(row=0, column=0, padx=6, pady=(0, 8), sticky="ew")
        frame_busqueda.grid_columnconfigure(0, weight=1)

        self._entry_busqueda = ctk.CTkEntry(
            frame_busqueda,
            placeholder_text="🔍 Buscar producto por nombre o código...",
            font=FUENTE_TEXTO,
            height=38,
            corner_radius=RADIO_ENTRY,
            fg_color=COLOR_SUPERFICIE,
            border_color=COLOR_BORDE_SUAVE,
            text_color=COLOR_TEXTO_TITULO,
        )
        self._entry_busqueda.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self._entry_busqueda.bind("<KeyRelease>", self._al_cambiar_busqueda)

        btn_limpiar = ctk.CTkButton(
            frame_busqueda,
            text="Limpiar",
            width=80,
            height=38,
            corner_radius=RADIO_BOTON,
            font=FUENTE_BOTON,
            fg_color=COLOR_BOTON_SECUNDARIO,
            hover_color=COLOR_BOTON_SECUNDARIO_HOVER,
            command=self._limpiar_busqueda,
        )
        btn_limpiar.grid(row=0, column=1)

    def _crear_barra_categorias(self) -> None:
        self._frame_cat = ctk.CTkScrollableFrame(
            self,
            orientation="horizontal",
            height=44,
            fg_color="transparent",
        )
        self._frame_cat.grid(row=1, column=0, padx=6, pady=(0, 8), sticky="ew")

        btn_todos = ctk.CTkButton(
            self._frame_cat,
            text="Todos",
            height=32,
            font=FUENTE_BOTON,
            corner_radius=RADIO_BOTON,
            fg_color=COLOR_DORADO_PREMIUM,
            text_color=COLOR_DORADO_TEXTO_OSCURO,
            hover_color=COLOR_DORADO_HOVER,
            command=lambda: self._filtrar_categoria(None),
        )
        btn_todos.pack(side="left", padx=4)
        self._botones_cat[None] = btn_todos

        for cat in self._categorias:
            btn = ctk.CTkButton(
                self._frame_cat,
                text=cat.nombre_categoria,
                height=32,
                font=FUENTE_BOTON,
                corner_radius=RADIO_BOTON,
                fg_color=COLOR_SUPERFICIE,
                text_color=COLOR_TEXTO_CUERPO,
                hover_color=COLOR_SUPERFICIE_HOVER,
                border_width=1,
                border_color=COLOR_BORDE_SUAVE,
                command=lambda cid=cat.id_categoria: self._filtrar_categoria(cid),
            )
            btn.pack(side="left", padx=4)
            self._botones_cat[cat.id_categoria] = btn

    def _crear_area_tarjetas(self) -> None:
        self._scroll_tarjetas = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
        )
        self._scroll_tarjetas.grid(row=2, column=0, padx=6, pady=0, sticky="nsew")
        for col in range(3):
            self._scroll_tarjetas.grid_columnconfigure(col, weight=1, uniform="col")

    def _al_cambiar_busqueda(self, event=None) -> None:
        self._texto_filtro = self._entry_busqueda.get().strip().lower()
        self._renderizar_tarjetas()

    def _limpiar_busqueda(self) -> None:
        self._entry_busqueda.delete(0, "end")
        self._texto_filtro = ""
        self._renderizar_tarjetas()

    def _filtrar_categoria(self, id_categoria: Optional[int]) -> None:
        self._categoria_activa = id_categoria
        for cid, btn in self._botones_cat.items():
            if cid == id_categoria:
                btn.configure(
                    fg_color=COLOR_DORADO_PREMIUM,
                    text_color=COLOR_DORADO_TEXTO_OSCURO,
                    border_width=0,
                )
            else:
                btn.configure(
                    fg_color=COLOR_SUPERFICIE,
                    text_color=COLOR_TEXTO_CUERPO,
                    border_width=1,
                    border_color=COLOR_BORDE_SUAVE,
                )
        self._renderizar_tarjetas()

    def _renderizar_tarjetas(self) -> None:
        for widget in self._scroll_tarjetas.winfo_children():
            widget.destroy()

        filtrados: List[Producto] = []
        for p in self._todos_productos:
            if self._categoria_activa is not None and p.id_categoria != self._categoria_activa:
                continue
            if self._texto_filtro:
                if self._texto_filtro not in p.nombre.lower() and self._texto_filtro not in p.codigo.lower():
                    continue
            filtrados.append(p)

        if not filtrados:
            lbl_vacio = ctk.CTkLabel(
                self._scroll_tarjetas,
                text="No se encontraron productos que coincidan con la búsqueda.",
                font=FUENTE_TEXTO,
                text_color=COLOR_TEXTO_MUTED,
            )
            lbl_vacio.grid(row=0, column=0, columnspan=3, pady=40)
            return

        columnas = 3
        for idx, prod in enumerate(filtrados):
            fila = idx // columnas
            col = idx % columnas
            cat_nombre = self._mapa_categorias.get(prod.id_categoria, "General")
            card = ProductCard(
                self._scroll_tarjetas,
                producto=prod,
                nombre_categoria=cat_nombre,
                on_add=self._on_add_product,
            )
            card.grid(row=fila, column=col, padx=6, pady=6, sticky="nsew")

    def actualizar_productos(self, productos: List[Producto], categorias: List[Categoria]) -> None:
        self._todos_productos = [p for p in productos if p.es_activo()]
        self._categorias = categorias
        self._mapa_categorias = {c.id_categoria: c.nombre_categoria for c in categorias if c.id_categoria}
        self._renderizar_tarjetas()
