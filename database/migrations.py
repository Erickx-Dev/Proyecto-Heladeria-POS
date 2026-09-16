"""
Módulo de Inicialización, Verificación y Migraciones de Base de Datos.

Encargado de aplicar el esquema DDL formal (schema.sql), verificar
la existencia e integridad de las 11 entidades y generar respaldos (.db).
"""

from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from .connection import DEFAULT_DB_PATH, get_connection

# Tablas mandatorias requeridas por la especificación del sistema
TABLAS_REQUERIDAS: tuple[str, ...] = (
    "Rol",
    "Usuario",
    "Categoria",
    "Producto",
    "Insumo",
    "Caja",
    "Venta",
    "DetalleVenta",
    "Gasto",
    "Merma",
    "AuditoriaLog",
)

SCHEMA_FILE: Path = Path(__file__).resolve().parent / "schema.sql"


def obtener_tablas_existentes(db_path: Optional[Union[str, Path]] = None) -> List[str]:
    """
    Retorna la lista de tablas de usuario presentes en la base de datos.
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
            """
        )
        return [str(row[0]) for row in cursor.fetchall()]
    finally:
        conn.close()


def verificar_integridad_referencial(db_path: Optional[Union[str, Path]] = None) -> List[tuple]:
    """
    Ejecuta PRAGMA foreign_key_check y retorna cualquier violación encontrada.
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_check;")
        return cursor.fetchall()
    finally:
        conn.close()


def inicializar_base_de_datos(
    db_path: Optional[Union[str, Path]] = None,
    forzar: bool = False,
) -> bool:
    """
    Aplica el script DDL de schema.sql en la base de datos especificada.

    Args:
        db_path: Ruta destino del archivo SQLite. Si es None, usa DEFAULT_DB_PATH.
        forzar: Si es True, ejecuta el script aún si ya existen tablas.

    Returns:
        bool: True si la inicialización se completó con éxito.

    Raises:
        FileNotFoundError: Si schema.sql no existe.
        sqlite3.IntegrityError: Si ocurren inconsistencias en DDL/datos semilla.
    """
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"No se encontró el archivo de esquema en: {SCHEMA_FILE}")

    tablas_actuales = obtener_tablas_existentes(db_path)
    todas_existen = all(tabla in tablas_actuales for tabla in TABLAS_REQUERIDAS)

    if todas_existen and not forzar:
        # La base de datos ya contiene la arquitectura de 11 tablas
        return True

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection(db_path)
    try:
        # executescript realiza un commit implícito al finalizar
        conn.executescript(schema_sql)

        # Verificación estricta post-creación
        violaciones = list(conn.execute("PRAGMA foreign_key_check;"))
        if violaciones:
            raise sqlite3.IntegrityError(
                f"Violaciones de clave foránea detectadas tras inicializar: {violaciones}"
            )
        return True
    finally:
        conn.close()


def crear_respaldo_db(
    db_path: Optional[Union[str, Path]] = None,
    destino_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Genera un respaldo físico consistente de la base de datos SQLite en caliente,
    utilizando el API nativo de backup para garantizar consistencia transaccional.

    Args:
        db_path: Ruta de la base de datos origen.
        destino_dir: Directorio donde almacenar el respaldo.

    Returns:
        Path: Ruta absoluta del archivo de respaldo generado.
    """
    origen_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    if not origen_path.exists():
        raise FileNotFoundError(f"La base de datos origen no existe: {origen_path}")

    target_dir = Path(destino_dir) if destino_dir is not None else origen_path.parent / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = target_dir / f"heladeria_backup_{timestamp}.db"

    origen_conn = get_connection(origen_path)
    destino_conn = sqlite3.connect(str(backup_path))
    try:
        with destino_conn:
            origen_conn.backup(destino_conn, pages=100)
    finally:
        destino_conn.close()
        origen_conn.close()

    return backup_path


if __name__ == "__main__":
    import sys

    print("=================================================================")
    print(" INICIALIZADOR DE BASE DE DATOS - HELADERÍA POS (SQLITE3)")
    print("=================================================================")
    try:
        print(f"[*] Aplicando esquema DDL desde: {SCHEMA_FILE}")
        exito = inicializar_base_de_datos()
        if exito:
            tablas = obtener_tablas_existentes()
            print(f"[+] Base de datos inicializada exitosamente en: {DEFAULT_DB_PATH}")
            print(f"[+] Total de tablas activas ({len(tablas)}): {', '.join(tablas)}")
            violaciones = verificar_integridad_referencial()
            if not violaciones:
                print("[+] Integridad referencial verificada: 0 violaciones.")
            else:
                print(f"[!] ADVERTENCIA: Violaciones detectadas: {violaciones}")
    except Exception as exc:
        print(f"[-] Error crítico durante la inicialización: {exc}", file=sys.stderr)
        sys.exit(1)
