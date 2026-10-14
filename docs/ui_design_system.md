# Sistema de Diseño Visual e Interfaz Gráfica (UI Design System)

> **Documento:** `docs/ui_design_system.md`  
> **Aprobado por el Tech Lead:** Erickson Sojo  
> **Tema:** *Heladería Artesanal Grafito Cálido & Oro (Carbón Suave, Frambuesa Pastel y Detalles en Oro Artesanal)*  
> **Framework Base:** `customtkinter` (Python 3)  
> **Filosofía Visual:** Experiencia de mostrador refinada, moderna y ágil para el día a día en la heladería, con fondos neutros en grafito cálido libre de tinte azulado y acentos dorados artesanales que aportan un toque premium y profesional.

---

## 1. Tokens de Color (Paleta Oficial)

Todos los componentes deben consumir estos valores centralizados en `src/ui/theme.py`, evitando colores fijos sueltos en el código.

| Token | Valor HEX | Uso / Semántica |
| :--- | :--- | :--- |
| `COLOR_FONDO_VENTANA` | `#2B2E36` | Fondo general de la aplicación (grafito cálido neutro, más claro y sin tinte azul). |
| `COLOR_SIDEBAR` | `#212328` | Barra lateral de navegación en grafito oscuro sobrio. |
| `COLOR_SUPERFICIE` | `#363A44` | Fondo de paneles, tarjetas de producto, comanda y tablas (carbón suave de alto contraste). |
| `COLOR_SUPERFICIE_HOVER` | `#434855` | Estado hover de tarjetas, filas de tabla y contenedores interactivos. |
| `COLOR_BORDE_SUAVE` | `#4A4F5C` | Líneas divisorias, bordes sutiles de paneles y cajas de texto (gris neutro). |
| `COLOR_BORDE_DORADO` | `#E5B869` | Filetes y bordes destacados en oro artesanal. |
| **`COLOR_DORADO_PREMIUM`** | `#E5B869` | **Dorado cálido artesanal:** categoría activa, botón activo de navegación, botón "+ Agregar", precios y totales. |
| **`COLOR_DORADO_HOVER`**   | `#F7C978` | Hover en elementos con acabado dorado. |
| **`COLOR_DORADO_TEXTO_OSCURO`** | `#1C1E22` | Texto oscuro de máxima legibilidad y contraste sobre botones de fondo dorado. |
| **`COLOR_COBRO_FRAMBUESA`**| `#FF5C8D` | **Botón de Cobrar y acciones principales de alta prioridad.** |
| `COLOR_COBRO_HOVER`       | `#E04876` | Hover del botón de cobro. |
| `COLOR_EXITO`              | `#06D6A0` | Verde menta para estados activos, cuadre de caja exacto y ventas guardadas. |
| `COLOR_PELIGRO`            | `#EF476F` | Rojo frambuesa intenso para eliminar ítems, mermas, cierres y alertas críticas. |
| `COLOR_TEXTO_TITULO`       | `#FFFFFF` | Blanco puro para encabezados y nombres de producto. |
| `COLOR_TEXTO_CUERPO`       | `#E1E4EA` | Texto estándar de lectura (alta legibilidad contra fondo carbón). |
| `COLOR_TEXTO_MUTED`        | `#9EA5B3` | Texto secundario, unidades de medida y marcas de agua. |
| `COLOR_BOTON_SECUNDARIO`   | `#3D424E` | Fondo de botones secundarios y controles de cantidad. |
| `COLOR_BOTON_SECUNDARIO_HOVER` | `#4D5363` | Hover de botones secundarios. |

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
