from __future__ import annotations

import unittest

from src.core.exceptions import (
    CantidadInvalidaError,
    MetodoPagoInvalidoError,
    PagoInsuficienteError,
    VentaSinItemsError,
)
from src.domain.sale import DetalleVenta, MetodoPago, TicketVenta, Venta


class TestSaleDomain(unittest.TestCase):

    def test_detalle_venta_calculo_subtotal_correcto(self) -> None:
        detalle = DetalleVenta(
            id_producto=1,
            cantidad=3,
            precio_unitario=5000.0,
        )
        self.assertEqual(detalle.subtotal, 15000.0)

    def test_detalle_venta_cantidad_cero_o_negativa_lanza_excepcion(self) -> None:
        with self.assertRaises(CantidadInvalidaError):
            DetalleVenta(id_producto=1, cantidad=0, precio_unitario=5000.0)

        with self.assertRaises(CantidadInvalidaError):
            DetalleVenta(id_producto=1, cantidad=-2, precio_unitario=5000.0)

    def test_detalle_venta_precio_negativo_lanza_excepcion(self) -> None:
        with self.assertRaises(ValueError):
            DetalleVenta(id_producto=1, cantidad=1, precio_unitario=-100.0)

    def test_detalle_venta_id_producto_invalido_lanza_excepcion(self) -> None:
        with self.assertRaises(ValueError):
            DetalleVenta(id_producto=0, cantidad=1, precio_unitario=5000.0)

    def test_venta_calculo_total_acumulado(self) -> None:
        d1 = DetalleVenta(id_producto=1, cantidad=2, precio_unitario=4000.0)
        d2 = DetalleVenta(id_producto=2, cantidad=1, precio_unitario=2500.0)
        venta = Venta(
            id_caja=1,
            fecha_hora="2026-09-22 20:00:00",
            detalles=[d1, d2],
        )
        self.assertEqual(venta.total, 10500.0)

    def test_venta_agregar_detalle_recalcula_total(self) -> None:
        venta = Venta(id_caja=1, fecha_hora="2026-09-22 20:00:00")
        self.assertEqual(venta.total, 0.0)
        venta.agregar_detalle(DetalleVenta(id_producto=1, cantidad=2, precio_unitario=3000.0))
        self.assertEqual(venta.total, 6000.0)
        venta.agregar_detalle(DetalleVenta(id_producto=2, cantidad=1, precio_unitario=1500.0))
        self.assertEqual(venta.total, 7500.0)

    def test_venta_liquidar_pago_efectivo_con_cambio_exacto(self) -> None:
        d1 = DetalleVenta(id_producto=1, cantidad=2, precio_unitario=4500.0)
        venta = Venta(id_caja=1, fecha_hora="2026-09-22 20:00:00", detalles=[d1])
        cambio = venta.liquidar_pago(metodo_pago="EFECTIVO", dinero_recibido=10000.0)
        self.assertEqual(venta.total, 9000.0)
        self.assertEqual(venta.dinero_recibido, 10000.0)
        self.assertEqual(venta.cambio, 1000.0)
        self.assertEqual(cambio, 1000.0)

    def test_venta_liquidar_pago_efectivo_insuficiente_lanza_excepcion(self) -> None:
        d1 = DetalleVenta(id_producto=1, cantidad=2, precio_unitario=5000.0)
        venta = Venta(id_caja=1, fecha_hora="2026-09-22 20:00:00", detalles=[d1])
        with self.assertRaises(PagoInsuficienteError):
            venta.liquidar_pago(metodo_pago="EFECTIVO", dinero_recibido=8000.0)

    def test_venta_liquidar_pago_transferencia(self) -> None:
        d1 = DetalleVenta(id_producto=1, cantidad=2, precio_unitario=5000.0)
        venta = Venta(id_caja=1, fecha_hora="2026-09-22 20:00:00", detalles=[d1])
        cambio = venta.liquidar_pago(metodo_pago="TRANSFERENCIA")
        self.assertEqual(venta.total, 10000.0)
        self.assertEqual(venta.dinero_recibido, 10000.0)
        self.assertEqual(venta.cambio, 0.0)
        self.assertEqual(cambio, 0.0)

    def test_venta_liquidar_pago_metodo_invalido_lanza_excepcion(self) -> None:
        d1 = DetalleVenta(id_producto=1, cantidad=1, precio_unitario=5000.0)
        venta = Venta(id_caja=1, fecha_hora="2026-09-22 20:00:00", detalles=[d1])
        with self.assertRaises(MetodoPagoInvalidoError):
            venta.liquidar_pago(metodo_pago="BITCOIN")

    def test_venta_validar_sin_items_lanza_excepcion(self) -> None:
        venta = Venta(id_caja=1, fecha_hora="2026-09-22 20:00:00")
        with self.assertRaises(VentaSinItemsError):
            venta.validar()

    def test_ticket_venta_generacion_texto(self) -> None:
        ticket = TicketVenta(
            id_venta=101,
            id_caja=1,
            fecha_hora="2026-09-22 20:15:00",
            metodo_pago="EFECTIVO",
            total=12000.0,
            dinero_recibido=20000.0,
            cambio=8000.0,
            items=[
                {"cantidad": 2, "nombre": "Cono Vainilla", "subtotal": 8000.0},
                {"cantidad": 1, "nombre": "Barquillo Extra", "subtotal": 4000.0},
            ],
        )
        texto = ticket.generar_texto(ancho=40)
        self.assertIn("HELADERIA ARTESANAL POS", texto)
        self.assertIn("Venta Consecutiva: #101", texto)
        self.assertIn("Cono Vainilla", texto)
        self.assertIn("Barquillo Extra", texto)
        self.assertIn("$12,000.00", texto)
        self.assertIn("$20,000.00", texto)
        self.assertIn("$8,000.00", texto)


if __name__ == "__main__":
    unittest.main()
