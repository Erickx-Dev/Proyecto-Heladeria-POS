from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_transaction
from src.core.exceptions import AutorizacionError, ValidacionError
from src.domain.recipe import Receta
from src.domain.supply import Insumo
from src.domain.user import Permiso, Usuario
from src.repositories.product_repository import ProductRepository
from src.repositories.recipe_repository import RecipeRepository
from src.repositories.supply_repository import SupplyRepository


class InventoryService:

    def __init__(
        self,
        supply_repository: Optional[SupplyRepository] = None,
        recipe_repository: Optional[RecipeRepository] = None,
        product_repository: Optional[ProductRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path
        self._supply_repo: SupplyRepository = supply_repository or SupplyRepository(db_path=db_path)
        self._recipe_repo: RecipeRepository = recipe_repository or RecipeRepository(db_path=db_path)
        self._product_repo: ProductRepository = product_repository or ProductRepository(db_path=db_path)

    def _registrar_auditoria(
        self,
        accion: str,
        id_usuario: Optional[int],
        detalles: str,
    ) -> None:
        fecha_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_transaction(self._db_path) as conn:
            conn.execute(
                "INSERT INTO AuditoriaLog (id_usuario, accion, modulo, fecha_hora, detalles) VALUES (?, ?, ?, ?, ?);",
                (id_usuario, accion, "INVENTARIO", fecha_hora, detalles),
            )

    def _verificar_permiso(self, autor: Usuario, permiso: Permiso) -> None:
        if not autor.has_permission(permiso):
            raise AutorizacionError(
                f"El usuario '{autor.username}' no tiene el permiso '{permiso.value}'."
            )

    def crear_insumo(
        self,
        autor: Usuario,
        nombre: str,
        unidad_medida: str,
        stock_actual: float = 0.0,
        stock_minimo: float = 0.0,
    ) -> Insumo:
        self._verificar_permiso(autor, Permiso.INVENTARIO)

        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del insumo no puede estar vacío.")

        if not unidad_medida or not unidad_medida.strip():
            raise ValidacionError("La unidad de medida no puede estar vacía.")

        if stock_actual < 0.0:
            raise ValidacionError("El stock actual no puede ser negativo.")

        if stock_minimo < 0.0:
            raise ValidacionError("El stock mínimo no puede ser negativo.")

        nombre_limpio = nombre.strip()
        existente = self._supply_repo.obtener_por_nombre(nombre_limpio)
        if existente is not None:
            raise ValidacionError(f"El insumo '{nombre_limpio}' ya existe en el sistema.")

        insumo = Insumo(
            nombre=nombre_limpio,
            unidad_medida=unidad_medida.strip(),
            stock_actual=round(stock_actual, 4),
            stock_minimo=round(stock_minimo, 4),
        )
        id_insumo = self._supply_repo.crear_insumo(insumo)
        insumo.id_insumo = id_insumo

        self._registrar_auditoria(
            "INSUMO_CREADO",
            autor.id_usuario,
            f"Insumo id={id_insumo} '{insumo.nombre}' ({insumo.unidad_medida}) creado por '{autor.username}'.",
        )

        return insumo

    def actualizar_insumo(
        self,
        autor: Usuario,
        id_insumo: int,
        nombre: str,
        unidad_medida: str,
        stock_minimo: float,
    ) -> Insumo:
        self._verificar_permiso(autor, Permiso.INVENTARIO)

        insumo_actual = self._supply_repo.obtener_por_id(id_insumo)
        if insumo_actual is None:
            raise ValidacionError("El insumo especificado no existe.")

        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del insumo no puede estar vacío.")

        if not unidad_medida or not unidad_medida.strip():
            raise ValidacionError("La unidad de medida no puede estar vacía.")

        if stock_minimo < 0.0:
            raise ValidacionError("El stock mínimo no puede ser negativo.")

        nombre_limpio = nombre.strip()
        existente = self._supply_repo.obtener_por_nombre(nombre_limpio)
        if existente is not None and existente.id_insumo != id_insumo:
            raise ValidacionError(f"El nombre '{nombre_limpio}' ya pertenece a otro insumo.")

        insumo_actualizado = Insumo(
            id_insumo=id_insumo,
            nombre=nombre_limpio,
            unidad_medida=unidad_medida.strip(),
            stock_actual=insumo_actual.stock_actual,
            stock_minimo=round(stock_minimo, 4),
        )
        self._supply_repo.actualizar_insumo(insumo_actualizado)

        self._registrar_auditoria(
            "INSUMO_ACTUALIZADO",
            autor.id_usuario,
            f"Insumo id={id_insumo} actualizado por '{autor.username}'.",
        )

        return insumo_actualizado

    def reabastecer_stock(
        self,
        autor: Usuario,
        id_insumo: int,
        cantidad: float,
    ) -> bool:
        self._verificar_permiso(autor, Permiso.INVENTARIO)

        if cantidad <= 0.0:
            raise ValidacionError("La cantidad a reabastecer debe ser mayor a cero.")

        insumo = self._supply_repo.obtener_por_id(id_insumo)
        if insumo is None:
            raise ValidacionError("El insumo especificado no existe.")

        resultado = self._supply_repo.aumentar_stock(id_insumo, cantidad)
        self._registrar_auditoria(
            "STOCK_REABASTECIDO",
            autor.id_usuario,
            f"Stock de insumo id={id_insumo} '{insumo.nombre}' incrementado en +{cantidad} {insumo.unidad_medida} por '{autor.username}'.",
        )
        return resultado

    def descontar_stock(
        self,
        autor: Usuario,
        id_insumo: int,
        cantidad: float,
    ) -> bool:
        self._verificar_permiso(autor, Permiso.INVENTARIO)

        if cantidad <= 0.0:
            raise ValidacionError("La cantidad a descontar debe ser mayor a cero.")

        insumo = self._supply_repo.obtener_por_id(id_insumo)
        if insumo is None:
            raise ValidacionError("El insumo especificado no existe.")

        resultado = self._supply_repo.descontar_stock(id_insumo, cantidad)
        self._registrar_auditoria(
            "STOCK_DESCONTADO",
            autor.id_usuario,
            f"Stock de insumo id={id_insumo} '{insumo.nombre}' descontado en -{cantidad} {insumo.unidad_medida} por '{autor.username}'.",
        )
        return resultado

    def obtener_insumo_por_id(self, id_insumo: int) -> Optional[Insumo]:
        return self._supply_repo.obtener_por_id(id_insumo)

    def listar_insumos(self) -> List[Insumo]:
        return self._supply_repo.listar_insumos()

    def obtener_alertas_stock(self) -> List[Insumo]:
        return self._supply_repo.obtener_insumos_en_alerta()

    def asociar_insumo_a_producto(
        self,
        autor: Usuario,
        id_producto: int,
        id_insumo: int,
        cantidad_necesaria: float,
    ) -> int:
        self._verificar_permiso(autor, Permiso.INVENTARIO)

        producto = self._product_repo.obtener_por_id(id_producto)
        if producto is None:
            raise ValidacionError("El producto especificado no existe.")

        insumo = self._supply_repo.obtener_por_id(id_insumo)
        if insumo is None:
            raise ValidacionError("El insumo especificado no existe.")

        if cantidad_necesaria <= 0.0:
            raise ValidacionError("La cantidad necesaria debe ser mayor a cero.")

        id_receta = self._recipe_repo.asociar_insumo_a_producto(id_producto, id_insumo, cantidad_necesaria)
        self._registrar_auditoria(
            "RECETA_CONFIGURADA",
            autor.id_usuario,
            f"Receta producto id={id_producto} ('{producto.nombre}') asociada con insumo id={id_insumo} ('{insumo.nombre}', cant: {cantidad_necesaria}) por '{autor.username}'.",
        )
        return id_receta

    def obtener_receta_por_producto(self, id_producto: int) -> List[Receta]:
        return self._recipe_repo.obtener_receta_por_producto(id_producto)

    def eliminar_insumo_de_receta(self, autor: Usuario, id_receta: int) -> bool:
        self._verificar_permiso(autor, Permiso.INVENTARIO)

        receta = self._recipe_repo.obtener_receta_por_id(id_receta)
        if receta is None:
            raise ValidacionError("El registro de receta especificado no existe.")

        resultado = self._recipe_repo.eliminar_insumo_de_receta(id_receta)
        self._registrar_auditoria(
            "RECETA_ITEM_ELIMINADO",
            autor.id_usuario,
            f"Registro de receta id={id_receta} eliminado por '{autor.username}'.",
        )
        return resultado
