from __future__ import annotations


class HeladeriaPOSException(Exception):
    """
    Excepción base del dominio HELA-POS.
    Todas las excepciones de negocio heredan de esta clase para que las capas
    superiores (Servicios / Interfaz Gráfica) puedan capturar errores de negocio
    de forma unificada mediante 'except HeladeriaPOSException as err:'.
    """

    def __init__(self, mensaje: str = "Error interno del sistema POS.") -> None:
        self.mensaje: str = mensaje
        super().__init__(self.mensaje)


class ValidacionError(HeladeriaPOSException):
    """Se lanza cuando un dato de entrada incumple el formato o rango esperado."""

    def __init__(self, mensaje: str = "Error de validación de datos.") -> None:
        super().__init__(mensaje)


class AutenticacionError(HeladeriaPOSException):
    """Se lanza cuando el username no existe, la clave no coincide o el usuario está inactivo."""

    def __init__(self, mensaje: str = "Credenciales incorrectas o usuario inactivo.") -> None:
        super().__init__(mensaje)


class AutorizacionError(HeladeriaPOSException):
    """Se lanza cuando un usuario autenticado intenta ejecutar una acción sin el rol/permiso requerido (RBAC)."""

    def __init__(self, mensaje: str = "No cuenta con los permisos necesarios para realizar esta acción.") -> None:
        super().__init__(mensaje)


class CajaYaAbiertaError(HeladeriaPOSException):
    """Impide que existan dos turnos de caja abiertos simultáneamente."""

    def __init__(
        self, mensaje: str = "Ya existe una caja abierta en el sistema. Debe cerrar el turno activo."
    ) -> None:
        super().__init__(mensaje)


class CajaNoAbiertaError(HeladeriaPOSException):
    """Impide registrar ventas o gastos si no se ha realizado la apertura de turno."""

    def __init__(
        self, mensaje: str = "No existe una caja abierta. Debe abrir turno para operar."
    ) -> None:
        super().__init__(mensaje)


class MontoInvalidoError(HeladeriaPOSException):
    """Se lanza cuando un valor monetario (precio, gasto, apertura) es negativo o inválido."""

    def __init__(
        self, mensaje: str = "El monto monetario no es válido."
    ) -> None:
        super().__init__(mensaje)


class StockInsuficienteError(HeladeriaPOSException):
    """Se lanza al intentar descontar más cantidad de insumo de la disponible en bodega."""

    def __init__(
        self, mensaje: str = "Stock insuficiente del insumo para realizar la operación."
    ) -> None:
        super().__init__(mensaje)


class GastoExcedeSaldoDisponibleError(HeladeriaPOSException):
    """Impide que un gasto de caja chica deje el efectivo físico del cajón en negativo."""

    def __init__(
        self, monto_solicitado: float = 0.0, saldo_disponible: float = 0.0
    ) -> None:
        self.monto_solicitado: float = monto_solicitado
        self.saldo_disponible: float = saldo_disponible
        super().__init__(
            f"El gasto de ${monto_solicitado:,.2f} excede el saldo disponible en caja de ${saldo_disponible:,.2f}."
        )


class PagoInsuficienteError(HeladeriaPOSException):
    """Se lanza en ventas en efectivo cuando el billete entregado por el cliente no cubre el total."""

    def __init__(
        self, mensaje: str = "El dinero recibido es menor al total de la venta."
    ) -> None:
        super().__init__(mensaje)
