"""Batería E2E manual del sistema FIA (no entra en `unittest discover`).

Uso:
    python tests/e2e_manual.py

Ejercita por la CLI real: init + bootstrap + check, sellos, `fia run` con `.cmd`
(PATHEXT), recibo con sellos y borrados, detección de tampering, cierre de fase,
re-emisión limpia, `verify --strict-receipts` y (si existe) el demo legacy en
`../fia-harness-demo`. Devuelve exit 0 solo si todo pasa.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEMO = Path(os.environ.get("FIA_DEMO_DIR", REPO.parent / "fia-harness-demo"))

failures = []


def env_for(path_extra=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env["PYTHONIOENCODING"] = "utf-8"
    if path_extra:
        env["PATH"] = f"{path_extra}{os.pathsep}{env.get('PATH', '')}"
    return env


def run(args, cwd, expect=0, path_extra=None, label=""):
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", env=env_for(path_extra))
    ok = proc.returncode == expect
    print(f"[{'PASS' if ok else 'FAIL'}] {label or ' '.join(map(str, args))} "
          f"(exit {proc.returncode})")
    if not ok:
        failures.append(label or " ".join(map(str, args)))
        print("  stdout:", proc.stdout.strip()[-500:])
        print("  stderr:", proc.stderr.strip()[-500:])
    return proc


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def cli(project, *args, expect=0, path_extra=None, label=""):
    return run([sys.executable, "-m", "fia_harness.cli", *args], project,
               expect=expect, path_extra=path_extra, label=label)


def main():
    tmp = tempfile.TemporaryDirectory()
    project = Path(tmp.name) / "proyecto-e2e"

    print("=== 1. init + bootstrap + check ===")
    cli(project.parent, "init", "-d", str(project), label="fia init")
    assert (project / "docs" / "UI_RECIPES.md").exists(), "falta docs/UI_RECIPES.md"
    write(project / "PRD.md", "# E2E\n\n## Problema\nProblema de prueba.\n\n"
                              "## Usuarios\nUsuarios de prueba.\n\n"
                              "## Funcionalidades\n* Uno\n\n## Fuera de alcance\n* Nada\n")
    run([sys.executable, "bootstrap.py"], project, label="bootstrap.py (M0)")
    run([sys.executable, "task_generator.py", "--check"], project,
        label="check tras bootstrap")

    print("=== 2. estado de fase + sellos ===")
    write(project / "PROGRESS.md", """# PROGRESS.md

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap | Plantillas | — | [x] Listo |
| F1 | Backend | API | M0 | [~] En curso |

## Checkpoints de Contexto Recientes
- **M0:** bootstrap listo.
""")
    write(project / "TASK-F1.md",
          "# TASK-F1\n\n## Alcance permitido (scope)\n- src/**\n- tools/**\n")
    write(project / "src" / "app.py", "print('v1')\n")
    write(project / "src" / "viejo.py", "print('old')\n")
    write(project / "tools" / "saluda.cmd", "@echo hola-desde-cmd\r\n")
    git(project, "init", "-q")
    git(project, "config", "user.email", "e2e@t")
    git(project, "config", "user.name", "e2e")
    git(project, "add", ".")
    git(project, "commit", "-qm", "base")
    cli(project, "seal", label="fia seal")
    cli(project, "sync", label="fia sync")

    print("=== 3. evidencia con fia run (resolución .cmd) ===")
    cli(project, "run", "--type", "test", "--", "saluda",
        path_extra=str(project / "tools"), label="fia run -- saluda (.cmd)")
    assert (project / "evidence" / "EV-001.json").exists(), "falta EV-001"

    print("=== 4. cambios + borrado + recibo dirty ===")
    write(project / "src" / "app.py", "print('v2')\n")
    (project / "src" / "viejo.py").unlink()
    cli(project, "receipt", "create", "F1", "--allow-dirty", "--evidence", "EV-001",
        "--tests", "5/5", label="receipt create (sellos + borrado)")
    receipt = json.loads((project / "evidence" / "receipts" / "receipt-F1.json")
                         .read_text(encoding="utf-8"))
    deleted = [f for f in receipt["files"] if f.get("deleted")]
    assert deleted and deleted[0]["path"] == "src/viejo.py", "borrado no representado"
    cli(project, "receipt", "verify", "F1", label="receipt verify (dirty)")

    print("=== 5. tampering del árbol ===")
    write(project / "src" / "app.py", "print('v2-manipulado')\n")
    cli(project, "receipt", "verify", "F1", expect=1, label="tampering detectado (exit 1)")
    write(project / "src" / "app.py", "print('v2')\n")
    cli(project, "receipt", "verify", "F1", label="restaurado")

    print("=== 6. cierre de fase y recibo limpio ===")
    write(project / "PROGRESS.md", """# PROGRESS.md

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap | Plantillas | — | [x] Listo |
| F1 | Backend | API | M0 | [x] Listo |

## Checkpoints de Contexto Recientes
- **M0:** bootstrap listo.
- **F1:** API lista.
    Evidencia: EV-001
    Recibo: evidence/receipts/receipt-F1.json
""")
    cli(project, "sync", label="sync de cierre")
    cli(project, "check", label="check de cierre")
    cli(project, "verify", label="verify (dirty aceptado en local)")
    git(project, "add", "-A")
    git(project, "commit", "-qm", "fase F1")
    cli(project, "receipt", "create", "F1", "--base", "HEAD~1", "--evidence", "EV-001",
        "--tests", "5/5", label="re-emisión limpia")
    clean = json.loads((project / "evidence" / "receipts" / "receipt-F1.json")
                       .read_text(encoding="utf-8"))
    assert clean["dirty"] is False, "recibo no quedó limpio"
    cli(project, "receipt", "verify", "F1", label="receipt verify (limpio)")
    cli(project, "verify", "--strict-receipts", label="verify --strict-receipts")

    print("=== 7. demo legacy (sin recibos) ===")
    if DEMO.exists():
        run([sys.executable, "-m", "fia_harness.cli", "verify", "-d", str(DEMO)],
            REPO, label="demo: verify legacy PASS")
    else:
        print("[SKIP] demo no encontrado en", DEMO)

    print()
    if failures:
        print(f"RESULTADO: {len(failures)} FALLOS -> {failures}")
        return 1
    print("RESULTADO: TODO OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
