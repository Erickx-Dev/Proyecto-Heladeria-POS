from __future__ import annotations


class HeladeriaPOSException(Exception):

    def __init__(self, mensaje: str = "Error interno del sistema POS.") -> None:
        self.mensaje: str = mensaje
        super().__init__(self.mensaje)


class ValidacionError(HeladeriaPOSException):

    def __init__(self, mensaje: str = "Error de validación de datos.") -> None:
        super().__init__(mensaje)


class AutenticacionError(HeladeriaPOSException):

    def __init__(self, mensaje: str = "Credenciales incorrectas o usuario inactivo.") -> None:
        super().__init__(mensaje)


class CajaYaAbiertaError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "Ya existe una caja abierta en el sistema. Debe cerrar el turno activo."
    ) -> None:
        super().__init__(mensaje)


class CajaNoAbiertaError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "No existe una caja abierta. Debe abrir turno para operar."
    ) -> None:
        super().__init__(mensaje)


class MontoInvalidoError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "El monto monetario no es válido."
    ) -> None:
        super().__init__(mensaje)


class StockInsuficienteError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "Stock insuficiente del insumo para realizar la operación."
    ) -> None:
        super().__init__(mensaje)


class GastoExcedeSaldoDisponibleError(HeladeriaPOSException):

    def __init__(
        self, monto_solicitado: float = 0.0, saldo_disponible: float = 0.0
    ) -> None:
        self.monto_solicitado: float = monto_solicitado
        self.saldo_disponible: float = saldo_disponible
        super().__init__(
            f"El gasto de ${monto_solicitado:,.2f} excede el saldo disponible en caja de ${saldo_disponible:,.2f}."
        )


class PagoInsuficienteError(HeladeriaPOSException):

    def __init__(
        self, mensaje: str = "El dinero recibido es menor al total de la venta."
    ) -> None:
        super().__init__(mensaje)
