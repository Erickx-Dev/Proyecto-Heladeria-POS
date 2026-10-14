# Sistema de Diseño Visual e Interfaz Gráfica (UI Design System)

> **Documento:** `docs/ui_design_system.md`  
> **Aprobado por el Tech Lead:** Erickson Sojo  
> **Tema:** *Light Mode Moderno (Blanco Puro & Gris Nube con Acentos en Oro Artesanal y Frambuesa)*  
> **Framework Base:** `customtkinter` (Python 3, modo de apariencia `light`)  
> **Filosofía Visual:** Experiencia de mostrador luminosa, fresca, moderna y 100% armónica, eliminando contrastes discordantes mediante fondo gris nube suave, tarjetas blancas con bordes sutiles y detalles premium en oro y frambuesa.

---

## 1. Tokens de Color (Paleta Oficial Light Mode)

Todos los componentes consumen estos valores centralizados en `src/ui/theme.py`:

| Token | Valor HEX | Uso / Semántica |
| :--- | :--- | :--- |
| `COLOR_FONDO_VENTANA` | `#F4F6F9` | Fondo general de la aplicación (gris nube suave, evita deslumbramientos). |
| `COLOR_SIDEBAR` | `#FFFFFF` | Barra lateral de navegación en blanco puro con divisor derecho. |
| `COLOR_SUPERFICIE` | `#FFFFFF` | Fondo de paneles, tarjetas de producto, comanda y tablas. |
| `COLOR_SUPERFICIE_HOVER` | `#F8FAFC` | Estado hover de tarjetas, filas de tabla y contenedores interactivos. |
| `COLOR_BORDE_SUAVE` | `#E2E8F0` | Líneas divisorias y bordes sutiles de paneles y tarjetas. |
| `COLOR_BORDE_DORADO` | `#D97706` | Filetes y bordes destacados en oro artesanal. |
| **`COLOR_DORADO_PREMIUM`** | `#D97706` | **Dorado cálido artesanal:** categoría activa, botón activo de navegación, precios y totales. |
| **`COLOR_DORADO_HOVER`**   | `#B45309` | Hover en elementos con acabado dorado. |
| **`COLOR_DORADO_TEXTO_OSCURO`** | `#FFFFFF` | Texto de contraste sobre botones con fondo dorado. |
| **`COLOR_COBRO_FRAMBUESA`**| `#E11D48` | **Botón de Cobro y llamadas a la acción principales.** |
| `COLOR_COBRO_HOVER`       | `#BE123C` | Hover del botón de cobro. |
| `COLOR_EXITO`              | `#059669` | Verde esmeralda para estados activos y cuadres de caja. |
| `COLOR_PELIGRO`            | `#DC2626` | Rojo carmesí para eliminar ítems, alertas y mermas. |
| `COLOR_TEXTO_TITULO`       | `#0F172A` | Azul pizarra oscuro para títulos y encabezados de alta legibilidad. |
| `COLOR_TEXTO_CUERPO`       | `#1E293B` | Texto estándar de lectura. |
| `COLOR_TEXTO_MUTED`        | `#64748B` | Texto secundario, unidades de medida y marcas de agua. |
| `COLOR_BOTON_SECUNDARIO`   | `#F1F5F9` | Fondo de botones secundarios y controles de cantidad. |
| `COLOR_BOTON_SECUNDARIO_HOVER` | `#E2E8F0` | Hover de botones secundarios. |

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

---

## 6. Pantalla de Bienvenida y Autenticación (`LoginView`)

* **Fondo Fotográfico:** Fotografía ambiental de alta resolución de la heladería artesanal (`assets/login_bg.jpg`) con redimensionamiento dinámico y recorte proporcional (*cover*).
* **Filtro de Contraste:** Atenuación sutil al 72% de brillo para garantizar que los elementos de texto y la tarjeta resalten con gran elegibilidad.
* **Tarjeta de Acceso Centrada:**
  * Fondo: Carbón oscuro `#181B22` con `corner_radius = 20`.
  * Marco: Filete doble `border_width = 2` en Dorado Artesanal `#E5B869`.
  * Logotipo: `🍨 HELA-POS` en Dorado `#E5B869`.
  * Campos de Entrada: `#242832` con tipografía blanca y bordes refinados.
  * Botón de Acceso: Frambuesa Pastel `#FF5C8D` con hover `#E04876`.
