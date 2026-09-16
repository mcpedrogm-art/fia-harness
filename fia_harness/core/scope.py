"""Scope post-hoc (v3.2): el diff debe caer dentro del alcance declarado de la TASK.

El alcance se declara en `TASK-Fx.md`, en una sección cuyo título contenga "alcance"
o "scope", como lista de globs. Sin sección (o vacía) el gate se omite
(compatibilidad con fases y proyectos existentes). Los archivos de gobernanza de la
propia fase están siempre permitidos.
"""

import fnmatch
import re
from pathlib import Path

from fia_harness.adapters import git

IMPLICIT_ALLOWED = ("PROGRESS.md", "progress.json", "DECISIONS.md", "SPEC.md",
                    "CONTEXT.md", "TASK-*.md", "evidence/**", "reproduce.json")


def declared_scope(task_text: str) -> list:
    """Globs declarados en la sección de alcance (vacío si no hay sección útil)."""
    globs, capture = [], False
    for line in task_text.split("\n"):
        header = re.match(r"^(#{2,4})\s+(.*)", line)
        if header:
            title = header.group(2).lower()
            capture = "alcance" in title or "scope" in title
            continue
        if not capture:
            continue
        item = line.strip()
        if not item.startswith(("-", "*")):
            continue
        value = item.lstrip("-* ").strip()
        if value and not value.startswith("<") and not value.startswith("<!--"):
            globs.append(value)
    return globs


def _active_phase(state: dict):
    """Fase F en curso (solo se comprueba scope mientras se trabaja en una fase)."""
    for key in ("process_phases", "execution_phases"):
        for phase in state.get(key, []):
            if (str(phase.get("id", "")).startswith("F")
                    and phase.get("status") == "in_progress"):
                return phase
    return None


def _is_allowed(path: str, globs) -> bool:
    return any(fnmatch.fnmatch(path, pattern)
               for pattern in list(IMPLICIT_ALLOWED) + list(globs))


def validate_scope(project_dir: Path, state: dict, base: str = None):
    """Devuelve (errors, note). Sin repo, sin fase en curso o sin alcance → sin errores."""
    if not git.is_repo(project_dir):
        return [], "omitido: no es un repo git"
    phase = _active_phase(state)
    if phase is None:
        return [], "omitido: sin fase F en curso"
    task = project_dir / f"TASK-{phase['id']}.md"
    if not task.exists():
        return [], f"omitido: {task.name} no existe"
    globs = declared_scope(task.read_text(encoding="utf-8"))
    if not globs:
        return [], f"omitido: {phase['id']} no declara alcance"
    changed = git.changed_files(project_dir, base)
    note = (f"{len(changed)} archivo(s) vs alcance de {phase['id']}"
            + (f" (base {base})" if base else ""))
    out_of_scope = [path for path in changed if not _is_allowed(path, globs)]
    if out_of_scope:
        return ([f"{phase['id']}: cambios fuera del alcance declarado en "
                 f"TASK-{phase['id']}.md: " + ", ".join(out_of_scope)], note)
    return [], note
