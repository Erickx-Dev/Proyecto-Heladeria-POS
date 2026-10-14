from __future__ import annotations

from typing import Callable, Optional
import tkinter.messagebox as msgbox
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.product import Producto
from src.domain.user import Usuario
from src.services.cash_service import CashService
from src.services.catalog_service import CatalogService
from src.services.pos_service import ItemVenta, POSService
from src.ui.components.cart_view import CartView
from src.ui.components.payment_modal import PaymentModal
from src.ui.components.product_grid import ProductGrid
from src.ui.theme import (
    COLOR_ACENTO_CYAN,
    COLOR_BORDE_SUAVE,
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
    RADIO_PANEL,
)


class POSView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        pos_service: POSService,
        catalog_service: CatalogService,
        cash_service: CashService,
        on_ir_a_caja: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._usuario: Usuario = usuario
        self._pos_service: POSService = pos_service
        self._catalog_service: CatalogService = catalog_service
        self._cash_service: CashService = cash_service
        self._on_ir_a_caja: Optional[Callable[[], None]] = on_ir_a_caja

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)

        self._crear_barra_superior()
        self._crear_cuerpo()

    def _crear_barra_superior(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL, height=54)
        bar.grid(row=0, column=0, columnspan=2, padx=12, pady=(12, 8), sticky="ew")
        bar.grid_columnconfigure(0, weight=1)

        frame_izq = ctk.CTkFrame(bar, fg_color="transparent")
        frame_izq.pack(side="left", padx=16, pady=8)

        lbl_tit = ctk.CTkLabel(
            frame_izq,
            text="🛒 Mostrador de Ventas",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_tit.pack(side="left")

        frame_der = ctk.CTkFrame(bar, fg_color="transparent")
        frame_der.pack(side="right", padx=16, pady=8)

        self._lbl_estado_caja = ctk.CTkLabel(
            frame_der,
            text="",
            font=FUENTE_SUBTITULO,
        )
        self._lbl_estado_caja.pack(side="left", padx=(0, 12))
        self._actualizar_indicador_caja()

        btn_refrescar = ctk.CTkButton(
            frame_der,
            text="🔄 Refrescar",
            width=90,
            height=32,
            font=FUENTE_BOTON,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLOR_BORDE_SUAVE,
            border_width=1,
            border_color=COLOR_BORDE_SUAVE,
            command=self._refrescar_catalogo,
        )
        btn_refrescar.pack(side="left")

    def _actualizar_indicador_caja(self) -> None:
        try:
            caja = self._cash_service.obtener_turno_activo()
            self._lbl_estado_caja.configure(
                text=f"🟢 Turno #{caja.id_caja} (Abierto)",
                text_color=COLOR_EXITO,
            )
        except Exception:
            self._lbl_estado_caja.configure(
                text="🔴 Caja Cerrada",
                text_color=COLOR_PELIGRO,
            )

    def _crear_cuerpo(self) -> None:
        productos = self._catalog_service.listar_productos(solo_activos=True)
        categorias = self._catalog_service.listar_categorias()

        self._grid = ProductGrid(
            self,
            productos=productos,
            categorias=categorias,
            on_add_product=self._al_agregar_producto,
        )
        self._grid.grid(row=1, column=0, padx=(12, 6), pady=(0, 12), sticky="nsew")

        self._cart = CartView(
            self,
            on_checkout=self._iniciar_cobro,
        )
        self._cart.grid(row=1, column=1, padx=(6, 12), pady=(0, 12), sticky="nsew")

    def _al_agregar_producto(self, producto: Producto) -> None:
        self._cart.agregar_producto(producto)

    def _refrescar_catalogo(self) -> None:
        productos = self._catalog_service.listar_productos(solo_activos=True)
        categorias = self._catalog_service.listar_categorias()
        self._grid.actualizar_productos(productos, categorias)
        self._actualizar_indicador_caja()

    def _iniciar_cobro(self) -> None:
        try:
            self._cash_service.obtener_turno_activo()
        except Exception:
            msgbox.showerror(
                "Caja Cerrada",
                "No hay un turno de caja abierto. Debe abrir caja antes de realizar ventas.",
            )
            if self._on_ir_a_caja:
                self._on_ir_a_caja()
            return

        items = self._cart.obtener_items()
        if not items:
            return

        total = self._cart.total
        PaymentModal(
            parent=self.winfo_toplevel(),
            total=total,
            on_confirm=self._procesar_venta,
        )

    def _procesar_venta(self, metodo_pago: str, dinero_recibido: float) -> None:
        items = [ItemVenta(id_producto=pid, cantidad=cant) for pid, cant in self._cart.obtener_items()]
        try:
            venta = self._pos_service.registrar_venta(
                id_usuario=self._usuario.id_usuario or 1,
                items=items,
                metodo_pago=metodo_pago,
                dinero_recibido=dinero_recibido,
            )
            msgbox.showinfo(
                "Venta Exitosa",
                f"✅ Venta #{venta.id_venta} registrada con éxito.\n\n"
                f"Total: ${venta.total:,.2f}\n"
                f"Método: {venta.metodo_pago}\n"
                f"Recibido: ${venta.dinero_recibido:,.2f}\n"
                f"Cambio: ${venta.cambio:,.2f}",
            )
            self._cart.vaciar()
            self._refrescar_catalogo()
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error en Venta", exc.mensaje)
        except Exception as exc:
            msgbox.showerror("Error Inesperado", f"Ocurrió un error al procesar la venta: {exc}")
