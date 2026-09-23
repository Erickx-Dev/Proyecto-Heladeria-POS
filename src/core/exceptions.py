from __future__ import annotations


class HeladeriaPOSException(Exception):

    def __init__(self, mensaje: str = "Error interno del sistema POS.") -> None:
        self.mensaje: str = mensaje
        super().__init__(self.mensaje)


class CajaYaAbiertaError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "Ya existe una caja abierta en el sistema. "
        "Debe cerrar el turno activo antes de abrir uno nuevo."
    ) -> None:
        super().__init__(mensaje)


class CajaNoAbiertaError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "No existe una caja abierta. "
        "Debe abrir un turno con monto inicial antes de operar."
    ) -> None:
        super().__init__(mensaje)


class MontoInvalidoError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "El monto proporcionado no es válido. "
        "Debe ser un valor numérico mayor o igual a cero."
    ) -> None:
        super().__init__(mensaje)


class GastoExcedeSaldoDisponibleError(HeladeriaPOSException):

    def __init__(
        self,
        monto_solicitado: float = 0.0,
        saldo_disponible: float = 0.0,
    ) -> None:
        mensaje: str = (
            f"El gasto de ${monto_solicitado:,.2f} excede el saldo disponible "
            f"en caja de ${saldo_disponible:,.2f}."
        )
        self.monto_solicitado: float = monto_solicitado
        self.saldo_disponible: float = saldo_disponible
        super().__init__(mensaje)


class DescripcionGastoVaciaError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "La descripción del gasto no puede estar vacía. "
        "Debe indicar el concepto del egreso."
    ) -> None:
        super().__init__(mensaje)


class StockInsuficienteError(HeladeriaPOSException):

    def __init__(
        self,
        id_insumo: int = 0,
        cantidad_solicitada: float = 0.0,
        stock_disponible: float = 0.0,
    ) -> None:
        mensaje: str = (
            f"Stock insuficiente para el insumo #{id_insumo}. "
            f"Solicitado: {cantidad_solicitada}, Disponible: {stock_disponible}."
        )
        self.id_insumo: int = id_insumo
        self.cantidad_solicitada: float = cantidad_solicitada
        self.stock_disponible: float = stock_disponible
        super().__init__(mensaje)


class InsumoNoEncontradoError(HeladeriaPOSException):

    def __init__(self, id_insumo: int) -> None:
        self.id_insumo: int = id_insumo
        super().__init__(f"No se encontró el insumo con ID #{id_insumo}.")


class ProductoNoEncontradoError(HeladeriaPOSException):

    def __init__(self, identificador: str | int) -> None:
        self.identificador: str | int = identificador
        super().__init__(f"No se encontró el producto: {identificador}.")


class PagoInsuficienteError(HeladeriaPOSException):

    def __init__(
        self,
        total_requerido: float = 0.0,
        monto_pagado: float = 0.0,
    ) -> None:
        mensaje: str = (
            f"El dinero recibido (${monto_pagado:,.2f}) no cubre "
            f"el total de la venta (${total_requerido:,.2f})."
        )
        self.total_requerido: float = total_requerido
        self.monto_pagado: float = monto_pagado
        super().__init__(mensaje)


class MetodoPagoInvalidoError(HeladeriaPOSException):

    def __init__(self, metodo: str) -> None:
        self.metodo: str = metodo
        super().__init__(
            f"Método de pago no válido: '{metodo}'. "
            f"Valores permitidos: EFECTIVO, TARJETA, TRANSFERENCIA, OTRO."
        )


class VentaSinItemsError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "No se puede procesar una venta sin partidas o productos."
    ) -> None:
        super().__init__(mensaje)


class CantidadInvalidaError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "La cantidad debe ser un valor numérico mayor a cero."
    ) -> None:
        super().__init__(mensaje)


class MermaInvalidaError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "Los datos de la merma no son válidos. "
        "Verifique que la cantidad sea positiva y el motivo no esté vacío."
    ) -> None:
        super().__init__(mensaje)
