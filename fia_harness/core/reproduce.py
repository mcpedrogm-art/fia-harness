"""Reproducción de evidencia (v3.2, opt-in).

`fia verify --reproduce [EV-NNN]` re-ejecuta el comando de un registro de evidencia
y compara **exit code + salida normalizada** contra los artifacts originales.

NUNCA es el comportamiento por defecto: re-ejecutar comandos tiene efectos
secundarios (migraciones, red) y flakiness. Requiere una **allowlist explícita** del
proyecto en `reproduce.json`; sin allowlist no se reproduce nada (fail-closed).
"""

import json
import re
import subprocess
from pathlib import Path

from fia_harness.core import evidence as ev

ALLOWLIST_FILE = "reproduce.json"

# Patrones volátiles que se normalizan antes de comparar salidas.
_VOLATILE_PATTERNS = (
    (re.compile(r"\bin \d+(?:\.\d+)?s\b"), "in <T>s"),          # "Ran 2 tests in 0.001s"
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?"), "<timestamp>"),
    (re.compile(r"0x[0-9a-fA-F]+"), "<addr>"),
)


def load_allowlist(project_dir: Path) -> list:
    """Prefijos de comando permitidos para reproducir (lista de strings)."""
    path = project_dir / ALLOWLIST_FILE
    if not path.exists():
        return []
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    prefixes = config.get("allow_prefixes", [])
    return [str(p).strip() for p in prefixes if str(p).strip()]


def is_allowed(command, prefixes) -> bool:
    """El comando (lista argv) debe empezar por alguno de los prefijos permitidos."""
    joined = " ".join(command or [])
    return any(joined.startswith(prefix) for prefix in prefixes)


def normalize_output(text: str, project_dir: Path) -> str:
    """Normaliza salida volátil (tiempos, timestamps, rutas, direcciones) para comparar."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace(str(project_dir), "<project>")
    for pattern, replacement in _VOLATILE_PATTERNS:
        text = pattern.sub(replacement, text)
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def reproduce_record(project_dir: Path, record: dict) -> dict:
    """Reproduce un registro. Devuelve {id, status, detail} con status:
    `reproduced` (coincide), `mismatch` (difiere), `skipped` (no aplicable)."""
    evidence_id = record.get("id", "?")
    command = list(record.get("command") or [])
    if not command:
        return {"id": evidence_id, "status": "skipped", "detail": "registro sin comando"}
    prefixes = load_allowlist(project_dir)
    if not prefixes:
        return {"id": evidence_id, "status": "skipped",
                "detail": f"sin allowlist ({ALLOWLIST_FILE})"}
    if not is_allowed(command, prefixes):
        return {"id": evidence_id, "status": "skipped",
                "detail": "comando fuera de la allowlist"}

    cwd = Path(record.get("cwd") or project_dir)
    if not cwd.exists():
        cwd = project_dir
    try:
        proc = subprocess.run(command, cwd=cwd, capture_output=True)
    except OSError as exc:
        return {"id": evidence_id, "status": "mismatch",
                "detail": f"no se pudo ejecutar: {exc}"}

    details = []
    if proc.returncode != record.get("exit_code"):
        details.append(f"exit code {proc.returncode} != {record.get('exit_code')}")
    for stream, produced in (("stdout", proc.stdout), ("stderr", proc.stderr)):
        artifact = project_dir / ev.EVIDENCE_DIR / f"{evidence_id}.{stream}.txt"
        if not artifact.exists():
            continue
        expected = normalize_output(artifact.read_text(encoding="utf-8", errors="replace"),
                                    project_dir)
        current = normalize_output(produced.decode("utf-8", errors="replace"), project_dir)
        if expected != current:
            details.append(f"{stream} difiere (salida no reproducible)")
    if details:
        return {"id": evidence_id, "status": "mismatch", "detail": "; ".join(details)}
    return {"id": evidence_id, "status": "reproduced",
            "detail": f"exit {proc.returncode}, salida idéntica"}


def reproduce_records(project_dir: Path, records) -> list:
    """Reproduce una lista de registros (en orden) y devuelve sus resultados."""
    return [reproduce_record(project_dir, record) for record in records]
