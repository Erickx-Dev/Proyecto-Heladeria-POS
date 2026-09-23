from __future__ import annotations

import unittest

from src.core.exceptions import (
    MontoInvalidoError,
    PagoInsuficienteError,
    StockInsuficienteError,
    ValidacionError,
)
from src.domain import (
    Arqueo,
    AuditoriaLog,
    Categoria,
    DetalleVenta,
    Gasto,
    Insumo,
    Merma,
    Producto,
    Rol,
    TurnoCaja,
    Usuario,
    Venta,
)


class TestUsuarioRol(unittest.TestCase):

    def test_rol_valido(self) -> None:
        rol = Rol(id_rol=1, nombre_rol="Administrador")
        rol.validar()
        self.assertEqual(rol.nombre_rol, "Administrador")

    def test_rol_invalido_vacio(self) -> None:
        rol = Rol(id_rol=1, nombre_rol="")
        with self.assertRaises(ValidacionError):
            rol.validar()

    def test_usuario_valido(self) -> None:
        usuario = Usuario(
            id_usuario=1,
            nombre="Carlos Cajero",
            username="carloscajero",
            password_hash="$2b$12$PmIxg7ONN2NO7XExZ9hBAODxQxq25YxDrbayYPDmfTgFxYFhMmSPa",
            id_rol=2,
            estado=1,
        )
        usuario.validar()
        self.assertTrue(usuario.es_activo())
        self.assertFalse(usuario.es_administrador())

    def test_usuario_administrador(self) -> None:
        admin = Usuario(
            id_usuario=1,
            nombre="Admin Principal",
            username="admin",
            password_hash="$2b$12$PmIxg7ONN2NO7XExZ9hBAODxQxq25YxDrbayYPDmfTgFxYFhMmSPa",
            id_rol=1,
            estado=1,
        )
        admin.validar()
        self.assertTrue(admin.es_activo())
        self.assertTrue(admin.es_administrador())

    def test_usuario_validaciones_erroneas(self) -> None:
        u_nombre_vacio = Usuario(nombre="", username="admin", password_hash="a" * 60)
        with self.assertRaises(ValidacionError):
            u_nombre_vacio.validar()

        u_user_corto = Usuario(nombre="Admin", username="ad", password_hash="a" * 60)
        with self.assertRaises(ValidacionError):
            u_user_corto.validar()

        u_hash_invalido = Usuario(nombre="Admin", username="admin", password_hash="corto")
        with self.assertRaises(ValidacionError):
            u_hash_invalido.validar()

        u_rol_invalido = Usuario(nombre="Admin", username="admin", password_hash="a" * 60, id_rol=99)
        with self.assertRaises(ValidacionError):
            u_rol_invalido.validar()


class TestCategoria(unittest.TestCase):

    def test_categoria_valida(self) -> None:
        cat = Categoria(id_categoria=1, nombre_categoria="Helados Artesanales", descripcion="De bola")
        cat.validar()
        self.assertEqual(cat.nombre_categoria, "Helados Artesanales")

    def test_categoria_invalida(self) -> None:
        cat = Categoria(id_categoria=1, nombre_categoria="   ")
        with self.assertRaises(ValidacionError):
            cat.validar()


class TestProducto(unittest.TestCase):

    def test_producto_valido(self) -> None:
        prod = Producto(
            id_producto=1,
            codigo="CONO-01",
            nombre="Cono Simple Vainilla",
            precio_venta=4500.0,
            id_categoria=1,
            estado=1,
        )
        prod.validar()
        self.assertTrue(prod.es_activo())

    def test_producto_precio_negativo(self) -> None:
        prod = Producto(
            id_producto=1,
            codigo="CONO-01",
            nombre="Cono Simple",
            precio_venta=-100.0,
            id_categoria=1,
        )
        with self.assertRaises(ValidacionError):
            prod.validar()

    def test_producto_codigo_vacio(self) -> None:
        prod = Producto(
            id_producto=1,
            codigo="",
            nombre="Cono Simple",
            precio_venta=4000.0,
            id_categoria=1,
        )
        with self.assertRaises(ValidacionError):
            prod.validar()


class TestInsumo(unittest.TestCase):

    def test_insumo_valido_y_alertas(self) -> None:
        insumo = Insumo(
            id_insumo=1,
            nombre="Helado Fresa Litro",
            unidad_medida="Litros",
            stock_actual=10.0,
            stock_minimo=2.0,
        )
        insumo.validar()
        self.assertFalse(insumo.esta_en_alerta_stock())

        insumo.descontar(8.5)
        self.assertEqual(insumo.stock_actual, 1.5)
        self.assertTrue(insumo.esta_en_alerta_stock())

        insumo.reabastecer(5.0)
        self.assertEqual(insumo.stock_actual, 6.5)
        self.assertFalse(insumo.esta_en_alerta_stock())

    def test_insumo_descontar_exceso_lanza_error(self) -> None:
        insumo = Insumo(
            id_insumo=1,
            nombre="Conos Waffle",
            unidad_medida="Unidades",
            stock_actual=10.0,
            stock_minimo=5.0,
        )
        with self.assertRaises(StockInsuficienteError):
            insumo.descontar(15.0)

    def test_insumo_cantidades_negativas(self) -> None:
        insumo = Insumo(
            id_insumo=1,
            nombre="Salsa Chocolate",
            unidad_medida="ml",
            stock_actual=100.0,
            stock_minimo=20.0,
        )
        with self.assertRaises(ValidacionError):
            insumo.descontar(-10.0)
        with self.assertRaises(ValidacionError):
            insumo.reabastecer(0.0)


class TestTurnoCajaYArqueo(unittest.TestCase):

    def test_turno_caja_flujo(self) -> None:
        turno = TurnoCaja(
            id_caja=1,
            id_usuario=1,
            fecha_apertura="2026-09-22 08:00:00",
            monto_inicial=50000.0,
        )
        turno.validar()
        self.assertTrue(turno.esta_abierta())

        turno.cerrar(monto_final_real=52000.0, diferencia=2000.0)
        self.assertFalse(turno.esta_abierta())
        self.assertEqual(turno.estado, "CERRADA")
        self.assertEqual(turno.diferencia, 2000.0)

    def test_arqueo_calculos(self) -> None:
        arqueo = Arqueo(
            monto_inicial=100000.0,
            total_ventas_efectivo=200000.0,
            total_gastos=15000.0,
            monto_fisico_real=285000.0,
        )
        self.assertEqual(arqueo.saldo_esperado, 285000.0)
        self.assertEqual(arqueo.diferencia, 0.0)
        self.assertEqual(arqueo.tipo_diferencia, "CUADRADO")

        arqueo_sobrante = Arqueo(100.0, 50.0, 0.0, 160.0)
        self.assertEqual(arqueo_sobrante.tipo_diferencia, "SOBRANTE")

        arqueo_faltante = Arqueo(100.0, 50.0, 0.0, 140.0)
        self.assertEqual(arqueo_faltante.tipo_diferencia, "FALTANTE")


class TestGasto(unittest.TestCase):

    def test_gasto_valido(self) -> None:
        gasto = Gasto(
            id_gasto=1,
            id_caja=1,
            fecha_hora="2026-09-22 10:00:00",
            monto=8000.0,
            descripcion="Compra de bolsas de hielo",
            id_usuario=1,
        )
        gasto.validar()

    def test_gasto_monto_cero_invalido(self) -> None:
        gasto = Gasto(id_caja=1, monto=0.0, descripcion="Prueba", id_usuario=1)
        with self.assertRaises(MontoInvalidoError):
            gasto.validar()

    def test_gasto_descripcion_vacia(self) -> None:
        gasto = Gasto(id_caja=1, monto=5000.0, descripcion="", id_usuario=1)
        with self.assertRaises(ValidacionError):
            gasto.validar()


class TestVentaYDetalle(unittest.TestCase):

    def test_venta_flujo_efectivo(self) -> None:
        venta = Venta(
            id_caja=1,
            fecha_hora="2026-09-22 11:30:00",
            metodo_pago="EFECTIVO",
            dinero_recibido=20000.0,
        )
        det1 = DetalleVenta(id_producto=1, cantidad=2, precio_unitario=5000.0)
        det2 = DetalleVenta(id_producto=2, cantidad=1, precio_unitario=6000.0)

        venta.agregar_detalle(det1)
        venta.agregar_detalle(det2)

        self.assertEqual(venta.total, 16000.0)
        cambio = venta.calcular_cambio()
        self.assertEqual(cambio, 4000.0)
        venta.validar()

    def test_venta_pago_insuficiente(self) -> None:
        venta = Venta(id_caja=1, metodo_pago="EFECTIVO", dinero_recibido=10000.0)
        det = DetalleVenta(id_producto=1, cantidad=1, precio_unitario=15000.0)
        venta.agregar_detalle(det)
        with self.assertRaises(PagoInsuficienteError):
            venta.calcular_cambio()

    def test_venta_transferencia_cambio_cero(self) -> None:
        venta = Venta(id_caja=1, metodo_pago="TRANSFERENCIA")
        det = DetalleVenta(id_producto=1, cantidad=1, precio_unitario=12000.0)
        venta.agregar_detalle(det)
        cambio = venta.calcular_cambio()
        self.assertEqual(cambio, 0.0)
        self.assertEqual(venta.dinero_recibido, 12000.0)


class TestMerma(unittest.TestCase):

    def test_merma_valida(self) -> None:
        merma = Merma(
            id_merma=1,
            id_insumo=2,
            cantidad=3.5,
            motivo="Helado derretido por corte de energía nocturno",
            fecha_hora="2026-09-22 09:00:00",
            id_usuario=1,
        )
        merma.validar()

    def test_merma_invalida(self) -> None:
        merma = Merma(id_insumo=0, cantidad=0.0, motivo="", id_usuario=0)
        with self.assertRaises(ValidacionError):
            merma.validar()


class TestAuditoriaLog(unittest.TestCase):

    def test_auditoria_valida(self) -> None:
        log = AuditoriaLog(
            id_log=1,
            id_usuario=1,
            accion="APERTURA_CAJA",
            modulo="CAJA",
            fecha_hora="2026-09-22 08:00:00",
            detalles="Apertura con $50,000",
        )
        log.validar()

    def test_auditoria_invalida(self) -> None:
        log = AuditoriaLog(accion="", modulo="")
        with self.assertRaises(ValidacionError):
            log.validar()


if __name__ == "__main__":
    unittest.main()
