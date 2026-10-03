from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

BASE_DIR: Path = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH: Path = BASE_DIR / "data" / "heladeria.db"


def get_connection(
    db_path: Optional[Union[str, Path]] = None,
    timeout: float = 10.0,
) -> sqlite3.Connection:
    target_path: Path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH

    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        database=str(target_path),
        timeout=timeout,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )

    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row

    return conn


@contextmanager
def get_db_transaction(
    db_path: Optional[Union[str, Path]] = None,
    timeout: float = 10.0,
) -> Generator[sqlite3.Connection, None, None]:
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
    conn: sqlite3.Connection = get_connection(db_path=db_path, timeout=timeout)
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
        conn.close()
