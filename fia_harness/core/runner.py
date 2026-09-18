"""Wrapper de ejecución `fia run -- <comando>` (F5, opcional por ADR-005).

Ejecuta el comando, captura ambos streams, tiempos y exit code, y registra la
evidencia (EV-NNN) con sus artifacts. Nunca es obligatorio: los artifacts de CI
son la fuente de verdad; esto mejora la confianza en local si el agente lo usa.

Hallazgo del spike F4: los runners escriben donde quieren (`unittest` → stderr),
así que se capturan y hashean SIEMPRE ambos streams.
"""

import datetime
import platform
import shutil
import subprocess
import time
from pathlib import Path

from fia_harness.core import evidence
from fia_harness.core.console import fail, fix_windows_console_encoding


def cmd_run(project_dir: Path, command, record_type: str = "test") -> int:
    """Ejecuta `command` (lista argv) y registra su evidencia. Devuelve el exit
    code del comando hijo (0 = éxito), de modo que `fia run` sea transparente."""
    fix_windows_console_encoding()
    if not command:
        fail("Uso: fia run [-d DIR] [--type T] -- <comando...>")
    command = list(command)
    root = project_dir.resolve()
    # Resolver con shutil.which aplica PATHEXT en Windows: `npm` → `npm.cmd`
    # (subprocess directo lanzaría [WinError 2] con npm/npx/pip).
    executable = shutil.which(command[0])
    if executable is None:
        fail(f"No se encontró el comando '{command[0]}' en el PATH. En Windows, "
             "npm/npx/pip necesitan su nombre real (p. ej. `fia run -- npm.cmd ...`).")
    started = datetime.datetime.now(datetime.timezone.utc)
    t0 = time.perf_counter()
    try:
        proc = subprocess.run([executable, *command[1:]], cwd=root, capture_output=True)
    except OSError as error:
        fail(f"No se pudo ejecutar '{command[0]}': {error}")
    t1 = time.perf_counter()
    finished = datetime.datetime.now(datetime.timezone.utc)

    evidence_id = evidence.next_evidence_id(root)
    record = evidence.create_record(
        evidence_id=evidence_id, record_type=record_type, source="local-run",
        command=command, cwd=root, exit_code=proc.returncode,
        started_at=started.isoformat(), finished_at=finished.isoformat(),
        duration_s=round(t1 - t0, 3), stdout=proc.stdout, stderr=proc.stderr,
        environment={"python": platform.python_version(), "os": platform.platform()})
    evidence.write_streams(root, evidence_id, proc.stdout, proc.stderr)
    evidence.save_record(root, record)

    print(f"✅ Evidencia registrada: {evidence_id} (exit {proc.returncode}, "
          f"{record['duration_s']}s, {len(record['artifacts'])} artifacts)")
    print(f"   Cítala en el checkpoint: Evidencia: {evidence_id}")
    return proc.returncode
