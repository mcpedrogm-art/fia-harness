"""Adaptador de git (v3.2/v3.3): archivos cambiados (scope) y lectura para recibos.

Solo lectura. `is_repo` detecta el repositorio real con `git rev-parse` (funciona
aunque el estado del harness viva en una subcarpeta, p. ej. `-d governance`). Si
git falla, los llamantes deciden: el gate de scope se omite y el recibo exige git.
"""

import subprocess
from pathlib import Path


def _run(project_dir: Path, *args) -> list:
    try:
        proc = subprocess.run(["git", *args], cwd=project_dir, capture_output=True, text=True)
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def is_repo(project_dir: Path) -> bool:
    try:
        proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=project_dir,
                              capture_output=True, text=True)
    except OSError:
        return False
    return proc.returncode == 0


def toplevel(project_dir: Path):
    """Raíz del repositorio que contiene `project_dir` (o None si no hay repo)."""
    out = _run(project_dir, "rev-parse", "--show-toplevel")
    return Path(out[0]) if out else None


def head_ref(project_dir: Path):
    """Commit actual (`git rev-parse HEAD`) o None si no hay commits."""
    out = _run(project_dir, "rev-parse", "HEAD")
    return out[0] if out else None


def show_file(project_dir: Path, ref: str, path: str):
    """Bytes del archivo en `ref` (path relativo a la raíz del repo), o None."""
    try:
        proc = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=project_dir,
                              capture_output=True)
    except OSError:
        return None
    return proc.stdout if proc.returncode == 0 else None


def changed_files(project_dir: Path, base: str = None) -> list:
    """Archivos cambiados (rutas relativas a la raíz del repo): diff contra `base`
    si se da; si no, los cambios del working tree respecto a HEAD **incluyendo
    untracked** (`git diff` no lista archivos nuevos sin trackear).

    Se ejecuta desde la raíz del repo para no limitar `ls-files` a una subcarpeta
    cuando el estado del harness vive fuera de ella (p. ej. `-d governance`)."""
    root = toplevel(project_dir) or project_dir
    if base:
        return sorted(set(_run(root, "diff", "--name-only", f"{base}...HEAD")))
    names = set(_run(root, "diff", "--name-only", "HEAD"))
    names.update(_run(root, "ls-files", "--others", "--exclude-standard"))
    return sorted(names)
