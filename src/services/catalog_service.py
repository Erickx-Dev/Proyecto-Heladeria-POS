from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from database.connection import get_db_transaction
from src.core.exceptions import AutorizacionError, ValidacionError
from src.domain.category import Categoria
from src.domain.product import Producto
from src.domain.user import Permiso, Usuario
from src.repositories.category_repository import CategoryRepository
from src.repositories.product_repository import ProductRepository


class CatalogService:

    def __init__(
        self,
        category_repository: Optional[CategoryRepository] = None,
        product_repository: Optional[ProductRepository] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._db_path: Optional[Union[str, Path]] = db_path
        self._category_repo: CategoryRepository = category_repository or CategoryRepository(db_path=db_path)
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
                (id_usuario, accion, "CATALOGO", fecha_hora, detalles),
            )

    def _verificar_permiso(self, autor: Usuario, permiso: Permiso) -> None:
        if not autor.has_permission(permiso):
            raise AutorizacionError(
                f"El usuario '{autor.username}' no tiene el permiso '{permiso.value}'."
            )

    def crear_categoria(
        self,
        autor: Usuario,
        nombre_categoria: str,
        descripcion: Optional[str] = None,
    ) -> Categoria:
        self._verificar_permiso(autor, Permiso.CATALOGO)

        if not nombre_categoria or not nombre_categoria.strip():
            raise ValidacionError("El nombre de la categoría no puede estar vacío.")

        existente = self._category_repo.obtener_por_nombre(nombre_categoria.strip())
        if existente is not None:
            raise ValidacionError(f"La categoría '{nombre_categoria.strip()}' ya existe.")

        categoria = Categoria(
            nombre_categoria=nombre_categoria.strip(),
            descripcion=descripcion.strip() if descripcion else None,
        )
        id_categoria = self._category_repo.crear_categoria(categoria)
        categoria.id_categoria = id_categoria

        self._registrar_auditoria(
            "CATEGORIA_CREADA",
            autor.id_usuario,
            f"Categoría id={id_categoria} '{categoria.nombre_categoria}' creada por '{autor.username}'.",
        )

        return categoria

    def actualizar_categoria(
        self,
        autor: Usuario,
        id_categoria: int,
        nombre_categoria: str,
        descripcion: Optional[str] = None,
    ) -> Categoria:
        self._verificar_permiso(autor, Permiso.CATALOGO)

        categoria_actual = self._category_repo.obtener_por_id(id_categoria)
        if categoria_actual is None:
            raise ValidacionError("La categoría especificada no existe.")

        if not nombre_categoria or not nombre_categoria.strip():
            raise ValidacionError("El nombre de la categoría no puede estar vacío.")

        nombre_limpio = nombre_categoria.strip()
        existente = self._category_repo.obtener_por_nombre(nombre_limpio)
        if existente is not None and existente.id_categoria != id_categoria:
            raise ValidacionError(f"El nombre '{nombre_limpio}' ya está siendo utilizado por otra categoría.")

        categoria_actualizada = Categoria(
            id_categoria=id_categoria,
            nombre_categoria=nombre_limpio,
            descripcion=descripcion.strip() if descripcion else None,
        )
        self._category_repo.actualizar_categoria(categoria_actualizada)

        self._registrar_auditoria(
            "CATEGORIA_ACTUALIZADA",
            autor.id_usuario,
            f"Categoría id={id_categoria} actualizada por '{autor.username}'.",
        )

        return categoria_actualizada

    def eliminar_categoria(self, autor: Usuario, id_categoria: int) -> bool:
        self._verificar_permiso(autor, Permiso.CATALOGO)

        categoria = self._category_repo.obtener_por_id(id_categoria)
        if categoria is None:
            raise ValidacionError("La categoría especificada no existe.")

        productos_asociados = self._product_repo.listar_productos(id_categoria=id_categoria)
        if productos_asociados:
            raise ValidacionError(
                f"No se puede eliminar la categoría '{categoria.nombre_categoria}' porque tiene {len(productos_asociados)} producto(s) asociado(s)."
            )

        resultado = self._category_repo.eliminar_categoria(id_categoria)
        self._registrar_auditoria(
            "CATEGORIA_ELIMINADA",
            autor.id_usuario,
            f"Categoría id={id_categoria} '{categoria.nombre_categoria}' eliminada por '{autor.username}'.",
        )
        return resultado

    def obtener_categoria_por_id(self, id_categoria: int) -> Optional[Categoria]:
        return self._category_repo.obtener_por_id(id_categoria)

    def listar_categorias(self) -> List[Categoria]:
        return self._category_repo.listar_categorias()

    def crear_producto(
        self,
        autor: Usuario,
        codigo: str,
        nombre: str,
        precio_venta: float,
        id_categoria: int,
        estado: int = 1,
    ) -> Producto:
        self._verificar_permiso(autor, Permiso.CATALOGO)

        if not codigo or not codigo.strip():
            raise ValidacionError("El código del producto no puede estar vacío.")

        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del producto no puede estar vacío.")

        if precio_venta < 0.0:
            raise ValidacionError("El precio de venta no puede ser negativo.")

        if self._category_repo.obtener_por_id(id_categoria) is None:
            raise ValidacionError("La categoría especificada no existe.")

        if self._product_repo.obtener_por_codigo(codigo.strip()) is not None:
            raise ValidacionError(f"El código '{codigo.strip()}' ya está en uso.")

        producto = Producto(
            codigo=codigo.strip().upper(),
            nombre=nombre.strip(),
            precio_venta=precio_venta,
            id_categoria=id_categoria,
            estado=estado,
        )
        id_producto = self._product_repo.crear_producto(producto)
        producto.id_producto = id_producto

        self._registrar_auditoria(
            "PRODUCTO_CREADO",
            autor.id_usuario,
            f"Producto id={id_producto} '{producto.nombre}' (código: {producto.codigo}) creado por '{autor.username}'.",
        )

        return producto

    def actualizar_producto(
        self,
        autor: Usuario,
        id_producto: int,
        codigo: str,
        nombre: str,
        precio_venta: float,
        id_categoria: int,
        estado: int,
    ) -> Producto:
        self._verificar_permiso(autor, Permiso.CATALOGO)

        producto_actual = self._product_repo.obtener_por_id(id_producto)
        if producto_actual is None:
            raise ValidacionError("El producto especificado no existe.")

        if not codigo or not codigo.strip():
            raise ValidacionError("El código del producto no puede estar vacío.")

        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del producto no puede estar vacío.")

        if precio_venta < 0.0:
            raise ValidacionError("El precio de venta no puede ser negativo.")

        if self._category_repo.obtener_por_id(id_categoria) is None:
            raise ValidacionError("La categoría especificada no existe.")

        codigo_limpio = codigo.strip().upper()
        existente_codigo = self._product_repo.obtener_por_codigo(codigo_limpio)
        if existente_codigo is not None and existente_codigo.id_producto != id_producto:
            raise ValidacionError(f"El código '{codigo_limpio}' ya está siendo utilizado por otro producto.")

        producto_actualizado = Producto(
            id_producto=id_producto,
            codigo=codigo_limpio,
            nombre=nombre.strip(),
            precio_venta=precio_venta,
            id_categoria=id_categoria,
            estado=estado,
        )
        self._product_repo.actualizar_producto(producto_actualizado)

        self._registrar_auditoria(
            "PRODUCTO_ACTUALIZADO",
            autor.id_usuario,
            f"Producto id={id_producto} actualizado por '{autor.username}'.",
        )

        return producto_actualizado

    def cambiar_estado_producto(
        self,
        autor: Usuario,
        id_producto: int,
        nuevo_estado: int,
    ) -> bool:
        self._verificar_permiso(autor, Permiso.CATALOGO)

        producto = self._product_repo.obtener_por_id(id_producto)
        if producto is None:
            raise ValidacionError("El producto especificado no existe.")

        resultado = self._product_repo.cambiar_estado(id_producto, nuevo_estado)
        self._registrar_auditoria(
            "PRODUCTO_ESTADO_CAMBIADO",
            autor.id_usuario,
            f"Estado del producto id={id_producto} cambiado a {nuevo_estado} por '{autor.username}'.",
        )
        return resultado

    def obtener_producto_por_id(self, id_producto: int) -> Optional[Producto]:
        return self._product_repo.obtener_por_id(id_producto)

    def obtener_producto_por_codigo(self, codigo: str) -> Optional[Producto]:
        return self._product_repo.obtener_por_codigo(codigo.strip())

    def listar_productos(
        self,
        solo_activos: bool = False,
        id_categoria: Optional[int] = None,
    ) -> List[Producto]:
        return self._product_repo.listar_productos(solo_activos=solo_activos, id_categoria=id_categoria)
