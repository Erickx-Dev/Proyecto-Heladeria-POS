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
