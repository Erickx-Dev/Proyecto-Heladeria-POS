from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

from database.connection import get_db_cursor
from src.core.exceptions import AutorizacionError, ValidacionError
from src.domain.user import Permiso, Usuario

FORMATO_FECHA: str = "%Y-%m-%d"


@dataclass
class ResumenFinanciero:

    fecha_desde: str
    fecha_hasta: str
    ventas_brutas: float = 0.0
    total_gastos: float = 0.0
    ganancia_neta: float = 0.0
    cantidad_ventas: int = 0
    ticket_promedio: float = 0.0
    ventas_por_metodo: Dict[str, float] = field(default_factory=dict)


@dataclass
class ProductoVendido:

    id_producto: int
    codigo: str
    nombre: str
    nombre_categoria: str
    cantidad_vendida: int
    ingresos: float


@dataclass
class VentaDiaria:

    fecha: str
    cantidad_ventas: int
    ventas_brutas: float


class ReportService:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _verificar_permiso(self, autor: Usuario) -> None:
        if not autor.has_permission(Permiso.REPORTES):
            raise AutorizacionError(
                f"El usuario '{autor.username}' no tiene el permiso '{Permiso.REPORTES.value}'."
            )

    @staticmethod
    def _normalizar_rango(fecha_desde: Union[str, date], fecha_hasta: Union[str, date]) -> tuple[str, str]:
        try:
            desde: date = fecha_desde if isinstance(fecha_desde, date) else datetime.strptime(fecha_desde, FORMATO_FECHA).date()
            hasta: date = fecha_hasta if isinstance(fecha_hasta, date) else datetime.strptime(fecha_hasta, FORMATO_FECHA).date()
        except (TypeError, ValueError):
            raise ValidacionError("Las fechas deben tener el formato AAAA-MM-DD.")

        if desde > hasta:
            raise ValidacionError("La fecha inicial no puede ser posterior a la fecha final.")

        return desde.strftime(FORMATO_FECHA), hasta.strftime(FORMATO_FECHA)

    @staticmethod
    def _limites(desde: str, hasta: str) -> tuple[str, str]:
        return f"{desde} 00:00:00", f"{hasta} 23:59:59"

    def resumen_financiero(
        self,
        autor: Usuario,
        fecha_desde: Union[str, date],
        fecha_hasta: Union[str, date],
    ) -> ResumenFinanciero:
        self._verificar_permiso(autor)
        desde, hasta = self._normalizar_rango(fecha_desde, fecha_hasta)
        inicio, fin = self._limites(desde, hasta)

        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT metodo_pago, COUNT(*) AS cantidad, COALESCE(SUM(total), 0.0) AS monto "
                "FROM Venta WHERE fecha_hora BETWEEN ? AND ? GROUP BY metodo_pago;",
                (inicio, fin),
            )
            filas = cursor.fetchall()

            cursor.execute(
                "SELECT COALESCE(SUM(monto), 0.0) FROM Gasto WHERE fecha_hora BETWEEN ? AND ?;",
                (inicio, fin),
            )
            total_gastos: float = round(float(cursor.fetchone()[0]), 2)

        ventas_por_metodo: Dict[str, float] = {f["metodo_pago"]: round(float(f["monto"]), 2) for f in filas}
        cantidad_ventas: int = sum(int(f["cantidad"]) for f in filas)
        ventas_brutas: float = round(sum(ventas_por_metodo.values()), 2)

        return ResumenFinanciero(
            fecha_desde=desde,
            fecha_hasta=hasta,
            ventas_brutas=ventas_brutas,
            total_gastos=total_gastos,
            ganancia_neta=round(ventas_brutas - total_gastos, 2),
            cantidad_ventas=cantidad_ventas,
            ticket_promedio=round(ventas_brutas / cantidad_ventas, 2) if cantidad_ventas else 0.0,
            ventas_por_metodo=ventas_por_metodo,
        )

    def reporte_diario(self, autor: Usuario, fecha: Optional[date] = None) -> ResumenFinanciero:
        dia: date = fecha or date.today()
        return self.resumen_financiero(autor, dia, dia)

    def reporte_semanal(self, autor: Usuario, fecha: Optional[date] = None) -> ResumenFinanciero:
        referencia: date = fecha or date.today()
        lunes: date = referencia - timedelta(days=referencia.weekday())
        return self.resumen_financiero(autor, lunes, lunes + timedelta(days=6))

    def reporte_mensual(self, autor: Usuario, anio: Optional[int] = None, mes: Optional[int] = None) -> ResumenFinanciero:
        hoy: date = date.today()
        anio = anio or hoy.year
        mes = mes or hoy.month
        if not 1 <= mes <= 12:
            raise ValidacionError("El mes debe estar entre 1 y 12.")
        ultimo_dia: int = calendar.monthrange(anio, mes)[1]
        return self.resumen_financiero(autor, date(anio, mes, 1), date(anio, mes, ultimo_dia))

    def productos_mas_vendidos(
        self,
        autor: Usuario,
        fecha_desde: Union[str, date],
        fecha_hasta: Union[str, date],
        limite: int = 10,
        id_categoria: Optional[int] = None,
    ) -> List[ProductoVendido]:
        self._verificar_permiso(autor)
        if limite <= 0:
            raise ValidacionError("El límite del ranking debe ser mayor a cero.")
        desde, hasta = self._normalizar_rango(fecha_desde, fecha_hasta)
        inicio, fin = self._limites(desde, hasta)

        filtro_categoria: str = " AND p.id_categoria = ?" if id_categoria is not None else ""
        parametros: list = [inicio, fin]
        if id_categoria is not None:
            parametros.append(id_categoria)
        parametros.append(limite)

        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT p.id_producto, p.codigo, p.nombre, c.nombre_categoria, "
                "SUM(d.cantidad) AS cantidad_vendida, SUM(d.subtotal) AS ingresos "
                "FROM DetalleVenta d "
                "JOIN Venta v ON v.id_venta = d.id_venta "
                "JOIN Producto p ON p.id_producto = d.id_producto "
                "JOIN Categoria c ON c.id_categoria = p.id_categoria "
                f"WHERE v.fecha_hora BETWEEN ? AND ?{filtro_categoria} "
                "GROUP BY p.id_producto "
                "ORDER BY cantidad_vendida DESC, ingresos DESC, p.nombre ASC "
                "LIMIT ?;",
                tuple(parametros),
            )
            return [
                ProductoVendido(
                    id_producto=f["id_producto"],
                    codigo=f["codigo"],
                    nombre=f["nombre"],
                    nombre_categoria=f["nombre_categoria"],
                    cantidad_vendida=int(f["cantidad_vendida"]),
                    ingresos=round(float(f["ingresos"]), 2),
                )
                for f in cursor.fetchall()
            ]

    def ventas_por_dia(
        self,
        autor: Usuario,
        fecha_desde: Union[str, date],
        fecha_hasta: Union[str, date],
    ) -> List[VentaDiaria]:
        self._verificar_permiso(autor)
        desde, hasta = self._normalizar_rango(fecha_desde, fecha_hasta)
        inicio, fin = self._limites(desde, hasta)

        with get_db_cursor(self._db_path) as cursor:
            cursor.execute(
                "SELECT substr(fecha_hora, 1, 10) AS dia, COUNT(*) AS cantidad, COALESCE(SUM(total), 0.0) AS monto "
                "FROM Venta WHERE fecha_hora BETWEEN ? AND ? GROUP BY dia ORDER BY dia;",
                (inicio, fin),
            )
            return [
                VentaDiaria(fecha=f["dia"], cantidad_ventas=int(f["cantidad"]), ventas_brutas=round(float(f["monto"]), 2))
                for f in cursor.fetchall()
            ]
