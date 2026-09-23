"""
Servicio de Aplicación: CatalogService.

Orquesta la lógica de negocio y las operaciones CRUD para el catálogo
comercial (productos, categorías) y el inventario de materias primas (insumos),
cumpliendo con la separación estricta de capas y principios SOLID.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union

from src.core.exceptions import (
    CategoriaNoEncontradaError,
    InsumoNoEncontradoError,
    ProductoNoEncontradoError,
    ReglaNegocioError,
)
from src.domain.category import Categoria
from src.domain.product import Producto, ProductoCompuesto, ProductoSimple
from src.domain.supply import Insumo
from src.repositories.category_repository import CategoryRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.supply_repository import SupplyRepository


class CatalogService:
    """
    Servicio integral para la gestión comercial del catálogo y los insumos de bodega.
    """

    def __init__(
        self,
        category_repo: Optional[CategoryRepository] = None,
        supply_repo: Optional[SupplyRepository] = None,
        product_repo: Optional[ProductRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Inicializa el servicio inyectando los repositorios requeridos.
        """
        self.category_repo = category_repo or CategoryRepository(db_path=db_path)
        self.supply_repo = supply_repo or SupplyRepository(db_path=db_path)
        self.product_repo = product_repo or ProductRepository(db_path=db_path)

    # --------------------------------------------------------------------------
    # 1. GESTIÓN DE CATEGORÍAS
    # --------------------------------------------------------------------------

    def crear_categoria(self, nombre_categoria: str, descripcion: Optional[str] = None) -> Categoria:
        """
        Registra una nueva categoría de productos.
        """
        nueva_cat = Categoria(nombre_categoria=nombre_categoria, descripcion=descripcion)
        return self.category_repo.crear(nueva_cat)

    def obtener_categoria(self, id_categoria: int) -> Categoria:
        """
        Recupera una categoría por su ID.

        Raises:
            CategoriaNoEncontradaError: Si no existe la categoría.
        """
        cat = self.category_repo.obtener_por_id(id_categoria)
        if not cat:
            raise CategoriaNoEncontradaError(f"No se encontró la categoría con ID {id_categoria}.")
        return cat

    def listar_categorias(self) -> List[Categoria]:
        """Retorna todas las categorías del catálogo."""
        return self.category_repo.listar_todas()

    def actualizar_categoria(
        self, id_categoria: int, nombre_categoria: str, descripcion: Optional[str] = None
    ) -> Categoria:
        """
        Actualiza el nombre y descripción de una categoría existente.
        """
        cat = self.obtener_categoria(id_categoria)
        cat.nombre_categoria = nombre_categoria
        cat.descripcion = descripcion
        # Valida invariantes mediante __post_init__ implícito
        cat = Categoria(
            id_categoria=cat.id_categoria,
            nombre_categoria=nombre_categoria,
            descripcion=descripcion,
        )
        self.category_repo.actualizar(cat)
        return cat

    def eliminar_categoria(self, id_categoria: int) -> bool:
        """
        Elimina una categoría si no contiene productos asignados.
        """
        # Verificar que la categoría exista
        self.obtener_categoria(id_categoria)

        # Validar si existen productos asignados a la categoría
        productos_asociados = self.product_repo.listar_por_categoria(id_categoria)
        if productos_asociados:
            raise ReglaNegocioError(
                f"No se puede eliminar la categoría #{id_categoria} porque tiene "
                f"{len(productos_asociados)} producto(s) asignado(s)."
            )

        return self.category_repo.eliminar(id_categoria)

    # --------------------------------------------------------------------------
    # 2. GESTIÓN DE INSUMOS DE BODEGA
    # --------------------------------------------------------------------------

    def crear_insumo(
        self,
        nombre: str,
        unidad_medida: str,
        stock_actual: float = 0.0,
        stock_minimo: float = 0.0,
    ) -> Insumo:
        """
        Registra una nueva materia prima o insumo (helado por sabor, conos, vasos, toppings).
        """
        insumo = Insumo(
            nombre=nombre,
            unidad_medida=unidad_medida,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
        )
        return self.supply_repo.crear(insumo)

    def obtener_insumo(self, id_insumo: int) -> Insumo:
        """
        Recupera un insumo por su ID.

        Raises:
            InsumoNoEncontradoError: Si no existe el insumo.
        """
        insumo = self.supply_repo.obtener_por_id(id_insumo)
        if not insumo:
            raise InsumoNoEncontradoError(f"No se encontró el insumo con ID {id_insumo}.")
        return insumo

    def listar_insumos(self) -> List[Insumo]:
        """Retorna la lista completa de insumos de bodega."""
        return self.supply_repo.listar_todos()

    def listar_insumos_en_alerta(self) -> List[Insumo]:
        """
        Retorna los insumos que han alcanzado o traspasado el umbral de stock mínimo.
        """
        return self.supply_repo.listar_con_alerta_stock()

    def asentar_abastecimiento(
        self, id_insumo: int, cantidad: float, costo_unitario: Optional[float] = None
    ) -> Insumo:
        """
        Asienta una entrada de mercancía por compra o reabastecimiento de bodega.

        Args:
            id_insumo: Identificador del insumo a abastecer.
            cantidad: Volumen o piezas recibidas (> 0).
            costo_unitario: Precio de compra por unidad opcional con fines informativos.
        """
        if cantidad <= 0:
            raise ReglaNegocioError("La cantidad a abastecer debe ser mayor a cero.")
        if costo_unitario is not None and costo_unitario < 0:
            raise ReglaNegocioError("El costo unitario no puede ser negativo.")

        insumo = self.obtener_insumo(id_insumo)
        insumo.asentar_abastecimiento(cantidad)
        self.supply_repo.actualizar_stock(id_insumo, insumo.stock_actual)
        return insumo

    def actualizar_insumo(
        self,
        id_insumo: int,
        nombre: str,
        unidad_medida: str,
        stock_minimo: float,
    ) -> Insumo:
        """
        Actualiza los metadatos y el umbral de alerta de un insumo existente.
        """
        insumo = self.obtener_insumo(id_insumo)
        insumo_actualizado = Insumo(
            id_insumo=id_insumo,
            nombre=nombre,
            unidad_medida=unidad_medida,
            stock_actual=insumo.stock_actual,
            stock_minimo=stock_minimo,
        )
        self.supply_repo.actualizar(insumo_actualizado)
        return insumo_actualizado

    def eliminar_insumo(self, id_insumo: int) -> bool:
        """Elimina un insumo del catálogo."""
        self.obtener_insumo(id_insumo)
        return self.supply_repo.eliminar(id_insumo)

    # --------------------------------------------------------------------------
    # 3. GESTIÓN DE PRODUCTOS COMERCIALES (POS)
    # --------------------------------------------------------------------------

    def crear_producto_simple(
        self,
        codigo: str,
        nombre: str,
        precio_venta: float,
        id_categoria: int,
        id_insumo_directo: Optional[int] = None,
    ) -> ProductoSimple:
        """
        Crea y registra un producto simple (sin receta compuesta de insumos).
        """
        self.obtener_categoria(id_categoria)
        if id_insumo_directo is not None:
            self.obtener_insumo(id_insumo_directo)

        prod = ProductoSimple(
            codigo=codigo,
            nombre=nombre,
            precio_venta=precio_venta,
            id_categoria=id_categoria,
            id_insumo_directo=id_insumo_directo,
        )
        self.product_repo.crear(prod)
        return prod

    def crear_producto_compuesto(
        self,
        codigo: str,
        nombre: str,
        precio_venta: float,
        id_categoria: int,
        receta: Optional[Dict[int, float]] = None,
    ) -> ProductoCompuesto:
        """
        Crea y registra un producto compuesto (conos dobles, copas gourmet, malteadas)
        con formulación de insumos de bodega.
        """
        self.obtener_categoria(id_categoria)

        # Validar que los insumos de la receta existan
        formula: Dict[int, float] = {}
        if receta:
            for id_insumo, cant in receta.items():
                self.obtener_insumo(id_insumo)
                if cant <= 0:
                    raise ReglaNegocioError(
                        f"La dosificación del insumo #{id_insumo} debe ser mayor a cero."
                    )
                formula[id_insumo] = cant

        prod = ProductoCompuesto(
            codigo=codigo,
            nombre=nombre,
            precio_venta=precio_venta,
            id_categoria=id_categoria,
            receta=formula,
        )
        self.product_repo.crear(prod)
        return prod

    def obtener_producto(self, id_producto: int) -> Producto:
        """
        Recupera un producto por su ID.

        Raises:
            ProductoNoEncontradoError: Si no existe el producto.
        """
        prod = self.product_repo.obtener_por_id(id_producto)
        if not prod:
            raise ProductoNoEncontradoError(f"No se encontró el producto con ID {id_producto}.")
        return prod

    def obtener_producto_por_codigo(self, codigo: str) -> Producto:
        """
        Recupera un producto por su código único de venta rápida.
        """
        prod = self.product_repo.obtener_por_codigo(codigo)
        if not prod:
            raise ProductoNoEncontradoError(f"No se encontró el producto con código '{codigo}'.")
        return prod

    def listar_productos(self, solo_activos: bool = False) -> List[Producto]:
        """
        Retorna la lista de productos del catálogo comercial.
        """
        return self.product_repo.listar_todos(solo_activos=solo_activos)

    def listar_productos_por_categoria(
        self, id_categoria: int, solo_activos: bool = False
    ) -> List[Producto]:
        """
        Retorna los productos filtrados por categoría.
        """
        self.obtener_categoria(id_categoria)
        return self.product_repo.listar_por_categoria(id_categoria, solo_activos=solo_activos)

    def actualizar_precio_producto(self, id_producto: int, nuevo_precio: float) -> Producto:
        """
        Actualiza el precio de venta al público de un producto.
        """
        if nuevo_precio < 0.0:
            raise ReglaNegocioError("El precio de venta no puede ser negativo.")

        prod = self.obtener_producto(id_producto)
        self.product_repo.actualizar_precio(id_producto, nuevo_precio)
        prod.actualizar_precio(nuevo_precio)
        return prod

    def suspender_producto(self, id_producto: int) -> Producto:
        """
        Deshabilita o suspende temporalmente un producto del menú de venta.
        """
        prod = self.obtener_producto(id_producto)
        self.product_repo.cambiar_estado(id_producto, 0)
        prod.suspender()
        return prod

    def activar_producto(self, id_producto: int) -> Producto:
        """
        Habilita un producto previamente suspendido para que vuelva a estar disponible en el POS.
        """
        prod = self.obtener_producto(id_producto)
        self.product_repo.cambiar_estado(id_producto, 1)
        prod.activar()
        return prod

    def asociar_categoria_producto(self, id_producto: int, nuevo_id_categoria: int) -> Producto:
        """
        Reasigna la categoría comercial de un producto.
        """
        self.obtener_categoria(nuevo_id_categoria)
        prod = self.obtener_producto(id_producto)
        prod.id_categoria = nuevo_id_categoria
        self.product_repo.actualizar(prod)
        return prod

    def actualizar_producto(self, producto: Producto) -> Producto:
        """
        Actualiza los datos maestros de un producto en el catálogo.
        """
        if not producto.id_producto:
            raise ValueError("No se puede actualizar un producto sin ID asignado.")

        self.obtener_categoria(producto.id_categoria)
        self.product_repo.actualizar(producto)
        return producto

    def eliminar_producto(self, id_producto: int) -> bool:
        """
        Elimina un producto del catálogo (si no tiene ventas asociadas).
        """
        self.obtener_producto(id_producto)
        return self.product_repo.eliminar(id_producto)
