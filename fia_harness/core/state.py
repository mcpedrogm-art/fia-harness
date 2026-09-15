"""Modelo de estado del harness: compilación, validación estricta y persistencia.

`STATE = authority; MARKDOWN = projection`. PROGRESS.md se compila a `progress.json`
(schema `3.0`, migración incremental desde `harness-state/1` según ADR-002) y se
valida contra las Reglas de Oro detectables por máquina. Las huellas (deriva e
integridad) viven en `core.fingerprints`.
"""

import datetime
import json
import re
import shutil
from pathlib import Path

from fia_harness.core import approvals, evidence
from fia_harness.core.fingerprints import (sha256_hex, state_fingerprint,
                                           state_sha256, validate_state_integrity)
from fia_harness.core.seals import (REQUIRED_SEALED, compute_doc_hashes,  # noqa: F401
                                    validate_sealed_docs)
from fia_harness.parser.markdown import extract_checkpoints, parse_progress_table

STATE_FILE = "progress.json"
SCHEMA_VERSION = "3.0"
LEGACY_SCHEMA = "harness-state/1"
SCHEMA_NAME = LEGACY_SCHEMA  # alias histórico: API v2.2 que re-exportan las fachadas
STATUS_VALUES = ("pending", "in_progress", "blocked", "done")
STATUS_SYMBOLS = {"x": "done", "X": "done", "~": "in_progress", "!": "blocked"}
PHASE_ID_RE = re.compile(r"^[MF]\d+$")

# Registro de archivos del proyecto que el kit conoce por nombre.
DEFAULT_FILES = {
    "context": "CONTEXT.md",
    "progress": "PROGRESS.md",
    "spec": "SPEC.md",
    "security": "SECURITY.md",
    "aeo_geo_seo": "AEO_GEO_SEO.md",
    "ui_ux": "UI_UX_EXCLUSIVA.md",
    "template": "TASK_TEMPLATE.md",
    "template_lite": "TASK_LITE_TEMPLATE.md",
}


def schema_of(state: dict) -> str:
    """Identificador de schema del estado (3.0 o el legado harness-state/1)."""
    return state.get("schema_version") or state.get("schema") or ""


def is_legacy_state(state: dict) -> bool:
    return schema_of(state) == LEGACY_SCHEMA


def phase_status(status_raw: str) -> str:
    """Traduce la casilla Markdown ([x], [~], [!], [ ]) a un estado del enum."""
    match = re.search(r"\[\s*([xX~!])\s*\]", status_raw or "")
    return STATUS_SYMBOLS[match.group(1)] if match else "pending"


def _split_dependencies(raw: str):
    """Separa la celda 'Depende de' en identificadores de fase validables y notas
    de texto libre ('SPEC aprobado' es una nota, no una fase)."""
    tokens = [t.strip() for t in re.split(r"[/,;]", raw or "") if t.strip()]
    ids = [t.upper() for t in tokens if PHASE_ID_RE.match(t.upper())]
    notes = [t for t in tokens if t.upper() not in {i.upper() for i in ids}]
    return ids, notes


def compile_state_from_md(md_text: str, updated: str = None) -> dict:
    """Compila PROGRESS.md al modelo de estado validable (schema 3.0)."""
    process, execution, seen = [], [], set()
    for row in parse_progress_table(md_text):
        phase_id = row["phase"].upper()
        if phase_id in seen:
            continue  # duplicados: los detecta validate_state sobre el MD recompilado
        seen.add(phase_id)
        ids, notes = _split_dependencies(row["dependencies"])
        entry = {
            "id": phase_id,
            "title": row["title"],
            "objective": row["objective"],
            "depends_on": ids,
            "depends_on_notes": " / ".join(notes),
            "status": phase_status(row["status_raw"]),
        }
        (process if phase_id.startswith("M") else execution).append(entry)
    state = {
        "schema_version": SCHEMA_VERSION,
        "process_phases": process,
        "execution_phases": execution,
        "checkpoints": extract_checkpoints(md_text),
    }
    if updated:
        state["updated"] = updated
    return state


def validate_spec_snapshot(state: dict, project_dir: Path):
    """Si existe SPEC.md y ya fue aprobada (spec_hashes no vacío), su hash actual
    debe coincidir con el último snapshot aprobado. Antes de la primera aprobación
    no hay nada que comparar."""
    spec_path = project_dir / "SPEC.md"
    if not spec_path.exists():
        return []
    hashes = state.get("spec_hashes", [])
    if not hashes:
        return []
    current = sha256_hex(spec_path.read_bytes())
    latest = hashes[-1].get("sha256")
    if latest and current != latest:
        return [f"SPEC.md cambió sin nueva aprobación: el último snapshot aprobado "
                f"no coincide. Re-aprueba con --approval (o revisa el cambio)."]
    return []


def load_state_json(project_dir: Path):
    state_path = project_dir / STATE_FILE
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _ensure_ids_and_timestamps(state: dict, now: str):
    """IDs estables y timestamps para los objetos del estado (idempotente: los que
    ya existen se conservan)."""
    for checkpoint in state.get("checkpoints", []):
        checkpoint.setdefault("id", f"CP-{checkpoint.get('phase', '?')}")
        checkpoint.setdefault("recorded_at", now)
    for index, snapshot in enumerate(state.get("spec_hashes", []), start=1):
        snapshot.setdefault("id", f"SNAP-{index:03d}")
    state["compiled_at"] = now


def write_state(project_dir: Path, state: dict):
    """Escribe el estado con IDs, timestamps y huella de integridad. Si el schema
    cambia (migración legacy → 3.0), guarda antes un backup `progress.json.bak`."""
    state_path = project_dir / STATE_FILE
    previous = load_state_json(project_dir)
    if previous is not None and schema_of(previous) != schema_of(state):
        shutil.copy2(state_path, state_path.with_name(state_path.name + ".bak"))
    _ensure_ids_and_timestamps(state, datetime.datetime.now().replace(microsecond=0).isoformat())
    state["state_sha256"] = state_sha256(state)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def carry_over_aux_fields(state: dict, previous) -> dict:
    """Preserva los campos no derivables del MD (sellos, snapshots, aprobadores) y
    los timestamps de checkpoints ya registrados, para que --sync no los pierda."""
    if not previous:
        return state
    for key in ("sealed_docs", "spec_hashes", "approvers"):
        if key in previous:
            state[key] = previous[key]
    previous_times = {c.get("phase"): c.get("recorded_at")
                      for c in previous.get("checkpoints", [])}
    for checkpoint in state.get("checkpoints", []):
        recorded = previous_times.get(checkpoint.get("phase"))
        if recorded:
            checkpoint["recorded_at"] = recorded
    return state


def collect_validation_errors(state: dict, project_dir: Path):
    return (validate_state(state, project_dir)
            + validate_sealed_docs(state, project_dir)
            + validate_spec_snapshot(state, project_dir))


def validate_state(state: dict, project_dir: Path):
    """Devuelve la lista de violaciones de las reglas de oro detectables por máquina.
    Lista vacía = estado coherente. Nunca modifica nada."""
    errors = []
    schema = schema_of(state)
    if schema not in (SCHEMA_VERSION, LEGACY_SCHEMA):
        errors.append(f"'schema_version' debe ser '{SCHEMA_VERSION}' "
                      f"(o '{LEGACY_SCHEMA}' en lectura legacy); encontrado: {schema!r}")

    phases = {}
    for key in ("process_phases", "execution_phases"):
        for phase in state.get(key, []):
            phase_id = phase.get("id", "")
            if not PHASE_ID_RE.match(phase_id):
                errors.append(f"Identificador de fase inválido: {phase_id!r}")
                continue
            if phase_id in phases:
                errors.append(f"Fase duplicada: {phase_id}")
            phases[phase_id] = phase
            if phase.get("status") not in STATUS_VALUES:
                errors.append(f"{phase_id}: estado {phase.get('status')!r} no válido "
                              f"(valores: {', '.join(STATUS_VALUES)})")

    # Regla de oro nº4/5: no se cierra una fase con dependencias abiertas
    for phase_id, phase in phases.items():
        for dep in phase.get("depends_on", []):
            if dep not in phases:
                errors.append(f"{phase_id} depende de {dep}, que no existe en el estado")
            elif phase.get("status") == "done" and phases[dep].get("status") != "done":
                errors.append(f"{phase_id} está cerrada pero su dependencia {dep} no — "
                              f"nunca cerrar una fase sin cerrar las previas (Regla de Oro nº4)")

    checkpoint_ids = {c.get("phase") for c in state.get("checkpoints", [])}
    for phase_id, phase in phases.items():
        if phase.get("status") == "done" and phase_id not in checkpoint_ids:
            errors.append(f"{phase_id} está cerrada sin checkpoint de contexto en PROGRESS.md "
                          f"(Definition of Done; añade '- **{phase_id}:** resumen' en la sección de checkpoints)")

    # Evidencia cruda: una fase de ejecución (F) no puede cerrarse con prosa sola.
    errors += evidence.validate_closed_phase_evidence(state, project_dir)

    # Regla de oro nº7: ninguna fase de ejecución se cierra sin su TASK-Fx.md
    for phase_id, phase in phases.items():
        if phase.get("status") == "done" and phase_id.startswith("F"):
            if not (project_dir / f"TASK-{phase_id}.md").exists():
                errors.append(f"{phase_id} está cerrada pero no existe TASK-{phase_id}.md — "
                              f"nunca ejecutar una fase sin su TASK (Regla de Oro nº7)")

    # Aprobaciones con sello: lo que una TASK cita debe existir en DECISIONS.md,
    # y toda entrada registrada debe estar completa (fecha, acción, aprobador).
    errors += approvals.validate_approvals(state, project_dir)
    return errors
