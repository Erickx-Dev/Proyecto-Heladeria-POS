from __future__ import annotations

from datetime import date
import tkinter.messagebox as msgbox
import customtkinter as ctk

from src.core.exceptions import HeladeriaPOSException
from src.domain.user import Usuario
from src.services.report_service import ReportService, ResumenFinanciero
from src.ui.theme import (
    COLOR_ACENTO_CELESTE,
    COLOR_ACENTO_CYAN,
    COLOR_ADVERTENCIA,
    COLOR_BORDE_SUAVE,
    COLOR_BOTON_SECUNDARIO,
    COLOR_BOTON_SECUNDARIO_HOVER,
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
    RADIO_PANEL,
    RADIO_TARJETA,
)


class ReportsView(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        usuario: Usuario,
        report_service: ReportService,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=COLOR_FONDO_VENTANA, **kwargs)
        self._usuario: Usuario = usuario
        self._report_service: ReportService = report_service

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._crear_encabezado()
        self._crear_cuerpo()
        self._cargar_reporte_hoy()

    def _crear_encabezado(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL, height=54)
        bar.grid(row=0, column=0, padx=16, pady=12, sticky="ew")

        lbl_tit = ctk.CTkLabel(
            bar,
            text="📊 Reportes Financieros y Métricas de Negocio",
            font=FUENTE_TITULO_MEDIO,
            text_color=COLOR_TEXTO_TITULO,
        )
        lbl_tit.pack(side="left", padx=16, pady=10)

        frame_filtros = ctk.CTkFrame(bar, fg_color="transparent")
        frame_filtros.pack(side="right", padx=16)

        btn_hoy = ctk.CTkButton(
            frame_filtros,
            text="Hoy",
            width=70,
            height=32,
            font=FUENTE_BOTON,
            corner_radius=8,
            fg_color=COLOR_ACENTO_CYAN,
            text_color="#141B24",
            command=self._cargar_reporte_hoy,
        )
        btn_hoy.pack(side="left", padx=3)

        btn_sem = ctk.CTkButton(
            frame_filtros,
            text="Semana",
            width=75,
            height=32,
            font=FUENTE_BOTON,
            corner_radius=8,
            fg_color=COLOR_BOTON_SECUNDARIO,
            text_color=COLOR_TEXTO_CUERPO,
            hover_color=COLOR_BOTON_SECUNDARIO_HOVER,
            command=self._cargar_reporte_semana,
        )
        btn_sem.pack(side="left", padx=3)

        btn_mes = ctk.CTkButton(
            frame_filtros,
            text="Mes",
            width=70,
            height=32,
            font=FUENTE_BOTON,
            corner_radius=8,
            fg_color=COLOR_BOTON_SECUNDARIO,
            text_color=COLOR_TEXTO_CUERPO,
            hover_color=COLOR_BOTON_SECUNDARIO_HOVER,
            command=self._cargar_reporte_mes,
        )
        btn_mes.pack(side="left", padx=3)

    def _crear_cuerpo(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._scroll.grid_columnconfigure((0, 1, 2), weight=1)

    def _cargar_reporte_hoy(self) -> None:
        try:
            resumen = self._report_service.reporte_diario(self._usuario)
            ranking = self._report_service.productos_mas_vendidos(self._usuario, resumen.fecha_desde, resumen.fecha_hasta, limite=5)
            self._mostrar_datos("Reporte de Hoy", resumen, ranking)
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)

    def _cargar_reporte_semana(self) -> None:
        try:
            resumen = self._report_service.reporte_semanal(self._usuario)
            ranking = self._report_service.productos_mas_vendidos(self._usuario, resumen.fecha_desde, resumen.fecha_hasta, limite=5)
            self._mostrar_datos("Reporte Semanal (Lunes - Domingo)", resumen, ranking)
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)

    def _cargar_reporte_mes(self) -> None:
        try:
            resumen = self._report_service.reporte_mensual(self._usuario)
            ranking = self._report_service.productos_mas_vendidos(self._usuario, resumen.fecha_desde, resumen.fecha_hasta, limite=5)
            self._mostrar_datos("Reporte Mensual Acumulado", resumen, ranking)
        except HeladeriaPOSException as exc:
            msgbox.showerror("Error", exc.mensaje)

    def _mostrar_datos(self, titulo_periodo: str, r: ResumenFinanciero, ranking: list) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        lbl_rango = ctk.CTkLabel(
            self._scroll,
            text=f"{titulo_periodo}  |  Período: {r.fecha_desde} al {r.fecha_hasta}",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_ACENTO_CELESTE,
            anchor="w",
        )
        lbl_rango.grid(row=0, column=0, columnspan=3, padx=6, pady=(4, 12), sticky="w")

        kpis = [
            ("Ventas Brutas", f"${r.ventas_brutas:,.2f}", COLOR_TEXTO_TITULO),
            ("Total Gastos", f"-${r.total_gastos:,.2f}", COLOR_PELIGRO),
            ("GANANCIA NETA", f"${r.ganancia_neta:,.2f}", COLOR_DORADO_PREMIUM if r.ganancia_neta >= 0 else COLOR_PELIGRO),
        ]

        for idx, (tit, val, col) in enumerate(kpis):
            card = ctk.CTkFrame(self._scroll, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_TARJETA)
            card.grid(row=1, column=idx, padx=6, pady=6, sticky="ew")
            ctk.CTkLabel(card, text=tit, font=FUENTE_MUTED, text_color=COLOR_TEXTO_MUTED).pack(padx=14, pady=(12, 2), anchor="w")
            ctk.CTkLabel(card, text=val, font=FUENTE_TOTAL_POS, text_color=col).pack(padx=14, pady=(0, 12), anchor="w")

        kpis_sec = [
            ("Cantidad de Ventas", f"{r.cantidad_ventas} transacciones", COLOR_TEXTO_CUERPO),
            ("Ticket Promedio", f"${r.ticket_promedio:,.2f}", COLOR_ACENTO_CYAN),
            ("Efectivo Registrado", f"${r.ventas_por_metodo.get('EFECTIVO', 0.0):,.2f}", COLOR_EXITO),
        ]

        for idx, (tit, val, col) in enumerate(kpis_sec):
            card = ctk.CTkFrame(self._scroll, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_TARJETA)
            card.grid(row=2, column=idx, padx=6, pady=6, sticky="ew")
            ctk.CTkLabel(card, text=tit, font=FUENTE_MUTED, text_color=COLOR_TEXTO_MUTED).pack(padx=14, pady=(10, 2), anchor="w")
            ctk.CTkLabel(card, text=val, font=FUENTE_SUBTITULO, text_color=col).pack(padx=14, pady=(0, 10), anchor="w")

        panel_ranking = ctk.CTkFrame(self._scroll, fg_color=COLOR_SUPERFICIE, corner_radius=RADIO_PANEL)
        panel_ranking.grid(row=3, column=0, columnspan=3, padx=6, pady=16, sticky="ew")
        panel_ranking.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel_ranking,
            text="🏆 Top Productos Más Vendidos del Período",
            font=FUENTE_SUBTITULO,
            text_color=COLOR_TEXTO_TITULO,
        ).pack(padx=16, pady=(14, 8), anchor="w")

        if not ranking:
            ctk.CTkLabel(
                panel_ranking,
                text="No hay ventas registradas en este período para generar el ranking.",
                font=FUENTE_TEXTO,
                text_color=COLOR_TEXTO_MUTED,
            ).pack(padx=16, pady=16)
        else:
            for i, p in enumerate(ranking, 1):
                fila = ctk.CTkFrame(panel_ranking, fg_color=COLOR_SUPERFICIE_HOVER, corner_radius=8)
                fila.pack(fill="x", padx=14, pady=3)
                fila.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(fila, text=f"#{i}", font=(FUENTE_FAMILIA, 13, "bold"), text_color=COLOR_DORADO_PREMIUM, width=35).grid(row=0, column=0, padx=8, pady=6)
                ctk.CTkLabel(fila, text=f"{p.nombre} ({p.nombre_categoria})", font=FUENTE_BOTON, text_color=COLOR_TEXTO_TITULO, anchor="w").grid(row=0, column=1, padx=6, pady=6, sticky="w")
                ctk.CTkLabel(fila, text=f"{p.cantidad_vendida} un.", font=FUENTE_TEXTO, text_color=COLOR_TEXTO_CUERPO, width=70).grid(row=0, column=2, padx=8, pady=6)
                ctk.CTkLabel(fila, text=f"${p.ingresos:,.2f}", font=FUENTE_BOTON, text_color=COLOR_ACENTO_CYAN, width=110).grid(row=0, column=3, padx=12, pady=6)
            ctk.CTkLabel(panel_ranking, text="", font=(FUENTE_FAMILIA, 4)).pack()
