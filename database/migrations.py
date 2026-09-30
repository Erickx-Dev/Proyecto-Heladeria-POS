from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from .connection import DEFAULT_DB_PATH, get_connection

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
    "Receta",
)

SCHEMA_FILE: Path = Path(__file__).resolve().parent / "schema.sql"


def obtener_tablas_existentes(db_path: Optional[Union[str, Path]] = None) -> List[str]:
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
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"No se encontró el archivo de esquema en: {SCHEMA_FILE}")

    tablas_actuales = obtener_tablas_existentes(db_path)
    todas_existen = all(tabla in tablas_actuales for tabla in TABLAS_REQUERIDAS)

    if todas_existen and not forzar:
        return True

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection(db_path)
    try:
        conn.executescript(schema_sql)

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
