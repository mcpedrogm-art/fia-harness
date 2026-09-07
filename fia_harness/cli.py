"""fia-harness CLI — instalador del kit (PyPI).

`fia-harness init` monta un proyecto nuevo con la misma estructura que describe
`INSTRUCCIONES DE APLICACION.txt`: plantillas del kit en /docs, los dos scripts
en la raíz y un `PRD.md` de partida. Igual que el resto del kit: solo librería
estándar, idempotente (nunca sobrescribe lo que ya existe) y sin telemetría.
"""

import argparse
import shutil
import sys
from pathlib import Path

from fia_harness import __version__

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
SCRIPTS_DIR = DATA_DIR / "scripts"
RAG_DIR = DATA_DIR / "rag"

TEMPLATE_NAMES = [
    "INICIO_PROYECTO.md",
    "SECURITY.md",
    "AEO_GEO_SEO.md",
    "UI_UX_EXCLUSIVA.md",
    "SKILLS_MCP.md",
    "TASK_TEMPLATE.md",
    "TASK_LITE_TEMPLATE.md",
    "QUICKSTART_LITE.md",
]

SCRIPT_NAMES = ["bootstrap.py", "task_generator.py"]

RAG_NAME = "RAG_VECTOR_EXTENSION.md"

DEFAULT_FOLDERS = ["src", "tests", "docs", "infra"]

PRD_STUB = """# <Nombre del Proyecto>

> ✏️ **PRD de partida generado por `fia-harness init`.** Completa cada sección
> antes de aprobar la Fase 1 (entrevista técnica). Si dejas esta plantilla tal
> cual, el bootstrap te avisará de los campos sin confirmar.

## Problema

✏️ Describe el problema de negocio que resuelve tu producto.

## Usuarios

✏️ ¿Quiénes son los usuarios finales? ¿Qué perfil, cuántos, qué frecuencia?

## Funcionalidades (Must Have)

* ✏️ Funcionalidad imprescindible nº1.
* ✏️ Funcionalidad imprescindible nº2.

## Fuera de alcance (Out of Scope)

* ✏️ Lo que explícitamente NO entra en esta versión.
"""


def _print_banner():
    print(f"======================================================================")
    print(f"     🚀 FIA HARNESS v{__version__} — INSTALADOR DE PROYECTOS (init)")
    print(f"======================================================================")


def copy_if_absent(source: Path, target: Path, label: str) -> None:
    """Copia `source` a `target` si no existe: el kit nunca pisa lo tuyo."""
    if target.exists():
        print(f"   [.] Ya existe (no sobrescrito): {label}")
        return
    shutil.copy2(source, target)
    print(f"   [+] {label}")


def run_init(target_dir: Path) -> int:
    _print_banner()

    for folder in DEFAULT_FOLDERS:
        folder_path = target_dir / folder
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"   [+] Creada carpeta: /{folder}")
        else:
            print(f"   [.] Ya existe carpeta: /{folder}")

    print("\n-> Copiando plantillas del kit a /docs ...")
    for name in TEMPLATE_NAMES:
        copy_if_absent(TEMPLATES_DIR / name, target_dir / "docs" / name, f"docs/{name}")
    copy_if_absent(RAG_DIR / RAG_NAME, target_dir / "docs" / RAG_NAME,
                   f"docs/{RAG_NAME} (módulo RAG/vectorial opcional)")

    print("\n-> Copiando los dos scripts del kit a la raíz ...")
    for name in SCRIPT_NAMES:
        copy_if_absent(SCRIPTS_DIR / name, target_dir / name, name)

    print("\n-> Preparando PRD.md de partida ...")
    prd_path = target_dir / "PRD.md"
    if prd_path.exists():
        print("   [.] PRD.md ya existe (no sobrescrito).")
    else:
        prd_path.write_text(PRD_STUB, encoding="utf-8")
        print("   [+] PRD.md generado (complétalo antes de la Fase 1).")

    print()
    print("✅ Proyecto montado. Siguientes pasos:")
    print(f"   1. Completa {target_dir / 'PRD.md'}")
    print(f"   2. cd {target_dir} && python bootstrap.py   (Fase M0)")
    print("   3. Abre tu agente con la carpeta: leerá CONTEXT.md y empezará la entrevista (M1).")
    return 0


def _fix_windows_console_encoding():
    """Evita UnicodeEncodeError (🚀/✅) en consolas Windows con codificación cp1252."""
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def main(argv=None) -> int:
    _fix_windows_console_encoding()
    parser = argparse.ArgumentParser(
        prog="fia-harness",
        description="FIA Harness: kit local de especificación y enforcement para agentes de IA.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="Monta un proyecto nuevo: plantillas en /docs, scripts en la raíz y PRD.md.",
    )
    init_parser.add_argument(
        "-d", "--dir", default=".",
        help="Directorio de destino del proyecto (por defecto: el actual).",
    )

    args = parser.parse_args(argv)

    if args.command == "init":
        return run_init(Path(args.dir))

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
