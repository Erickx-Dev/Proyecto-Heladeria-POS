# Sistema de Diseño Visual e Interfaz Gráfica (UI Design System)

> **Documento:** `docs/ui_design_system.md`  
> **Aprobado por el Tech Lead:** Erickson Sojo  
> **Tema:** *Heladería Artesanal Fresca & Dorada (Celeste, Frambuesa Pastel y Detalles Dorados)*  
> **Framework Base:** `customtkinter` (Python 3)  
> **Filosofía Visual:** Experiencia de mostrador fresca, moderna y ágil para el día a día en la heladería, con acentos dorados artesanales que aportan un toque premium y profesional.

---

## 1. Tokens de Color (Paleta Oficial)

Todos los componentes deben consumir estos valores centralizados en `src/ui/theme.py`, evitando colores fijos sueltos en el código.

| Token | Valor HEX | Uso / Semántica |
| :--- | :--- | :--- |
| `COLOR_FONDO_VENTANA` | `#1B2430` | Fondo general de la aplicación (azul marino grisáceo profundo). |
| `COLOR_SUPERFICIE` | `#222E3D` | Fondo de paneles, tarjetas de producto, sidebar y tablas. |
| `COLOR_SUPERFICIE_HOVER` | `#2C3B4E` | Estado hover de tarjetas, filas de tabla y contenedores interactivos. |
| `COLOR_BORDE_SUAVE` | `#334458` | Líneas divisorias, bordes sutiles de paneles y cajas de texto. |
| **`COLOR_ACENTO_CYAN`** | `#00F0FF` | Acento helado fresco: botones de filtro, selecciones activas y pestañas. |
| **`COLOR_ACENTO_CELESTE`**| `#48CAE4` | Celeste suave: iconos, etiquetas informativas y estados secundarios. |
| **`COLOR_DORADO_PREMIUM`** | `#E5B869` | **Dorado cálido artesanal:** insignias, cifras de dinero, títulos destacados y marcos de turno/caja. |
| **`COLOR_DORADO_HOVER`**   | `#F7C978` | Hover en elementos con acabado dorado. |
| **`COLOR_COBRO_FRAMBUESA`**| `#FF5C8D` | **Botón de Cobrar y acciones principales de alta prioridad.** |
| `COLOR_COBRO_HOVER`       | `#E04876` | Hover del botón de cobro. |
| `COLOR_EXITO`              | `#06D6A0` | Verde menta para estados activos, cuadre de caja exacto y ventas guardadas. |
| `COLOR_PELIGRO`            | `#EF476F` | Rojo frambuesa intenso para eliminar ítems, mermas, cierres y alertas críticas. |
| `COLOR_TEXTO_TITULO`       | `#FFFFFF` | Blanco puro para encabezados y nombres de producto. |
| `COLOR_TEXTO_CUERPO`       | `#D8E2EC` | Texto estándar de lectura (alta legibilidad contra fondo azul grisáceo). |
| `COLOR_TEXTO_MUTED`        | `#8A9BB0` | Texto secundario, unidades de medida y marcas de agua. |

---

## 2. Geometría, Radios y Espaciados

Siguiendo la decisión de **esquinas redondeadas modernas**:

* **Botones de acción y filtros:** `corner_radius = 12`
* **Tarjetas táctiles de producto (`ProductCard`):** `corner_radius = 12`, borde sutil `border_width = 1` en `COLOR_BORDE_SUAVE`.
* **Paneles principales y contenedores (`CTkFrame`):** `corner_radius = 16`.
* **Ventanas modales (Cobro, Arqueo):** `corner_radius = 16`.
* **Cajas de texto (`CTkEntry`):** `corner_radius = 10`.
* **Espaciados estándar (`padding`):**
  * Entre tarjetas: `padx = 8`, `pady = 8`.
  * Relleno interno de paneles: `padx = 16`, `pady = 16`.
  * Margen exterior de la ventana: `padx = 12`, `pady = 12`.

---

## 3. Tipografía Oficial

Usando la familia tipográfica moderna del sistema (`Segoe UI` en Windows / `Helvetica` en POS touch):

* **Títulos de Pantalla:** `("Segoe UI", 22, "bold")` — Color `#FFFFFF` con línea base en `#E5B869` (Dorado).
* **Cifra de Total / Cobro:** `("Segoe UI", 24, "bold")` — Color `#E5B869` (Dorado) o `#00F0FF` (Cyan).
* **Nombres de Producto en Tarjeta:** `("Segoe UI", 13, "bold")` — Color `#FFFFFF`.
* **Precios en Tarjeta:** `("Segoe UI", 13, "bold")` — Color `#48CAE4` (Celeste helado).
* **Botones Principales:** `("Segoe UI", 13, "bold")`.
* **Etiquetas y Tablas:** `("Segoe UI", 12)`.
* **Subtextos y Unidades:** `("Segoe UI", 10)`.

---

## 4. Distribución del Mostrador Principal (`POSView`)

Estructura de dos columnas divididas:

```
+-----------------------------------------------------------------------------------------+
|                                    BARRA SUPERIOR (HEADER)                               |
|  [Logo Heladería + Titulo Dorado]           [Turno Caja #1: ABIERTA]  [Usuario: admin]  |
+-------------------------------------------------------------------+---------------------+
|  COLUMNA IZQUIERDA (70%): CATÁLOGO TÁCTIL                         | COLUMNA DERECHA(30%)|
|  +--------------------------------------------------------------+ | [Comanda de Venta]  |
|  | [Buscador] [Todos] [Helados] [Bebidas] [Toppings]            | |                     |
|  +--------------------------------------------------------------+ | 1. Helado Fresa x2  |
|  | [ HELADO FRESA ]   [ HELADO VAINILLA ]   [ MALTEADA CHOCO ]  | |    $10,000.00 [x]   |
|  |   $5,000  (Cyan)     $4,000  (Cyan)        $8,000  (Cyan)    | | 2. Topping Chips x1 |
|  |   [+ Agregar]        [+ Agregar]           [+ Agregar]       | |    $1,500.00  [x]   |
|  |                                                              | | ------------------- |
|  | [ CONO DOBLE ]     [ PALETA ARTESANAL]   [ COPA ESPECIAL ]   | | SUBTOTAL: $11,500   |
|  |   $7,500             $3,500                $12,000           | | TOTAL:    $11,500   |
|  |   [+ Agregar]        [+ Agregar]           [+ Agregar]       | | (Dorado Grande)     |
|  +--------------------------------------------------------------+ |                     |
|                                                                   | [ BOTÓN COBRAR ]    |
|                                                                   | (Rosa Frambuesa)    |
+-------------------------------------------------------------------+---------------------+
```

---

## 5. Navegación Lateral (`SidebarNavigation`)

* Ubicación: Barra vertical a la izquierda con ancho compacto (200 px).
* Color de fondo: `#161D27` (un tono ligeramente más profundo para jerarquía visual).
* Botones de navegación:
  * Icono/Emoji + Nombre del módulo.
  * Botón seleccionado: fondo `#2C3B4E` con barra indicadora vertical izquierda en `#00F0FF` (Cyan) y texto en `#FFFFFF`.
  * Botón no seleccionado: fondo transparente, texto `#A6B7CC`, hover en `#222E3D`.
* Permisos automáticos:
  * **Empleado:** Muestra solo *POS / Venta* y *Caja / Turno*.
  * **Administrador:** Muestra *POS*, *Caja*, *Catálogo*, *Inventario*, *Mermas*, *Gastos*, *Reportes*, *Usuarios* y *Respaldo*.
