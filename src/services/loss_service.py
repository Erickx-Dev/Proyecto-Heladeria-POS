from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_transaction
from src.core.exceptions import AutorizacionError, StockInsuficienteError, ValidacionError
from src.domain.loss import Merma
from src.domain.user import Permiso, Usuario
from src.repositories.loss_repository import LossRepository
from src.repositories.supply_repository import SupplyRepository


class LossService:

    def __init__(
        self,
        loss_repository: Optional[LossRepository] = None,
        supply_repository: Optional[SupplyRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path
        self._loss_repo: LossRepository = loss_repository or LossRepository(db_path=db_path)
        self._supply_repo: SupplyRepository = supply_repository or SupplyRepository(db_path=db_path)

    def _verificar_permiso(self, autor: Usuario, permiso: Permiso) -> None:
        if not autor.has_permission(permiso):
            raise AutorizacionError(
                f"El usuario '{autor.username}' no tiene el permiso '{permiso.value}'."
            )

    def registrar_merma(
        self,
        autor: Usuario,
        id_insumo: int,
        cantidad: float,
        motivo: str,
    ) -> Merma:
        self._verificar_permiso(autor, Permiso.MERMAS)

        if cantidad <= 0.0:
            raise ValidacionError("La cantidad de merma debe ser mayor a cero.")

        if not motivo or not motivo.strip():
            raise ValidacionError("El motivo de la merma no puede estar vacío.")

        insumo = self._supply_repo.obtener_por_id(id_insumo)
        if insumo is None:
            raise ValidacionError("El insumo especificado no existe.")

        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_transaction(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT stock_actual, nombre FROM Insumo WHERE id_insumo = ?;",
                (id_insumo,),
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValidacionError("El insumo especificado no existe.")

            stock_actual = float(fila["stock_actual"])
            if cantidad > stock_actual:
                raise StockInsuficienteError(
                    f"Stock insuficiente para {fila['nombre']}. Disponible: {stock_actual}, Merma solicitada: {cantidad}."
                )

            nuevo_stock = round(stock_actual - cantidad, 4)
            conn.execute(
                "UPDATE Insumo SET stock_actual = ? WHERE id_insumo = ?;",
                (nuevo_stock, id_insumo),
            )

            cursor_merma = conn.execute(
                "INSERT INTO Merma (id_insumo, cantidad, motivo, fecha_hora, id_usuario) VALUES (?, ?, ?, ?, ?);",
                (id_insumo, cantidad, motivo.strip(), fecha_hora, autor.id_usuario),
            )
            id_merma = cursor_merma.lastrowid

            detalles = f"Merma id={id_merma} de {cantidad} {insumo.unidad_medida} de '{insumo.nombre}' registrada por '{autor.username}'. Motivo: '{motivo.strip()}'."
            conn.execute(
                "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) VALUES (?, ?, ?, ?, ?);",
                (autor.id_usuario, "MERMA_REGISTRADA", "MERMAS", fecha_hora, detalles),
            )

        return Merma(
            id_merma=id_merma,
            id_insumo=id_insumo,
            cantidad=cantidad,
            motivo=motivo.strip(),
            fecha_hora=fecha_hora,
            id_usuario=autor.id_usuario,
        )

    def obtener_merma_por_id(self, id_merma: int) -> Optional[Merma]:
        return self._loss_repo.obtener_por_id(id_merma)

    def listar_mermas(self, id_insumo: Optional[int] = None) -> List[Merma]:
        return self._loss_repo.listar_mermas(id_insumo=id_insumo)
