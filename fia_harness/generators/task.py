"""Generación del TASK-Fx.md de la fase activa.

Inyecta los checklists reales (seguridad, visibilidad, UI/UX) en los marcadores
`<!-- INJECT:X -->` de TASK_TEMPLATE.md según la heurística de `core.policy`.
La inyección basada en marcadores es robusta a cambios de redacción en la plantilla.
"""

import re

from fia_harness.core.console import warn
from fia_harness.core.policy import (INJECT_MARKERS, NOT_APPLICABLE_TEXT,  # noqa: F401
                                     detect_lite_mode)
from fia_harness.core.state import DEFAULT_FILES
from fia_harness.parser.markdown import extract_section, load_file


def strip_template_meta_header(template: str, template_name: str) -> str:
    """Recorta la cabecera meta de la plantilla ('# TASK_..._TEMPLATE.md — Propósito /
    Cómo usar esta plantilla'). Ese bloque documenta CÓMO RELLENAR la plantilla: si
    viaja dentro de cada TASK-Fx.md, el agente ejecutor recibe instrucciones de
    generación que no le aplican. El corte se hace en el primer encabezado '# TASK-'
    (el '_TEMPLATE' de la cabecera meta nunca coincide porque usa guion bajo)."""
    match = re.search(r"^# TASK-", template, re.MULTILINE)
    if not match:
        warn(f"La plantilla {template_name} no contiene ningún encabezado '# TASK-': "
             f"se copia íntegra, incluida su cabecera meta. Revísala a mano.")
        return template
    return template[match.start():]


def inject(template: str, marker_key: str, replacement_lines: str):
    """Sustituye el bloque <!-- INJECT:marker_key --> ... <!-- /INJECT --> completo
    por `replacement_lines`. Devuelve (texto_resultante, encontrado)."""
    marker = INJECT_MARKERS[marker_key]
    pattern = re.compile(
        rf"<!--\s*INJECT:{marker}\s*-->.*?<!--\s*/INJECT\s*-->",
        re.DOTALL,
    )
    if not pattern.search(template):
        return template, False
    safe_repl = replacement_lines.replace("\\", "\\\\")
    return pattern.sub(lambda _m: safe_repl, template, count=1), True


def build_security_block(security_content: str) -> str:
    sections = [
        ("Autenticación (AuthN)", "Autenticación"),
        ("Autorización y control de acceso a datos (AuthZ)", "Autorización"),
        ("Gestión de secretos", "Secretos"),
        ("Protección de datos", "Protección de Datos"),
        ("Seguridad de infraestructura", "Infraestructura"),
        ("Skills, MCP, conectores y agentes externos", "Skills / MCP / Conectores"),
        ("Seguridad de instrucciones y prompt injection", "Prompt Injection / Contenido Externo"),
    ]
    parts = ["#### Checklist de Seguridad Obligatorio (extraído en vivo de `SECURITY.md`):"]
    for heading, label in sections:
        block = extract_section(security_content, heading)
        parts.append(f"\n**{label}:**\n{block if block else '_(sección no encontrada en SECURITY.md)_'}")
    return "\n".join(parts)


def build_visibility_block(seo_content: str) -> str:
    sections = [
        ("Checklist técnico transversal", "Transversal"),
        ("Checklist específico SEO", "SEO"),
        ("Checklist específico AEO", "AEO"),
        ("Checklist específico GEO", "GEO"),
    ]
    parts = ["#### Checklist de Visibilidad Activo (extraído en vivo de `AEO_GEO_SEO.md`):"]
    for heading, label in sections:
        block = extract_section(seo_content, heading)
        parts.append(f"\n**{label}:**\n{block if block else '_(sección no encontrada en AEO_GEO_SEO.md)_'}")
    return "\n".join(parts)


def build_ui_ux_block(ui_content: str) -> str:
    sections = [
        ("Gate de entrada", "Gate de Entrada UX"),
        ("Reglas de exclusividad", "Reglas de Originalidad y Exclusividad (Anti-clon)"),
    ]
    parts = ["#### Requisitos de UI/UX Activos (extraídos en vivo de `UI_UX_EXCLUSIVA.md`):"]
    for heading, label in sections:
        block = extract_section(ui_content, heading)
        parts.append(f"\n**{label}:**\n{block if block else '_(sección no encontrada en UI_UX_EXCLUSIVA.md)_'}")
    return "\n".join(parts)


def _fallback_title(row: dict) -> str:
    """Cuando la tabla de fases no tiene columna de título separada (p. ej. el
    esquema Fase|Objetivo|Entregable|Depende de|Estado de la Fase 3 de
    INICIO_PROYECTO.md), usa el objetivo como título en vez del código de fase
    desnudo ('TASK-F0 — F0' no dice nada; 'TASK-F0 — BOOTSTRAP DEL REPO...' sí)."""
    if row["title"]:
        return row["title"]
    if row["objective"]:
        obj = row["objective"].split(" / ")[0].strip()
        return (obj[:70] + "…") if len(obj) > 70 else obj
    return row["phase"]


def build_task_file(project_dir, row: dict, reqs: dict, use_lite: bool) -> str:
    template_key = "template_lite" if use_lite else "template"
    template_path = project_dir / DEFAULT_FILES[template_key]
    output = strip_template_meta_header(load_file(template_path), DEFAULT_FILES[template_key])

    display_title = _fallback_title(row)

    # Reemplazos básicos de cabecera (mismos para ambas plantillas)
    output = output.replace("<N>", row["phase"])
    output = output.replace("<TÍTULO CORTO DE LA FASE O TAREA>", display_title.upper())
    output = output.replace("<TÍTULO>", display_title.upper())

    obj_text = (
        f"**Objetivo (desde PROGRESS.md):** {row['objective'] or '<pendiente de completar>'}\n"
        f"**Dependencias:** {row['dependencies']}"
    )
    output = output.replace(
        "Construir <funcionalidad> cumpliendo el criterio de aceptación definido en "
        "`SPEC.md`, sección <X>, sin romper lo ya construido en fases previas.",
        obj_text,
    )
    output = output.replace("<funcionalidad>", display_title)

    if template_key != "template":
        # La plantilla Lite no usa el sistema de marcadores <!-- INJECT --> del
        # TASK_TEMPLATE.md completo; el propio TASK_LITE_TEMPLATE.md ya remite a
        # SECURITY.md / UI_UX_EXCLUSIVA.md en su sección 5/6/8, así que aquí no
        # tocamos esas secciones. Ver aviso en el resumen final del script.
        return output

    for key in ("visibility", "security", "ui_ux"):
        applies = reqs[key]
        if applies:
            source_path = project_dir / DEFAULT_FILES[
                {"visibility": "aeo_geo_seo", "security": "security", "ui_ux": "ui_ux"}[key]
            ]
            if not source_path.exists():
                warn(f"{source_path.name} no existe: se marca '{key}' como no verificable.")
                replacement = f"No verificable: falta el archivo `{source_path.name}` en el proyecto."
            else:
                source_content = load_file(source_path)
                builder = {"visibility": build_visibility_block, "security": build_security_block,
                           "ui_ux": build_ui_ux_block}[key]
                replacement = builder(source_content)
        else:
            replacement = NOT_APPLICABLE_TEXT[key]

        output, found = inject(output, key, replacement)
        if not found:
            warn(f"No se encontró el marcador <!-- INJECT:{INJECT_MARKERS[key]} --> en "
                 f"{DEFAULT_FILES['template']}. Esa sección quedó SIN modificar — revísala a mano.")

    return output
