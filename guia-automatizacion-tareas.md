# Guía de Automatización del Harness de Tareas (`TASK-Fx.md`)

Este kit de herramientas contiene una propuesta concreta y un script ejecutable en Python (`task_generator.py`) diseñado para eliminar de raíz la fricción documental ("burocracia del harness").

## El Problema: Fricción Documental
El sistema de harness es sumamente robusto para garantizar la seguridad, el SEO y la UX. Sin embargo, tener que copiar manualmente plantillas, leer de forma cruzada el plan de fases y copiar/pegar checklists de `SECURITY.md`, `AEO_GEO_SEO.md` y `UI_UX_EXCLUSIVA.md` introduce una sobrecarga operativa considerable que puede tentar a los desarrolladores a saltarse pasos.

## La Solución: Automatización Semántica
Hemos creado un script CLI en Python 3 (`task_generator.py`) libre de dependencias externas que asume la responsabilidad de generar de forma instantánea el archivo `TASK-Fx.md` de la fase correspondiente, aplicando las siguientes reglas de automatización:

1. **Detección Automática de Estado:** Lee `PROGRESS.md` para identificar la primera fase con casilla vacía `[ ]`.
2. **Extracción de Metadatos:** Extrae el objetivo, entregable y dependencias de esa fase específica desde la tabla de progreso.
3. **Análisis Semántico de Requisitos:** Analiza el título y objetivo de la fase para detectar automáticamente si requiere:
   - **Seguridad (Fase J2):** Si el objetivo incluye base de datos, autenticación, secretos, VPS, migraciones, etc.
   - **Visibilidad (SEO/AEO/GEO - Fase H2):** Si el objetivo menciona landing, frontend, blog, contenido, etc.
   - **Diseño UI/UX (Fase H3):** Si el objetivo involucra pantallas, componentes, flujos visuales, etc.
4. **Inyección Selectiva de Checklists:**
   - Si un módulo aplica, lee los checklists reales declarados en tus archivos vivos (`SECURITY.md`, `AEO_GEO_SEO.md`, `UI_UX_EXCLUSIVA.md`) y los inyecta dinámicamente en los placeholders de la tarea.
   - Si no aplica, auto-escribe un bloque limpio indicando `"No aplica"` con el motivo exacto, reduciendo el ruido de contexto.
5. **Plantilla limpia:** recorta la cabecera meta de la plantilla ("Cómo usar esta plantilla..."), que es documentación para quien genera la tarea, no para el agente que la ejecuta. El `TASK-Fx.md` final empieza directamente en su encabezado de tarea.

---

## Cómo Ejecutar el Generador

> Comando según sistema operativo: `python` en Windows, `python3` en macOS/Linux. Los ejemplos usan `python` (Windows); en Unix sustitúyelo por `python3`.

### 1. Generar la siguiente fase pendiente (Recomendado)
El script detectará automáticamente qué fase sigue pendiente en tu `PROGRESS.md` y creará su archivo de tareas correspondiente:
```bash
python task_generator.py
```

### 2. Generar una fase específica
Si deseas forzar la creación de una tarea para una fase concreta (por ejemplo, `F3`):
```bash
python task_generator.py --phase F3
```

### 3. Forzar el Modo Lite (`TASK-QUICK.md`)
Si el proyecto está configurado para desarrollo rápido o deseas forzar la plantilla simplificada:
```bash
python task_generator.py --lite
```

---

## Control de estado y aprobaciones (nuevo en v2)

El script ya no solo genera tareas: también es el guardian del estado del proyecto.

| Comando | Qué hace |
|---|---|
| `python task_generator.py --sync` | Compila `PROGRESS.md` en `progress.json` y lo valida. Si el estado viola una regla, **no escribe nada** (fail-closed). |
| `python task_generator.py --check` | Valida el estado sin modificar nada. Es el comando que ejecuta el CI generado por `bootstrap.py` en cada push/PR. |
| `python task_generator.py --approval "acción" --phase F2 --ref "chat/PR"` | Registra una aprobación humana sellada (`APPROVAL-NNN`) en `DECISIONS.md`. |

Qué valida `--check` (cada regla es una Regla de Oro hecha mecánica):

- `progress.json` sincronizado con `PROGRESS.md` (una edición manual sin compilar rompe el CI hasta que hagas `--sync`).
- Los estados de fase pertenecen al enum válido y no hay identificadores duplicados.
- Toda dependencia declarada existe y **ninguna fase cerrada tiene dependencias abiertas**.
- Toda fase cerrada tiene su **checkpoint de contexto** en `PROGRESS.md`.
- Toda fase F cerrada tiene su **`TASK-F<N>.md`** en la raíz.
- Toda `APPROVAL-NNN` citada en una `TASK-*.md` existe en `DECISIONS.md`, y toda entrada registrada incluye fecha, `Acción:` y `Aprobado por:`.

---

## Ejemplo Práctico de Comportamiento

* **Ejemplo A (F1 - Base de Datos):** Al analizar `"Modelo de datos + migraciones"`, el script detecta que requiere **Seguridad** pero no requiere **Visibilidad** ni **UX**. Inyecta el checklist de RLS y políticas desde tu `SECURITY.md` y marca las fases H2 y H3 como "No aplica".
* **Ejemplo B (F3 - Landing Page):** Al analizar `"Frontend public landing"`, detecta que requiere **Visibilidad** y **UI/UX**, pero no **Seguridad**. Inyecta los checklists de SEO/AEO/GEO de `AEO_GEO_SEO.md` y las directrices anti-clon de `UI_UX_EXCLUSIVA.md`, y marca la Fase J2 como "No aplica".

---

## Archivos Entregados en tu Panel Studio
1. `task_generator.py`: El script de automatización completo y documentado, listo para ser copiado a la raíz de tu repositorio.
2. `guia-automatizacion-tareas.md`: Esta guía explicativa que resume las ventajas, el flujo de trabajo y la ejecución del script.
3. `tests/test_harness.py`: Tests automatizados de los parsers y del ciclo completo (ver README.md, sección Verificación).
