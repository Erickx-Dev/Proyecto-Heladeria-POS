# Manual de Gobernanza, Instrucciones y Reglas de Trabajo para Agentes de IA

> **Documento:** `docs/agents.md`  
> **Versión:** 1.0 (Línea Base Oficial)  
> **Destinatarios:** Antigravity 2.0 y cualquier Agente de Inteligencia Artificial o Asistente Autónomo de Código que interactúe en este repositorio.  
> **Administrador del Repositorio y Tech Lead:** Erickson Sojo  
> **Alcance:** Sistema de Gestión Comercial, Control de Inventario, Caja y Punto de Venta (POS) para Heladería.

---

## 1. Contexto del Dominio y Límites Operativos del Sistema

El software en desarrollo es una aplicación de escritorio local (*Desktop Standalone*) diseñada para sistematizar las operaciones diarias de una heladería de mostrador. El agente debe interiorizar los siguientes límites operativos y requisitos del entorno:

### 1.1. Dominio de Negocio
- **Punto de Venta Rápido (POS):** Facturación en mostrador con selección ágil de categorías, sabores de helado, adición de toppings y cálculo automático de subtotales.
- **Cobro Multimodal:** Procesamiento de pagos en efectivo (cálculo de cambio/devuelta exacta) y transferencias electrónicas (Nequi, Daviplata, QR bancario).
- **Gestión de Turnos y Caja:** Apertura con fondo base obligatorio, registro de egresos de caja menor y arqueo conciliado con cálculo automático de faltantes o sobrantes.
- **Control Integral de Insumos:** Descuento en tiempo real de inventario perecedero tras cada venta y disparo de alertas visuales ante stock mínimo.
- **Control de Mermas:** Registro justificado y cuantitativo de pérdidas (descongelamiento, derrames, roturas, caducidad) sin impacto dinerario.
- **Auditoría y Trazabilidad:** Bitácora inalterable (`AuditoriaLog`) con sello de tiempo para eventos críticos y sensibles.

### 1.2. Restricciones de Hardware Modesto (RNF01) y Entorno Operativo
- **Consumo de Memoria:** El sistema en ejecución **no debe superar en ningún momento los 200 MB de memoria RAM**.
- **Latencia de Respuesta:** Las transacciones locales, consultas de catálogo y cálculos deben responder en **menos de 0.3 segundos**.
- **Autonomía 100% Offline (RNF04):** Cero dependencias de servicios en la nube, APIs remotas o conectividad a internet. Todo se ejecuta y almacena localmente.
- **Prohibición de Frameworks Pesados:** Queda terminantemente descartado el uso de Electron, WebView2 o navegadores embebidos que degraden equipos sencillos.

### 1.3. Stack Tecnológico Aprobado
- **Lenguaje:** Python 3.10+ (usando tipado estático `typing`).
- **Interfaz Gráfica (GUI):** CustomTkinter (widgets modulares, ligeros y de alto contraste).
- **Motor de Base de Datos:** SQLite3 (embebido nativamente en la biblioteca estándar de Python, archivo canónico en `data/heladeria.db`).

---

## 2. Gobernanza y Subordinación a la Documentación Técnica

El agente de IA no opera de forma anárquica ni toma decisiones unilaterales. **Tiene la obligación explícita de consultar y subordinarse a los siguientes documentos de ingeniería antes de escribir código:**

1. **[`docs/git_protocol.md`](file:///c:/Users/ASUS%20VIVO/Documents/Heladeria%20POO/docs/git_protocol.md) (Protocolo Estricto de Git):**
   - **Regla Inquebrantable:** El agente tiene **estrictamente prohibido** ejecutar `git add`, `git commit`, `git checkout/switch`, `git merge` o `git push` de manera autónoma.
   - Debe operar exclusivamente en ramas dedicadas (`feature/<nombre>`, `fix/<nombre>`). Jamás tocar `main` o `develop` directamente.
   - Todo commit debe formularse en español técnico bajo **Conventional Commits** (`feat(...)`, `fix(...)`, `refactor(...)`, etc.) y presentarse en el chat solicitando confirmación textual explícita antes de ejecutar.
   - Prohibición total de comandos destructivos (`push --force`, `reset --hard`, `clean -fd`).

2. **Gestión de Tareas y Prioridades en GitHub Projects (Sin Roadmap Local):**
   - **Fuente Única de Verdad para Tareas y Prioridades:** No existe un archivo `roadmap.md` local. El backlog, las prioridades (Ola 1 a Ola 5) y el estado de los requisitos funcionales se gestionan exclusivamente a través de **GitHub Projects** y los **Issues** del repositorio.
   - **Flujo de Tareas:** Al iniciar una funcionalidad, el desarrollador o agente toma el requerimiento asignado desde la columna "Todo" del tablero en GitHub Projects, lo mueve a "In Progress" y crea la rama correspondiente (`feature/...`). El desarrollo respeta las dependencias por capas (Persistencia -> Dominio -> Repositorios -> Servicios -> UI) sin adelantar componentes no consolidados.
   - **Cierre de Tareas:** Al completar la implementación, el Pull Request debe hacer referencia al requerimiento (ej. `Closes #1` o asociando el Issue) para que el tablero se actualice de forma trazable.

3. **[`docs/architecture.md`](file:///c:/Users/ASUS%20VIVO/Documents/Heladeria%20POO/docs/architecture.md) (Diseño de Capas y Flujos):**
   - Define las responsabilidades y contratos entre módulos. El flujo de invocación debe ser estrictamente unidireccional:
     $$\text{UI (Views/Components)} \longrightarrow \text{Services (Casos de Uso)} \longrightarrow \text{Repositories (SQL)} \longrightarrow \text{Database (SQLite3)}$$

4. **[`docs/templates/session_summary_template.md`](file:///c:/Users/ASUS%20VIVO/Documents/Heladeria%20POO/docs/templates/session_summary_template.md) (Cierre de Jornadas):**
   - Al culminar cada sesión de trabajo, el agente debe generar obligatoriamente la bitácora histórica en `docs/sessions/YYYY-MM-DD_sesion_XX.md`, detallando el trabajo realizado a nivel función por función con sus tipos y firmas.

---

## 3. Reglas Inquebrantables de Arquitectura y Código (SOLID)

Para asegurar la mantenibilidad y estabilidad del sistema, el agente debe verificar en cada cambio el cumplimiento estricto de las siguientes reglas de arquitectura:

### 3.1. Cero SQL en la Capa de Interfaz Gráfica (UI)
- Los archivos en `src/ui/views/` y `src/ui/components/` **tienen estrictamente prohibido importar `sqlite3`, ejecutar queries SQL o instanciar conexiones a la base de datos**.
- Las vistas son pasivas: únicamente capturan eventos del usuario, validan formatos básicos de formulario y delegan la acción a la capa `src/services/`.
- Cualquier lógica de negocio o consulta SQL detectada en la UI será considerada una violación crítica de arquitectura.

### 3.2. Aislamiento y Orquestación en la Capa de Servicios
- La capa `src/services/` encapsula los casos de uso (autenticación, cobro de ventas, arqueo de caja, cálculo de reportes financieros).
- No ejecuta SQL directo: coordina y consume uno o más repositorios (`src/repositories/`).
- Maneja excepciones de negocio personalizadas importadas desde `src/core/exceptions.py` (ej. `StockInsuficienteError`, `CajaCerradaError`).

### 3.3. Transacciones Atómicas (ACID) en Repositorios
- Toda operación de datos compuesta que involucre más de una inserción/actualización (ejemplo: registrar una venta + insertar sus $N$ detalles + descontar insumos del inventario + registrar log de auditoría) **debe ejecutarse bajo una única transacción atómica** utilizando el context manager `get_db_transaction()` de `database/connection.py`.
- Si ocurre una excepción en cualquier punto de la operación, el context manager disparará un `rollback` inmediato, previniendo datos huérfanos o inconsistencias contables ante cortes eléctricos.

### 3.4. Seguridad Criptográfica
- **Cero contraseñas en texto plano:** Todas las credenciales deben procesarse exclusivamente a través de funciones hash seguras (SHA-256) centralizadas en `src/core/security.py`.
- Las consultas SQL deben utilizar parámetros enlazados mediante tuplas (`?`), **prohibiendo estrictamente la interpolación de cadenas (`f"SELECT... {variable}"`)** para blindar el sistema contra inyecciones SQL.

### 3.5. Gestión de Memoria y Ciclo de Vida de Widgets
- Para garantizar el consumo < 200 MB en CustomTkinter:
  - Cuando el usuario navegue entre pantallas, la vista anterior debe destruirse o desvincularse explícitamente (`frame.destroy()`).
  - No mantener referencias circulares ni listas acumulativas de widgets en memoria.
  - Las conexiones de base de datos deben cerrarse siempre en bloques `finally` (garantizado por los context managers de `database/connection.py`).

### 3.6. Estándares y Convenciones de Código
- **Tipado Estático Obligatorio:** Todo método, función y parámetro debe declarar tipos mediante el módulo `typing` (`Optional`, `Union`, `List`, `Dict`, `Tuple`, `Generator`).
- **Modelos de Dominio:** Las entidades puras en `src/domain/` deben implementarse mediante `@dataclass` inmutables o limpias, sin dependencias de librerías externas.
- **Idioma:** Nombres de variables, funciones, tablas y comentarios técnicos redactados en **español**, manteniendo coherencia con el documento IEEE 830 del cliente.

---

## 4. Protocolo de Interacción con el Desarrollador Humano

El agente de IA colabora bajo la modalidad de pair-programming con el equipo humano, respetando las siguientes directrices de interacción:

1. **Autoridad Centralizada:**
   - **Erickson Sojo** es el administrador único, arquitecto y líder técnico del repositorio.
   - Cualquier decisión que modifique el esquema de la base de datos, agregue dependencias o altere flujos de arquitectura debe ser consultada y aprobada por él.

2. **Resolución de Ambigüedades:**
   - Si una regla de negocio presenta ambigüedades (ej. tratamiento de redondeos monetarios, fórmulas de arqueo o umbrales de stock), el agente **no debe asumir comportamientos por su cuenta**; formulará la pregunta de forma concisa y estructurada al usuario.

3. **Protocolo de Cierre de Tarea / Ola:**
   Al finalizar la implementación de un requerimiento funcional o tarea técnica, el agente debe seguir obligatoriamente este flujo:
   1. Ejecutar las pruebas automatizadas (`unittest`) y verificar que pasen al 100%.
   2. Presentar la **Solicitud de Confirmación Git** en el chat conforme a `docs/git_protocol.md` (rama actual, archivos staged, conventional commit).
   3. Una vez aprobado y ejecutado el commit, documentar la bitácora correspondiente en `docs/sessions/` basada en `docs/templates/session_summary_template.md`.
   4. Notificar a Erickson Sojo qué requerimiento IEEE 830 quedó cubierto para proceder con la apertura y revisión del Pull Request.
