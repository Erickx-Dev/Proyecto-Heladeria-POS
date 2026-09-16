"""
Módulo de Persistencia y Base de Datos (SQLite3).

Exporta las utilidades canónicas para conexión, transacciones seguras
y control de esquemas relacionales.
"""

from .connection import (
    BASE_DIR,
    DEFAULT_DB_PATH,
    get_connection,
    get_db_cursor,
    get_db_transaction,
)


def inicializar_base_de_datos(*args, **kwargs):
    from .migrations import inicializar_base_de_datos as _init
    return _init(*args, **kwargs)


def obtener_tablas_existentes(*args, **kwargs):
    from .migrations import obtener_tablas_existentes as _obt
    return _obt(*args, **kwargs)


def verificar_integridad_referencial(*args, **kwargs):
    from .migrations import verificar_integridad_referencial as _ver
    return _ver(*args, **kwargs)


def crear_respaldo_db(*args, **kwargs):
    from .migrations import crear_respaldo_db as _resp
    return _resp(*args, **kwargs)


__all__ = [
    "BASE_DIR",
    "DEFAULT_DB_PATH",
    "get_connection",
    "get_db_cursor",
    "get_db_transaction",
    "inicializar_base_de_datos",
    "obtener_tablas_existentes",
    "verificar_integridad_referencial",
    "crear_respaldo_db",
]
