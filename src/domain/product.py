from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Producto:
    codigo: str
    nombre: str
    precio_venta: float
    id_categoria: int
    estado: int = 1
    id_producto: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.codigo or not self.codigo.strip():
            raise ValueError("El código del producto no puede estar vacío.")
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío.")
        if self.precio_venta < 0.0:
            raise ValueError("El precio de venta no puede ser negativo.")
        if self.id_categoria <= 0:
            raise ValueError("El id_categoria debe ser un entero positivo válido.")
        if self.estado not in (0, 1):
            raise ValueError("El estado del producto debe ser 1 (activo) o 0 (suspendido/inactivo).")

        self.codigo = self.codigo.strip()
        self.nombre = self.nombre.strip()
        self.precio_venta = round(float(self.precio_venta), 2)
        self.id_categoria = int(self.id_categoria)
        self.estado = int(self.estado)

    def esta_activo(self) -> bool:
        return self.estado == 1

    def activar(self) -> None:
        self.estado = 1

    def suspender(self) -> None:
        self.estado = 0

    def actualizar_precio(self, nuevo_precio: float) -> None:
        if nuevo_precio < 0.0:
            raise ValueError("El precio de venta no puede ser negativo.")
        self.precio_venta = round(float(nuevo_precio), 2)


@dataclass
class ProductoSimple(Producto):
    id_insumo_directo: Optional[int] = None


@dataclass
class ProductoCompuesto(Producto):
    receta: Dict[int, float] = field(default_factory=dict)

    def agregar_insumo_receta(self, id_insumo: int, cantidad: float) -> None:
        if id_insumo <= 0:
            raise ValueError("El id_insumo debe ser un identificador positivo válido.")
        if cantidad <= 0:
            raise ValueError("La cantidad de insumo en la receta debe ser estrictamente positiva.")
        self.receta[id_insumo] = round(float(cantidad), 4)

    def quitar_insumo_receta(self, id_insumo: int) -> None:
        self.receta.pop(id_insumo, None)

    def obtener_receta(self) -> Dict[int, float]:
        return dict(self.receta)
