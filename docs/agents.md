# Manual de Gobernanza, Instrucciones y Reglas de Trabajo para Agentes de IA

> **Documento Canónico:** `docs/agents.md`  
> **Versión:** 2.0 (Línea Base Reestructurada)  
> **Destinatarios:** Antigravity 2.0 y cualquier Agente de Inteligencia Artificial o Asistente Autónomo de Código que interactúe en este repositorio.  
> **Administrador del Repositorio y Tech Lead:** Erickson Sojo  
> **Alcance:** Sistema de Gestión Comercial, Control de Inventario, Caja y Punto de Venta (POS) para Heladería.

---

## 1. Principio Fundamental del Agente Conservador

Antigravity y cualquier asistente de IA en este repositorio deben operar bajo el **principio de agente conservador**. El agente no opera de forma autónoma no supervisada ni toma decisiones unilaterales sobre el diseño, el comportamiento o los datos del sistema.

### 1.1. Filosofía de Trabajo
El agente prioriza la estabilidad, la integridad documental y la trazabilidad del código. El flujo de trabajo inalterable es:

```text
Entender
   ↓
Verificar
   ↓
Proponer
   ↓
Preguntar ante ambigüedad
   ↓
Implementar únicamente lo autorizado
   ↓
Probar (100% tests aprobados)
   ↓
Solicitar confirmación explícita para commit
   ↓
Sincronizar con main antes del Pull Request
   ↓
Pull Request
```

**Queda terminantemente prohibido el patrón:**
$$\text{Asumir} \longrightarrow \text{Modificar} \longrightarrow \text{Justificar después}$$

### 1.2. Matriz de Autonomía vs. Autorización Obligatoria

| Acciones Autónomas Permitidas | Acciones que Exigen Autorización Previa de Erickson Sojo |
| :--- | :--- |
| Inspeccionar y analizar código y documentación existente. | Tomar o modificar decisiones de arquitectura. |
| Ejecutar comandos de solo lectura (`git status`, `git diff`, etc.). | Modificar el esquema de base de datos (`schema.sql` o migraciones). |
| Ejecutar suites de pruebas locales (`unittest`). | Modificar o interpretar arbitrariamente reglas de negocio. |
| Diagnosticar errores técnicos y advertencias de linting. | Alterar políticas criptográficas o algoritmos de seguridad. |
| Proponer soluciones técnicas estructuradas y explicar problemas. | Realizar operaciones destructivas en Git o en el sistema de archivos. |
| Implementar tareas puntuales previamente aprobadas. | **Ejecutar cualquier `git commit`** (sin excepción alguna). |

---

## 2. Contexto del Dominio y Restricciones Operativas

El software es una aplicación de escritorio local (*Desktop Standalone*) diseñada para optimizar las operaciones diarias de una heladería de mostrador.

### 2.1. Dominio de Negocio
- **Punto de Venta Rápido (POS):** Facturación ágil en mostrador con selección por categorías, sabores, adición de toppings y cálculo automático de subtotales y totales.
- **Cobro Multimodal:** Procesamiento de pagos en efectivo (con cálculo exacto de cambio/devuelta) y transferencias electrónicas (Nequi, Daviplata, QR bancario).
- **Gestión de Turnos y Caja:** Apertura obligatoria con fondo base en efectivo, registro de egresos de caja menor y arqueo conciliado con cálculo automático de faltantes o sobrantes.
- **Control Integral de Insumos:** Descuento en tiempo real de inventario tras cada venta registrada y alertas visuales automáticas ante stock mínimo.
- **Control de Mermas:** Registro justificado y cuantitativo de pérdidas (descongelamiento, derrames, roturas, caducidad) sin afectación dineraria.
- **Auditoría y Trazabilidad:** Bitácora cronológica inalterable (`AuditoriaLog`) con sello de tiempo para eventos críticos del sistema.

### 2.2. Restricciones de Hardware Modesto (RNF01) y Entorno Operativo
- **Consumo de Memoria:** El sistema en ejecución **no debe superar en ningún momento los 200 MB de memoria RAM**.
- **Latencia de Respuesta:** Las transacciones locales, consultas de catálogo y cálculos deben ejecutarse en **menos de 0.3 segundos**.
- **Autonomía 100% Offline (RNF04):** Cero dependencias de servicios en la nube, APIs remotas o conectividad a internet. Toda la operativa y persistencia es estrictamente local.
- **Prohibición de Frameworks Pesados:** Queda terminantemente descartado el uso de Electron, WebView2 o navegadores embebidos que degraden el rendimiento en equipos sencillos.

### 2.3. Stack Tecnológico Aprobado
- **Lenguaje:** Python 3.10+ con tipado estático riguroso (`typing`).
- **Interfaz Gráfica (GUI):** CustomTkinter (widgets modulares, ligeros y de alto contraste).
- **Motor de Base de Datos:** SQLite3 (embebido nativamente en la biblioteca estándar de Python). Archivo canónico en `data/heladeria.db`.

---

## 3. Arquitectura Oficial y Reglas de Capas

El sistema implementa una arquitectura en capas estrictamente desacoplada. Toda nueva implementación o refactorización debe subordinarse a este diseño:

### 3.1. Flujo Unidireccional de Invocación

$$\text{UI (Views / Components)} \longrightarrow \text{Services (Casos de Uso)} \longrightarrow \text{Repositories (Persistencia SQL)} \longrightarrow \text{Database (SQLite3)}$$

### 3.2. Estructura Conceptual del Proyecto

```text
src/
├── core/              # Utilidades transversales, excepciones de negocio y seguridad
├── domain/            # Entidades puras del dominio de negocio (@dataclass)
├── repositories/      # Acceso a datos, consultas SQL parametrizadas y transacciones
├── services/          # Orquestación de lógica de negocio y casos de uso
└── ui/                # Interfaz gráfica de usuario con CustomTkinter
    ├── components/    # Widgets y fragmentos visuales reutilizables
    └── views/         # Pantallas y vistas completas

database/              # Infraestructura de datos (connection.py, schema.sql, migrations.py)
data/                  # Directorio del archivo canónico SQLite (heladeria.db)
docs/                  # Documentación técnica, gobernanza y bitácoras de sesión
tests/                 # Suite de pruebas automatizadas unitarias y de integración
```

### 3.3. Reglas de Aislamiento por Capa
1. **Cero SQL en la Capa UI:**
   - Los módulos en `src/ui/views/` y `src/ui/components/` **tienen estrictamente prohibido importar `sqlite3`, ejecutar queries SQL o instanciar conexiones a la base de datos**.
   - La UI es pasiva: captura eventos del usuario, valida formatos de entrada y delega la ejecución a `src/services/`.
2. **Aislamiento y Orquestación en Services:**
   - La capa `src/services/` encapsula los casos de uso.
   - No ejecuta consultas SQL directas: coordina y consume uno o más repositorios (`src/repositories/`).
   - Maneja y propaga excepciones de negocio personalizadas importadas desde `src/core/exceptions.py`.
3. **Transacciones Atómicas (ACID) en Repositorios:**
   - Toda operación de datos compuesta que involucre más de una inserción o actualización (ejemplo: registrar una venta + registrar detalles + descontar insumos + asentar log de auditoría) **debe ejecutarse bajo una única transacción atómica** mediante el context manager `get_db_transaction()` de `database/connection.py`.
   - Ante cualquier excepción, el context manager dispara un `rollback` inmediato, previniendo inconsistencias contables o datos huérfanos.

---

## 4. Estándares y Convenciones de Código

1. **Tipado Estático Obligatorio:**
   - Toda función, método y parámetro debe declarar tipos utilizando el módulo `typing` (`Optional`, `Union`, `List`, `Dict`, `Tuple`, `Generator`, etc.).
2. **Entidades de Dominio Puras:**
   - Los modelos en `src/domain/` deben implementarse mediante `@dataclass` limpias e inmutables, libres de dependencias de infraestructura, UI o librerías externas.
3. **Idioma:**
   - Nombres de variables, clases, métodos, funciones, tablas de base de datos y comentarios técnicos redactados en **español**, manteniendo coherencia con la especificación del sistema.
4. **Prevención de Inyección SQL:**
   - Las consultas SQL deben utilizar siempre parámetros enlazados mediante tuplas (`?`). **Queda estrictamente prohibida la interpolación de cadenas (`f"SELECT... {var}"`)**.
5. **Gestión de Memoria en CustomTkinter:**
   - Para mantener el consumo por debajo de 200 MB de RAM:
     - Destruir o desvincular explícitamente vistas anteriores al navegar (`frame.destroy()`).
     - No retener referencias circulares ni listas acumulativas de widgets.
     - Las conexiones de base de datos deben liberarse y cerrarse siempre en bloques `finally` (garantizado por los context managers de `database/connection.py`).

---

## 5. Protocolo Estricto de Git

El repositorio se rige por un esquema de gobernanza centralizada y protección absoluta de ramas base:

### 5.1. Blindaje de Ramas Base ("Branch First, Code Second")
- **Queda estrictamente prohibido crear, modificar o eliminar archivos estando posicionado sobre `main` o `develop`**.
- **Paso Cero Obligatorio:** Antes de invocar cualquier herramienta de edición o creación de archivos en disco, el agente debe verificar la rama activa:
  ```powershell
  git branch --show-current
  ```
- Si la rama detectada es `main` o `develop`, el agente no debe alterar ningún archivo; debe conmutar de inmediato a una sub-rama de trabajo dedicada:
  ```powershell
  git switch -c <tipo>/<nombre-descriptivo>
  ```

### 5.2. Convención de Nombres de Ramas
Las ramas deben nombrarse en minúsculas y `kebab-case` bajo los siguientes prefijos normativos:
- `feature/<nombre>`: Nuevas funcionalidades o requerimientos de negocio.
- `fix/<nombre>`: Corrección de fallos o defectos.
- `refactor/<nombre>`: Reestructuración de código sin alterar comportamiento observable.
- `docs/<nombre>`: Documentación técnica, bitácoras y gobernanza.
- `test/<nombre>`: Adición o mantenimiento de pruebas automatizadas.
- `chore/<nombre>`: Mantenimiento general, configuración o dependencias.

### 5.3. Conventional Commits en Español
Los commits deben formularse en modo imperativo y redactarse en español técnico:
$$\text{<tipo>}(\text{<alcance>}):\ \text{<descripción breve>}$$
Tipos válidos: `feat`, `fix`, `docs`, `refactor`, `test`, `style`, `chore`.

### 5.4. Regla Crítica: Confirmación Obligatoria Previa a Cualquier Commit
**ANTES DE EJECUTAR CUALQUIER `git commit`**, el agente debe solicitar obligatoriamente confirmación textual explícita en el chat, presentando el siguiente reporte de pre-autorización:

```markdown
### 📋 Solicitud de Confirmación de Operación Git
1. **Rama Actual:** `<nombre-rama-actual>`
2. **Archivos a Agregar (git add):**
   - `ruta/al/archivo1.py`
   *(Prohibido usar `git add .` o agregar bases de datos locales, venv o cachés)*
3. **Mensaje de Commit Propuesto:**
   `tipo(alcance): descripción breve en español`
4. **Comando Exacto:**
   `git add <archivos> && git commit -m "..."`

⚠️ Esperando confirmación explícita de Erickson Sojo para proceder.
```

> **Regla de Bloqueo:** El agente NO ejecutará el comando de commit hasta recibir la confirmación textual ("Acepto", "Adelante", "Confirmado"). Nunca debe asumir autorización.

### 5.5. Prohibición Absoluta de Comandos Destructivos
Bajo ninguna circunstancia el agente ejecutará ni propondrá:
```powershell
git push --force
git reset --hard
git clean -fd
git branch -D
git merge (directo sobre main o develop)
```
Si se presentan divergencias o conflictos, el agente se detendrá, reportará el estado con `git status` / `git diff` y esperará instrucciones de resolución.

---

## 6. Planificación de Tareas y Flujo de Pull Requests

### 6.1. Fuente Canónica de Verdad: Roadmap Local (`docs/roadmap.md`)
El archivo [`docs/roadmap.md`](docs/roadmap.md) constituye la **fuente canónica oficial de verdad** para la planificación, priorización, dependencias por Olas (Ola 1 a Ola 6) y estado de los 15 Requerimientos Funcionales del proyecto.
- Las tareas no se gestionan en tableros remotos de GitHub, sino directamente en el repositorio mediante el roadmap local.
- Al tomar una tarea, el agente o desarrollador consulta `docs/roadmap.md`, crea la rama correspondiente (`<tipo>/<nombre>`) y actualiza el estado correspondiente al culminar (`[x]`).
- El ciclo de vida de una tarea sigue:
  $$\text{Planificación en Roadmap} \longrightarrow \text{Creación de Rama} \longrightarrow \text{Implementación} \longrightarrow \text{Testing (100%)} \longrightarrow \text{Commit Autorizado} \longrightarrow \text{Sincronización con main} \longrightarrow \text{Pull Request}$$

### 6.2. Checklist Secuencial Obligatorio Previo a Pull Request
Antes de solicitar, abrir o actualizar un Pull Request, el agente debe seguir estrictamente estos pasos:
1. **Verificar estado de la rama:** Confirmar que no queden cambios sin asentar mediante `git status`.
2. **Obtener la versión más reciente de `main`:** Ejecutar `git fetch origin main`.
3. **Sincronizar la rama de trabajo con `main`:** Integrar las actualizaciones de `main` en la sub-rama local para detectar tempranamente cualquier divergencia.
4. **Resolver conflictos:** Si se detectan conflictos de fusión, detenerse y presentarlos para resolución guiada; jamás sobrescribir historial.
5. **Re-ejecutar la suite completa de pruebas:** Ejecutar `python -m unittest discover -s tests`.
6. **Verificar ausencia de errores:** Asegurar que el 100% de las pruebas aprueben limpiamente.
7. **Publicar la rama remota:** Disparar `git push origin <tipo>/<nombre>`.
8. **Vincular el Pull Request:** Abrir el Pull Request referenciando la tarea o Requisito Funcional correspondiente del roadmap (ej. `RF01 - Autenticación`).

---

## 7. Pruebas Automatizadas (Testing)

- **Framework Oficial:** Módulo estándar `unittest` de Python.
- **Comando Canónico:**
  ```powershell
  python -m unittest discover -s tests
  ```
- **Criterio de Aceptación:** Todas las pruebas deben pasar al 100% antes de considerar una tarea completada.
- **Integridad:** Si una prueba falla, la tarea no está terminada. No se permite omitir pruebas ni relajar validaciones para forzar aprobaciones.

---

## 8. Seguridad y Persistencia

### 8.1. Base de Datos Oficial
- Motor: SQLite3 local.
- Archivo canónico: `data/heladeria.db`.
- Cualquier modificación a la estructura o esquema de datos requiere autorización previa y debe formularse en `database/schema.sql` y las migraciones correspondientes.

### 8.2. Hashing de Contraseñas
- **Cero contraseñas en texto plano.**
- **Algoritmo Oficial:** Se ratifica **`bcrypt`** como estándar criptográfico del proyecto.
  - La columna `password_hash` de la tabla `Usuario` cuenta con la restricción `CHECK (length(password_hash) = 60)`.
  - Las credenciales deben procesarse centralizadamente en `src/core/security.py`.
  - *(Nota técnica: La mención preliminar a SHA-256 en borradores iniciales queda formalmente sustituida por `bcrypt` para garantizar protección industrial contra ataques de fuerza bruta y coherencia con el esquema de base de datos y la suite de pruebas).*

### 8.3. Auditoría de Eventos Sensibles
- La tabla `AuditoriaLog` almacena de forma cronológica inalterable los eventos críticos (aperturas/cierres de turno, inserción de gastos, registros de mermas, anulaciones y cambios de configuración) con fecha, hora, usuario y detalle de la operación.

---

## 9. Reglas de Negocio y Prohibición de Asunciones

El agente **no debe asumir comportamientos por su cuenta** ante ambigüedades en las reglas del negocio. Ante cualquier duda o vacío de especificación, debe **detenerse y formular la pregunta estructurada al usuario**.

Dominios especialmente sensibles a supervisión:
1. **Punto de Venta:** Fórmulas de cálculo de subtotal, descuentos y cobro multimodal.
2. **Caja y Turnos:** Obligatoriedad de base de apertura, cálculo de sobrantes/faltantes en arqueo y registro de gastos menores.
3. **Inventario y Suministros:** Fórmulas de descuento de insumos por venta y umbrales de stock mínimo.
4. **Mermas:** Justificación requerida y descarte físico de existencias sin alteración monetaria en caja.
5. **Usuarios y Permisos:** Restricción estricta de accesos entre roles (Administrador vs. Empleado).
6. **Reportes Financieros:** Períodos de consolidación (diario, semanal, mensual) y cálculo de ganancias netas.

---

## 10. Matriz Oficial de Requerimientos Funcionales (IEEE 830 V2)

Para asegurar la trazabilidad con el roadmap técnico (`docs/roadmap.md`) y las bitácoras de sesión, el sistema se estructura en torno a los 15 Requerimientos Funcionales oficiales:

| Código | Requerimiento Funcional | Módulo Asociado |
| :--- | :--- | :--- |
| **RF01** | Autenticación de Usuarios y Control de Acceso (Login) | `src/services/auth_service.py` / `Usuario` |
| **RF02** | Apertura de Turno con Monto Inicial de Caja | `src/services/cash_service.py` / `Caja` |
| **RF03** | Punto de Venta (POS) y Registro Rápido de Comandas | `src/ui/views/pos_view.py` / `Venta` |
| **RF04** | Flexibilidad en Pedidos y Cobro Multimodal | `src/services/pos_service.py` / `Venta` |
| **RF05** | Generación y Registro de Detalle de Venta | `src/repositories/sale_repository.py` / `DetalleVenta` |
| **RF06** | Gestión del Catálogo de Productos y Categorías (CRUD) | `src/services/catalog_service.py` / `Producto` |
| **RF07** | Control Integral de Insumos y Materias Primas | `src/repositories/supply_repository.py` / `Insumo` |
| **RF08** | Descuento Automático de Inventario y Alertas de Stock Mínimo | `src/services/inventory_service.py` / `Insumo` |
| **RF09** | Registro y Cuantificación de Mermas | `src/services/loss_service.py` / `Merma` |
| **RF10** | Control de Gastos Operativos de Caja Menor | `src/services/expense_service.py` / `Gasto` |
| **RF11** | Cierre de Turno y Arqueo Conciliado de Caja | `src/services/cash_service.py` / `Caja` |
| **RF12** | Reportes Periódicos y Estadísticas de Ganancias Netas | `src/services/report_service.py` / Consolidación |
| **RF13** | Administración de Usuarios y Asignación de Roles | `src/services/user_service.py` / `Usuario` |
| **RF14** | Auditoría, Trazabilidad e Historial de Movimientos (Logs) | `src/services/audit_service.py` / `AuditoriaLog` |
| **RF15** | Mantenimiento y Respaldo Local del Archivo SQLite | `database/backup.py` / `data/heladeria.db` |

---

## 11. Gestión de Sesiones y Documentación de Cierre

1. **Registro Histórico Obligatorio:**  
   Al culminar cada jornada técnica y tras haberse ejecutado el commit autorizado, el agente debe generar la bitácora formal en:
   `docs/sessions/YYYY-MM-DD_sesion_XX.md`
2. **Plantilla Oficial:**  
   La bitácora se redacta basándose estrictamente en la plantilla canónica `docs/templates/session_summary_template.md`.
3. **Nivel de Detalle Quirúrgico:**  
   Se deben detallar todos los módulos, clases y funciones creadas o modificadas, indicando parámetros, tipos de datos (`typing`) y propósito funcional.
4. **Veracidad Absoluta:**  
   Prohibido inventar tareas, archivos o resultados. El registro debe reflejar fielmente el estado real del repositorio.
5. **Portabilidad de Enlaces:**  
   Todos los enlaces y referencias a documentos dentro del repositorio deben emplear rutas relativas (ej. `docs/git_protocol.md`), **prohibiendo expresamente rutas absolutas dependientes de una computadora (`file:///C:/Users/...`)**.
