"""Parsing robusto de Markdown: tablas de fases, secciones y checkpoints.

Todo el parseo tolera negrita/código (`strip_md`) y detecta columnas por cabecera,
nunca por posición: es la base sobre la que `core.state` compila el estado.
"""

import re
from pathlib import Path

from fia_harness.core.console import fail


def strip_md(text: str) -> str:
    """Quita marcado Markdown básico (negrita, cursiva, código) para poder comparar
    texto de forma robusta, independientemente de cómo esté formateado el original."""
    text = re.sub(r"[`*_]", "", text)
    return text.strip()


def load_file(path: Path, required: bool = True) -> str:
    if not path.exists():
        if required:
            fail(f"No se encontró el archivo obligatorio: {path.name}")
        return ""
    return path.read_text(encoding="utf-8")


def _is_separator_row(line: str) -> bool:
    inner = line.strip().strip("|")
    return bool(inner) and set(inner.replace(" ", "").replace(":", "")) <= {"-"}


def _split_table_blocks(content: str):
    """Divide el documento en bloques de líneas consecutivas que empiezan por '|'.
    Permite que PROGRESS.md tenga varias tablas (p. ej. la de fases M0-M3 del
    proceso y, más abajo, la de fases F0-Fn de ejecución) sin que una tabla
    contamine el mapeo de columnas de la otra."""
    blocks, current = [], []
    for line in content.split("\n"):
        if line.strip().startswith("|"):
            current.append(line)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def parse_progress_table(progress_content: str):
    """Extrae todas las filas de fase (`F<N>` o `M<N>`) de todas las tablas
    presentes en PROGRESS.md, detectando columnas por cabecera en cada tabla por
    separado. Tolera negrita/código y columnas Objetivo/Entregable separadas o
    combinadas en una sola celda."""
    rows = []
    for block in _split_table_blocks(progress_content):
        if len(block) < 2:
            continue
        header_cells = [strip_md(c).lower() for c in block[0].strip().strip("|").split("|")]

        def find_col(*keywords, _headers=header_cells):
            for i, h in enumerate(_headers):
                if any(k in h for k in keywords):
                    return i
            return None

        col = {
            "phase": find_col("fase"),
            "title": find_col("tarea", "hito", "titulo", "título"),
            "status": find_col("estado"),
            "objective": find_col("objetivo"),
            "deliverable": find_col("entregable"),
            "deps": find_col("depend"),
        }
        if col["phase"] is None:
            continue  # este bloque de '|' no es una tabla de fases (p. ej. otra tabla del documento)
        if col["objective"] is not None and col["objective"] == col["deliverable"]:
            col["deliverable"] = None  # misma celda combinada ("Entregable / Objetivo"): no duplicar

        for line in block[1:]:
            if _is_separator_row(line):
                continue
            raw = [c.strip() for c in line.strip().strip("|").split("|")]
            clean = [strip_md(c) for c in raw]
            if col["phase"] >= len(clean):
                continue
            phase_code = clean[col["phase"]]
            if not re.fullmatch(r"[A-Za-z]+\d+", phase_code):
                continue  # fila de cabecera repetida, separador atípico, etc. — se ignora

            def get(colname, cells):
                idx = col.get(colname)
                return cells[idx] if idx is not None and idx < len(cells) else ""

            objective = " / ".join(x for x in (get("objective", clean), get("deliverable", clean)) if x)
            rows.append({
                "phase": phase_code,
                "title": get("title", clean),
                "status_raw": get("status", raw),
                "objective": objective,
                "dependencies": get("deps", clean) or "Ninguna",
            })
    return rows


def is_row_done(row: dict) -> bool:
    return bool(re.search(r"\[\s*[xX]\s*\]", row["status_raw"]))


def detect_next_phase(rows):
    """Solo se auto-detectan fases de EJECUCIÓN (`F<N>`). Las fases de proceso
    (`M<N>`: lectura de PRD, entrevista, SPEC.md, plan de fases) son pasos de
    descubrimiento/documentación de INICIO_PROYECTO.md, no tareas de código —
    generarles un TASK-Mx.md desde TASK_TEMPLATE.md no tendría sentido."""
    for row in rows:
        if re.fullmatch(r"F\d+", row["phase"]) and not is_row_done(row):
            return row["phase"]
    return None


def get_phase_row(rows, phase: str):
    for row in rows:
        if row["phase"] == phase:
            return row
    return None


def extract_section(file_content: str, section_title: str) -> str:
    """Devuelve el contenido íntegro (tablas incluidas) bajo el primer encabezado que
    contenga `section_title`, hasta el siguiente encabezado de igual o mayor nivel.
    A diferencia de un filtro por viñeta/checkbox, esto no descarta tablas ni notas."""
    lines = file_content.split("\n")
    captured, capture, header_level = [], False, None
    needle = section_title.lower()

    for line in lines:
        header_match = re.match(r"^(#+)\s+(.*)", line)
        if header_match:
            level = len(header_match.group(1))
            title = strip_md(header_match.group(2)).lower()
            if capture and level <= header_level:
                break
            if not capture and needle in title:
                capture, header_level = True, level
                continue
        if capture:
            captured.append(line)

    return "\n".join(captured).strip()


CHECKPOINT_LINE_RE = re.compile(
    r"^\s*-\s*\*{0,2}([MF]\d+)\*{0,2}(?:\s*\([^)]*\))?\s*:?\s*\*{0,2}\s*(.+)$"
)


def extract_checkpoints(md_text: str):
    """Extrae los checkpoints de contexto (- **F1 (...):** resumen) de las secciones
    de checkpoints de PROGRESS.md. Son la evidencia del Definition of Done.

    Cada checkpoint puede llevar, debajo, un bloque de código cercado (``` ... ```)
    con la salida cruda de validación (tests/build/lint) o una línea
    `Evidencia: <archivo>` que apunte a un archivo de evidencia. Ambos se capturan
    en los campos `evidence` y `evidence_file` respectivamente."""
    checkpoints, in_section = [], False
    lines = md_text.split("\n")
    i, current = 0, None
    while i < len(lines):
        line = lines[i]
        header = re.match(r"^(#+)\s+(.*)", line)
        if header:
            in_section = "checkpoint" in header.group(2).lower()
            current = None
            i += 1
            continue
        if not in_section:
            i += 1
            continue
        match = CHECKPOINT_LINE_RE.match(line)
        if match:
            current = {"phase": match.group(1).upper(),
                       "summary": match.group(2).strip(),
                       "evidence": "", "evidence_file": None}
            checkpoints.append(current)
            i += 1
            continue
        if current is not None:
            if re.match(r"^\s*```", line):
                buf = []
                i += 1
                while i < len(lines) and not re.match(r"^\s*```", lines[i]):
                    buf.append(lines[i].strip())
                    i += 1
                i += 1  # consume la valla de cierre
                current["evidence"] = "\n".join(buf).strip()
                continue
            ev = re.match(r"^\s*Evidencia\s*:\s*(.+)$", line)
            if ev:
                current["evidence_file"] = ev.group(1).strip()
            i += 1
            continue
        i += 1
    return checkpoints


def flip_phase_status(md_text: str, phase: str, symbol: str):
    """Cambia la casilla de estado ([x]/[ ]/[~]/[!]) de la fila de `phase` en la
    tabla de fases de PROGRESS.md por `[symbol]`. Devuelve el texto editado, o None
    si no localiza la fila. Solo toca la celda de la columna 'Estado'."""
    lines = md_text.split("\n")
    i, n = 0, len(lines)
    while i < n:
        if not lines[i].strip().startswith("|"):
            i += 1
            continue
        block, start = [], i
        while i < n and lines[i].strip().startswith("|"):
            block.append(lines[i])
            i += 1
        if len(block) < 2:
            continue
        header = [strip_md(c).lower() for c in block[0].strip().strip("|").split("|")]
        phase_col = next((k for k, h in enumerate(header) if "fase" in h), None)
        status_col = next((k for k, h in enumerate(header) if "estado" in h), None)
        if phase_col is None or status_col is None:
            continue
        for j in range(1, len(block)):
            line = block[j]
            if _is_separator_row(line):
                continue
            clean = [strip_md(c) for c in line.strip().strip("|").split("|")]
            if phase_col >= len(clean) or clean[phase_col].upper() != phase.upper():
                continue
            parts = line.split("|")
            cell_idx = status_col + 1
            if cell_idx >= len(parts):
                continue
            parts[cell_idx] = re.sub(r"\[\s*[xX~! ]\s*\]", f"[{symbol}]",
                                     parts[cell_idx], count=1)
            lines[start + j] = "|".join(parts)
            return "\n".join(lines)
    return None
