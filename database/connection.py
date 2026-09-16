"""
Módulo de Conexión y Gestión Transaccional para SQLite3.

Proporciona la factoría de conexiones seguras y context managers
para operaciones atómicas (ACID) y consultas sobre la base de datos local.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

# Ruta canónica hacia el archivo de base de datos en la carpeta data/
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH: Path = BASE_DIR / "data" / "heladeria.db"


def get_connection(
    db_path: Optional[Union[str, Path]] = None,
    timeout: float = 10.0,
) -> sqlite3.Connection:
    """
    Crea y retorna una nueva conexión a la base de datos SQLite.

    Configuraciones aplicadas obligatoriamente:
    - Habilitación de claves foráneas (PRAGMA foreign_keys = ON).
    - Acceso a columnas por nombre vía sqlite3.Row.
    - Manejo de timeout para evitar bloqueos por concurrencia.

    Args:
        db_path: Ruta al archivo .db. Si no se especifica, usa DEFAULT_DB_PATH.
        timeout: Segundos máximos de espera ante bloqueos de archivo.

    Returns:
        sqlite3.Connection configurada.
    """
    target_path: Path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH

    # Asegurar que el directorio contenedor exista
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        database=str(target_path),
        timeout=timeout,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )

    # Configuración estricta de la sesión
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row

    return conn


@contextmanager
def get_db_transaction(
    db_path: Optional[Union[str, Path]] = None,
    timeout: float = 10.0,
) -> Generator[sqlite3.Connection, None, None]:
    """
    Gestor de contexto para operaciones transaccionales compuestas (ACID).

    Garantiza:
    - Inicio automático de bloque transaccional.
    - Commit automático si el bloque termina sin excepciones.
    - Rollback inmediato ante cualquier excepción levantada.
    - Cierre seguro de la conexión física en la cláusula finally.

    Yields:
        sqlite3.Connection: Conexión activa bajo contexto transaccional.
    """
    conn: sqlite3.Connection = get_connection(db_path=db_path, timeout=timeout)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


@contextmanager
def get_db_cursor(
    db_path: Optional[Union[str, Path]] = None,
    timeout: float = 10.0,
) -> Generator[sqlite3.Cursor, None, None]:
    """
    Gestor de contexto para consultas de lectura o ejecución controlada.

    Garantiza el cierre adecuado del cursor y de la conexión al finalizar.

    Yields:
        sqlite3.Cursor: Cursor listo para ejecutar consultas.
    """
    conn: sqlite3.Connection = get_connection(db_path=db_path, timeout=timeout)
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
        conn.close()
