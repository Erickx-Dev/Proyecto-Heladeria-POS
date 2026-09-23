from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from src.core.exceptions import ProductoNoEncontradoError
from src.domain.product import Categoria, Producto
from src.repositories.product_repository import ProductRepository


class ProductService:

    def __init__(
        self,
        repository: Optional[ProductRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._repository: ProductRepository = (
            repository if repository is not None else ProductRepository(db_path=db_path)
        )

    def listar_categorias(self) -> List[Categoria]:
        return self._repository.listar_categorias()

    def obtener_categoria(self, id_categoria: int) -> Optional[Categoria]:
        return self._repository.obtener_categoria_por_id(id_categoria)

    def crear_categoria(self, nombre: str, descripcion: Optional[str] = None) -> Categoria:
        categoria = Categoria(id_categoria=None, nombre_categoria=nombre, descripcion=descripcion)
        id_generado = self._repository.crear_categoria(categoria)
        categoria.id_categoria = id_generado
        return categoria

    def listar_productos_activos(self) -> List[Producto]:
        return self._repository.listar_productos(solo_activos=True)

    def listar_productos_por_categoria(
        self, id_categoria: int, solo_activos: bool = True
    ) -> List[Producto]:
        return self._repository.listar_productos_por_categoria(
            id_categoria=id_categoria, solo_activos=solo_activos
        )

    def obtener_producto_por_id(self, id_producto: int) -> Producto:
        producto = self._repository.obtener_producto_por_id(id_producto)
        if producto is None:
            raise ProductoNoEncontradoError(id_producto)
        return producto

    def obtener_producto_por_codigo(self, codigo: str) -> Producto:
        producto = self._repository.obtener_producto_por_codigo(codigo)
        if producto is None:
            raise ProductoNoEncontradoError(codigo)
        return producto

    def registrar_producto(
        self,
        codigo: str,
        nombre: str,
        precio_venta: float,
        id_categoria: int,
        estado: int = 1,
    ) -> Producto:
        producto = Producto(
            id_producto=None,
            codigo=codigo,
            nombre=nombre,
            precio_venta=precio_venta,
            id_categoria=id_categoria,
            estado=estado,
        )
        id_generado = self._repository.crear_producto(producto)
        producto.id_producto = id_generado
        return producto

    def actualizar_producto(
        self,
        id_producto: int,
        codigo: str,
        nombre: str,
        precio_venta: float,
        id_categoria: int,
        estado: int = 1,
    ) -> Producto:
        self.obtener_producto_por_id(id_producto)
        producto = Producto(
            id_producto=id_producto,
            codigo=codigo,
            nombre=nombre,
            precio_venta=precio_venta,
            id_categoria=id_categoria,
            estado=estado,
        )
        self._repository.actualizar_producto(producto)
        return producto

    def desactivar_producto(self, id_producto: int) -> bool:
        self.obtener_producto_por_id(id_producto)
        return self._repository.cambiar_estado_producto(id_producto, nuevo_estado=0)

    def activar_producto(self, id_producto: int) -> bool:
        self.obtener_producto_por_id(id_producto)
        return self._repository.cambiar_estado_producto(id_producto, nuevo_estado=1)
