---
trigger: always_on
---

# Regla: Control Estético de la Interfaz Gráfica (Decisión del Usuario)

El usuario (Tech Lead del proyecto) tiene el **control total y exclusivo** sobre la parte estética de todas las interfaces de la aplicación (CustomTkinter, `src/ui/` y `main.py`).

## Qué debe consultarse SIEMPRE antes de escribir código visual

- Paleta de colores (fondos, textos, acentos, bordes).
- Colores y estados de botones (normal, hover, presionado, deshabilitado).
- Ubicación y distribución de los elementos en cada pantalla (qué va a la izquierda, derecha, arriba, abajo; grillas, columnas, paneles).
- Tamaños de botones, tarjetas y paneles; radios de esquinas; espaciados.
- Tipografías y tamaños de letra.
- Modo de apariencia (oscuro / claro / sistema), iconos e imágenes.

## Cómo proceder

1. Antes de implementar cualquier pantalla o componente visual, presentar al usuario una propuesta (descripción del layout, colores en HEX y, si ayuda, un mockup) y **esperar su aprobación explícita**.
2. No asumir ni inventar colores ni ubicaciones por cuenta propia. Si algo no fue definido, preguntar.
3. Registrar las decisiones aprobadas en `docs/ui_design_system.md` y reutilizarlas de forma consistente (tokens centralizados en el código, nunca colores sueltos).
4. Cualquier cambio estético posterior también requiere aprobación previa del usuario.

## Qué NO requiere consulta

La lógica de negocio, servicios, repositorios, pruebas, conexión entre la UI y los servicios, validaciones y manejo de errores. Esa parte la implementa el agente siguiendo la arquitectura existente.
