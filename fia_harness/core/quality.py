"""Gates de calidad y riesgo (v3.1): presencia, completitud y decisión humana.

Principio: FIA **no juzga calidad**. Aquí solo se comprueba que existen los
artefactos y que las fases con señales de riesgo tienen una **decisión humana
registrada** (aprobación o exención motivada).

- `validate_risk_decisions`: fail-closed (gobernanza). Va en `--check` y `verify`.
- `quality_advisories`: avisos que **nunca** bloquean (observabilidad).

Grandfathering (ADR-007): las fases cuyo checkpoint es anterior a
`GRANDFATHER_BEFORE` se consideran legacy (como ADR-004) y no generan avisos.
"""

import re
from pathlib import Path

from fia_harness.core import policy
from fia_harness.core.approvals import APPROVAL_REF_RE
from fia_harness.parser.markdown import load_file

GRANDFATHER_BEFORE = "2026-09-16"  # ISO: cierres anteriores a esta fecha = legacy
TASK_REPORT_SECTIONS = (
    ("2", ("diagnóstico", "diagnostico", "diseño", "diseno")),
    ("8", ("tests",)),
    ("10", ("lint",)),
    ("11", ("build",)),
    ("12", ("seguridad",)),
)


def _phases(state: dict):
    for key in ("process_phases", "execution_phases"):
        for phase in state.get(key, []):
            yield phase


def _checkpoints(state: dict) -> dict:
    return {c.get("phase"): c for c in state.get("checkpoints", [])}


def _decision_text(project_dir: Path, checkpoint, phase_id: str) -> str:
    """Texto donde buscar la decisión humana: TASK-Fx.md + checkpoint."""
    chunks = []
    task = project_dir / f"TASK-{phase_id}.md"
    if task.exists():
        chunks.append(task.read_text(encoding="utf-8"))
    if checkpoint:
        chunks += [checkpoint.get("summary") or "",
                   checkpoint.get("evidence") or "",
                   checkpoint.get("evidence_file") or ""]
    return "\n".join(chunks)


def validate_risk_decisions(state: dict, project_dir: Path) -> list:
    """Fases con señales de riesgo exigen una decisión humana registrada (fail-closed).

    La heurística NO bloquea por la palabra clave: bloquea por la ausencia de una
    decisión humana (aprobación o exención) citada en la TASK o en el checkpoint.
    """
    errors = []
    checkpoints = _checkpoints(state)
    context = load_file(project_dir / "CONTEXT.md", required=False)
    lite = policy.detect_lite_mode(context, project_dir, forced=False)
    for phase in _phases(state):
        signals = policy.risk_signals(phase)
        if not signals:
            continue
        phase_id = phase.get("id", "?")
        status = phase.get("status")
        listed = ", ".join(signals)
        if status in ("in_progress", "done") and lite:
            errors.append(f"{phase_id} toca riesgo ({listed}) y el proyecto está en Modo Lite: "
                          f"promociona a Modo Completo (QUICKSTART_LITE.md §2) antes de continuar")
        if status == "done" and not APPROVAL_REF_RE.search(
                _decision_text(project_dir, checkpoints.get(phase_id), phase_id)):
            errors.append(f"{phase_id} está cerrada con señales de riesgo ({listed}) y no registra "
                          f"ninguna decisión humana: cita una APPROVAL-NNN en su TASK o checkpoint "
                          f"(aprobación o exención motivada) — `fia approve \"...\" --phase {phase_id}`")
    return errors


def _missing_report_sections(task_text: str) -> list:
    """Secciones del INFORME FINAL (2/8/10/11/12) ausentes o vacías."""
    final = re.search(r"^#{1,3}\s*TASK-.*INFORME FINAL", task_text,
                      re.MULTILINE | re.IGNORECASE)
    body = task_text[final.end():] if final else task_text
    missing = []
    for number, keywords in TASK_REPORT_SECTIONS:
        matches = [m for m in re.finditer(rf"^#{{2,4}}\s*{number}\.\s*(.*)$", body, re.MULTILINE)
                   if any(k in m.group(1).lower() for k in keywords)]
        if not matches:
            missing.append(number)
            continue
        section = body[matches[-1].end():]
        nxt = re.search(r"^#{2,4}\s", section, re.MULTILINE)
        section = (section[:nxt.start()] if nxt else section).strip()
        if not section or section.startswith("<"):
            missing.append(number)
    return missing


def quality_advisories(state: dict, project_dir: Path) -> list:
    """Avisos de calidad que NUNCA bloquean (observabilidad, no autoridad)."""
    advisories = []
    checkpoints = _checkpoints(state)
    for phase in _phases(state):
        phase_id = phase.get("id", "?")
        signals = policy.risk_signals(phase)
        if phase.get("status") == "pending" and signals:
            advisories.append(f"{phase_id}: fase pendiente con señales de riesgo "
                              f"({', '.join(signals)}): planifica su decisión humana")
        if phase.get("status") != "done" or not str(phase_id).startswith("F"):
            continue
        checkpoint = checkpoints.get(phase_id)
        recorded = (checkpoint or {}).get("recorded_at") or ""
        if not recorded or recorded[:10] < GRANDFATHER_BEFORE:
            continue  # legacy (ADR-007): no se avisa de cierres anteriores al gate
        task = project_dir / f"TASK-{phase_id}.md"
        if task.exists():
            missing = _missing_report_sections(task.read_text(encoding="utf-8"))
            if missing:
                advisories.append(f"{phase_id}: informe TASK incompleto "
                                  f"(secciones {', '.join(missing)} vacías)")
    return advisories
