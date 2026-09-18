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


def _run_paths(project_dir: Path, *args) -> list:
    """Salida de git con `-z`: rutas NUL-separadas, sin comillas ni escapes
    (seguras con espacios, acentos, 'ñ' y otros caracteres no-ASCII)."""
    try:
        proc = subprocess.run(["git", *args], cwd=project_dir, capture_output=True)
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return [chunk.decode("utf-8", "surrogateescape")
            for chunk in proc.stdout.split(b"\x00") if chunk]


def changed_files(project_dir: Path, base: str = None) -> list:
    """Archivos cambiados (rutas relativas a la raíz del repo): diff contra `base`
    si se da; si no, los cambios del working tree respecto a HEAD **incluyendo
    untracked** (`git diff` no lista archivos nuevos sin trackear).

    `--no-renames` para que un renombrado aparezca como borrado + alta (si no, git
    solo lista el destino y la baja del origen no queda anclada). Se ejecuta desde
    la raíz del repo para no limitar `ls-files` a una subcarpeta."""
    root = toplevel(project_dir) or project_dir
    if base:
        return sorted(set(_run_paths(root, "diff", "--name-only", "--no-renames",
                                      "-z", f"{base}...HEAD")))
    names = set(_run_paths(root, "diff", "--name-only", "--no-renames", "-z", "HEAD"))
    names.update(_run_paths(root, "ls-files", "--others", "--exclude-standard", "-z"))
    return sorted(names)
