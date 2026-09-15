"""Aprobaciones humanas selladas (APPROVAL-NNN) y su validación.

Se separa de `state.py` porque el módulo de estado ya dolía por tamaño (criterio
del plan v3: extraer cuando un módulo concreto lo necesite). El modelo completo de
aproximación con hash/firma es v3.1+ (roadmap diferido); aquí solo se valida lo
que ya existe en v2.2.
"""

import re

APPROVAL_REF_RE = re.compile(r"APPROVAL-(\d+)")
APPROVAL_ENTRY_RE = re.compile(r"\*\*APPROVAL-(\d+)\*\*")


def validate_approvals(state: dict, project_dir) -> list:
    """Lo que una TASK cita debe existir en DECISIONS.md, y toda entrada registrada
    debe estar completa (fecha, acción, aprobador)."""
    errors = []
    approvals_defined = set()
    decisions_path = project_dir / "DECISIONS.md"
    if decisions_path.exists():
        for line in decisions_path.read_text(encoding="utf-8").splitlines():
            match = APPROVAL_ENTRY_RE.search(line)
            if not match:
                continue
            approvals_defined.add(match.group(1))
            if (not re.search(r"\d{4}-\d{2}-\d{2}", line)
                    or "acción" not in line.lower()
                    or "aprobado por" not in line.lower()):
                errors.append(f"APPROVAL-{match.group(1)} en DECISIONS.md está incompleta: "
                              f"necesita fecha (AAAA-MM-DD), 'Acción:' y 'Aprobado por:'")
    for task_file in sorted(project_dir.glob("TASK-*.md")):
        content = task_file.read_text(encoding="utf-8")
        for ref in APPROVAL_REF_RE.findall(content):
            if ref not in approvals_defined:
                errors.append(f"{task_file.name} cita APPROVAL-{ref}, que no está registrada "
                              f"en DECISIONS.md (regístrala con --approval)")
    return errors
