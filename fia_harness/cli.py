"""FIA Harness CLI — instalador y comandos del kit.

`fia init` monta un proyecto nuevo con la estructura que describe el protocolo
(`templates/INICIO_PROYECTO.md`): plantillas del kit en /docs, fachadas de los
scripts en la raíz (que importan el paquete instalado, ADR-001) y un `PRD.md` de
partida. El resto de subcomandos (`check`, `sync`, `task`, `status`, `approve`,
`seal`, `reopen`, `run`, `evidence`, `verify`) delegan en el núcleo: `fia` y
`fia-harness` son el mismo comando. Igual que el resto del kit: solo librería
estándar, idempotente (nunca sobrescribe lo que ya existe) y sin telemetría.
"""

import argparse
import shutil
import sys
from pathlib import Path

from fia_harness import __version__
from fia_harness.core import commands
from fia_harness.core.console import fix_windows_console_encoding
from fia_harness.facades import facade_files

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
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
    "AGENTS.md",
    "PRD_TEMPLATE.md",
    "MODELOS.md",
]

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

## Funcionalidades

* ✏️ Funcionalidad imprescindible nº1.
* ✏️ Funcionalidad imprescindible nº2.

## Fuera de alcance

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

    print("\n-> Escribiendo las fachadas de los scripts en la raíz ...")
    for name, content in facade_files().items():
        facade_path = target_dir / name
        if facade_path.exists():
            print(f"   [.] Ya existe (no sobrescrito): {name}")
            continue
        with open(facade_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"   [+] {name} (fachada; requiere `pip install fia-harness`)")

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


def main(argv=None) -> int:
    fix_windows_console_encoding()
    parser = argparse.ArgumentParser(
        prog="fia",
        description="FIA Harness: kit local de especificación y enforcement para agentes de IA.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="Monta un proyecto nuevo: plantillas en /docs, fachadas en la raíz y PRD.md.",
    )
    init_parser.add_argument("-d", "--dir", default=".",
                             help="Directorio de destino del proyecto (por defecto: el actual).")

    sync_parser = subparsers.add_parser("sync", help="Compila y valida PROGRESS.md → progress.json.")
    sync_parser.add_argument("-d", "--dir", default=".")

    check_parser = subparsers.add_parser("check", help="Valida el estado sin modificar nada (lo que ejecuta el CI).")
    check_parser.add_argument("-d", "--dir", default=".")
    check_parser.add_argument("--state-optional", action="store_true",
                              help="Permite validar sin progress.json (escape explícito).")

    status_parser = subparsers.add_parser("status", help="Resumen del estado del proyecto.")
    status_parser.add_argument("-d", "--dir", default=".")

    approve_parser = subparsers.add_parser("approve", help="Registra una aprobación humana (APPROVAL-NNN).")
    approve_parser.add_argument("accion", help="Acción aprobada.")
    approve_parser.add_argument("--phase", default=None, help="Fase asociada (p. ej. M2 o F3).")
    approve_parser.add_argument("--ref", default="", help="Referencia (chat, PR, reunión).")
    approve_parser.add_argument("--approved-by", default="Humano", help="Quién aprueba.")
    approve_parser.add_argument("-d", "--dir", default=".")

    seal_parser = subparsers.add_parser("seal", help="Sella documentos normativos (SHA-256).")
    seal_parser.add_argument("docs", nargs="*", help="Documentos extra a sellar (sin args: set obligatorio).")
    seal_parser.add_argument("-d", "--dir", default=".")

    reopen_parser = subparsers.add_parser("reopen", help="Reabre una fase cerrada (done → in_progress).")
    reopen_parser.add_argument("fase", help="Código de fase (p. ej. F3).")
    reopen_parser.add_argument("--reason", required=True, help="Motivo de la reapertura.")
    reopen_parser.add_argument("-d", "--dir", default=".")

    task_parser = subparsers.add_parser("task", help="Genera el TASK-Fx.md de la fase activa.")
    task_parser.add_argument("-p", "--phase", default=None, help="Fase explícita (p. ej. F1).")
    task_parser.add_argument("-l", "--lite", action="store_true", help="Forzar la plantilla Lite.")
    task_parser.add_argument("-d", "--dir", default=".")

    run_parser = subparsers.add_parser("run", help="Ejecuta un comando y registra su evidencia (EV-NNN).")
    run_parser.add_argument("-d", "--dir", default=".")
    run_parser.add_argument("--type", default="test", help="Tipo de evidencia (por defecto: test).")
    run_parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Comando: fia run -- <cmd...>")

    evidence_parser = subparsers.add_parser("evidence", help="Lista, muestra o ancla evidencia (EV-NNN).")
    evidence_parser.add_argument("evidence_id", nargs="?", default=None,
                                 help="ID a mostrar con su cadena validada (p. ej. EV-001).")
    evidence_parser.add_argument("--ingest", default=None, metavar="MANIFEST",
                                 help="Adjunta los digests de CI desde un manifiesto.")
    evidence_parser.add_argument("-d", "--dir", default=".")

    verify_parser = subparsers.add_parser(
        "verify", help="Reporte de verificación (STATE/DEPS/EVIDENCE/PROVENANCE/SEALS/SPEC).")
    verify_parser.add_argument("-d", "--dir", default=".")

    args = parser.parse_args(argv)
    target = Path(args.dir)

    if args.command == "init":
        return run_init(target)
    if args.command == "sync":
        commands.cmd_sync(target)
        return 0
    if args.command == "check":
        commands.cmd_check(target, state_optional=args.state_optional)
        return 0
    if args.command == "status":
        commands.cmd_stats(target)
        return 0
    if args.command == "approve":
        commands.cmd_approval(target, args.accion, args.phase, args.ref, args.approved_by)
        return 0
    if args.command == "seal":
        commands.cmd_seal(target, args.docs)
        return 0
    if args.command == "reopen":
        commands.cmd_reopen(target, args.fase, args.reason)
        return 0
    if args.command == "task":
        from fia_harness.legacy import main_task_generator
        legacy_argv = ["--dir", str(target)]
        if args.phase:
            legacy_argv += ["--phase", args.phase]
        if args.lite:
            legacy_argv.append("--lite")
        main_task_generator(legacy_argv)
        return 0
    if args.command == "run":
        from fia_harness.core.runner import cmd_run
        tokens = list(args.cmd or [])
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
        return cmd_run(target, tokens, args.type)
    if args.command == "evidence":
        from fia_harness.core.evidence import cmd_evidence
        return cmd_evidence(target, args.evidence_id, args.ingest)
    if args.command == "verify":
        from fia_harness.core.verify import cmd_verify
        return cmd_verify(target)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
