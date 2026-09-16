"""Adaptador de git (v3.2): archivos cambiados para el gate de scope post-hoc.

Solo lectura (`git diff --name-only`). Si no hay repo o git falla, devuelve una
lista vacía y el llamante decide (el gate se omite, no bloquea).
"""

import subprocess
from pathlib import Path


def is_repo(project_dir: Path) -> bool:
    return (project_dir / ".git").exists()


def _run(project_dir: Path, *args) -> list:
    try:
        proc = subprocess.run(["git", *args], cwd=project_dir, capture_output=True, text=True)
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def changed_files(project_dir: Path, base: str = None) -> list:
    """Archivos cambiados: diff contra `base` (p. ej. `origin/main`) si se da;
    si no, los cambios del working tree respecto a HEAD **incluyendo untracked**
    (`git diff` no lista archivos nuevos sin trackear)."""
    if base:
        return sorted(set(_run(project_dir, "diff", "--name-only", f"{base}...HEAD")))
    names = set(_run(project_dir, "diff", "--name-only", "HEAD"))
    names.update(_run(project_dir, "ls-files", "--others", "--exclude-standard"))
    return sorted(names)
