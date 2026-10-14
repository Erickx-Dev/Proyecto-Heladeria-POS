from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from database.backup import carpeta_respaldos_por_defecto, crear_respaldo, listar_respaldos
from database.connection import get_db_transaction
from src.core.exceptions import AutorizacionError
from src.domain.user import Permiso, Usuario


class BackupService:

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path

    def _verificar_permiso(self, autor: Usuario) -> None:
        if not autor.has_permission(Permiso.BACKUP):
            raise AutorizacionError(
                f"El usuario '{autor.username}' no tiene el permiso '{Permiso.BACKUP.value}'."
            )

    def _registrar_auditoria(self, accion: str, id_usuario: Optional[int], detalles: str) -> None:
        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_transaction(self._db_path) as conn:
            conn.execute(
                "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) "
                "VALUES (?, ?, ?, ?, ?);",
                (id_usuario, accion, "BACKUP", fecha_hora, detalles),
            )

    def carpeta_por_defecto(self) -> Path:
        return carpeta_respaldos_por_defecto(self._db_path)

    def crear_respaldo(self, autor: Usuario, destino_dir: Optional[Union[str, Path]] = None) -> Path:
        self._verificar_permiso(autor)
        destino: Path = Path(destino_dir) if destino_dir is not None else self.carpeta_por_defecto()
        try:
            ruta: Path = crear_respaldo(db_path=self._db_path, destino_dir=destino)
        except Exception as exc:
            self._registrar_auditoria(
                "RESPALDO_FALLIDO",
                autor.id_usuario,
                f"Respaldo hacia '{destino}' falló: {exc}",
            )
            raise

        self._registrar_auditoria(
            "RESPALDO_CREADO",
            autor.id_usuario,
            f"Respaldo '{ruta.name}' creado en '{ruta.parent}' por '{autor.username}'.",
        )
        return ruta

    def listar_respaldos(self, autor: Usuario, directorio: Optional[Union[str, Path]] = None) -> List[Path]:
        self._verificar_permiso(autor)
        return listar_respaldos(directorio if directorio is not None else self.carpeta_por_defecto())
