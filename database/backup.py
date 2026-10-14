from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from .connection import DEFAULT_DB_PATH
from .migrations import crear_respaldo_db

PATRON_RESPALDO: str = "heladeria_backup_*.db"


def verificar_integridad_respaldo(ruta_respaldo: Union[str, Path]) -> bool:
    ruta: Path = Path(ruta_respaldo)
    if not ruta.exists() or ruta.stat().st_size == 0:
        return False

    conn = sqlite3.connect(str(ruta))
    try:
        resultado = conn.execute("PRAGMA integrity_check;").fetchone()
        return resultado is not None and resultado[0] == "ok"
    except sqlite3.DatabaseError:
        return False
    finally:
        conn.close()


def crear_respaldo(
    db_path: Optional[Union[str, Path]] = None,
    destino_dir: Optional[Union[str, Path]] = None,
) -> Path:
    if destino_dir is not None:
        destino: Path = Path(destino_dir)
        if destino.exists() and not destino.is_dir():
            raise NotADirectoryError(f"El destino no es una carpeta válida: {destino}")

    ruta_respaldo: Path = crear_respaldo_db(db_path=db_path, destino_dir=destino_dir)

    if not verificar_integridad_respaldo(ruta_respaldo):
        ruta_respaldo.unlink(missing_ok=True)
        raise sqlite3.DatabaseError(f"El respaldo generado está corrupto y fue descartado: {ruta_respaldo}")

    return ruta_respaldo


def carpeta_respaldos_por_defecto(db_path: Optional[Union[str, Path]] = None) -> Path:
    origen: Path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    return origen.parent / "backups"


def listar_respaldos(directorio: Union[str, Path]) -> List[Path]:
    carpeta: Path = Path(directorio)
    if not carpeta.is_dir():
        return []
    return sorted(carpeta.glob(PATRON_RESPALDO), key=lambda p: p.name, reverse=True)
