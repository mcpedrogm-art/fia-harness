"""FIA Harness CLI — instalador y comandos del kit.

`fia init` monta un proyecto nuevo con la estructura que describe el protocolo
(`templates/INICIO_PROYECTO.md`): plantillas del kit en /docs, fachadas de los
scripts en la raíz (que importan el paquete instalado, ADR-001) y un `PRD.md` de
partida. El resto de subcomandos (`check`, `sync`, `task`, `status`, `approve`,
`seal`, `reopen`, `run`, `evidence`, `receipt`, `route`, `assets`, `ui`, `verify`)
delegan en el núcleo: `fia` y `fia-harness` son el mismo comando. Igual que el
resto del kit: solo librería estándar, idempotente (nunca sobrescribe lo que ya
existe) y sin telemetría.
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
    "UI_RECIPES.md",
    "UI_ASSETS.json",
    "QUICKSTART_LITE.md",
    "AGENTS.md",
    "PRD_TEMPLATE.md",
    "MODELOS.md",
    "TYPESAFE_EXTENSION.md",
]

RAG_NAME = "RAG_VECTOR_EXTENSION.md"

DEFAULT_FOLDERS = ["src", "tests", "docs", "infra"]

PRD_STUB = """# <Nombre del Proyecto>

> ✏️ **PRD de partida generado por `fia-harness init`.** Completa cada sección
> antes de aprobar la Fase 1 (entrevista técnica). Si dejas esta plantilla tal
> cual, el bootstrap te avisará de los campos sin confirmar.
> 📄 Si tu brief ya existe con otro nombre (p. ej. `PDR_x.md.txt`), cópialo o
> renómbralo a **`PRD.md`** en la raíz: el harness lee este archivo en M0.

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


def _absolute(path: Path) -> Path:
    try:
        return path.expanduser().resolve()
    except OSError:
        return path


def _init_failure_hint(target_dir: Path, error: OSError) -> int:
    """Mensaje claro cuando la carpeta destino no se puede preparar (v3.4.2/v3.6.1)."""
    print()
    print(f"❌ No se pudo preparar el proyecto en: {_absolute(target_dir)}")
    print(f"   Error del sistema: {error}")
    filename = str(getattr(error, "filename", "") or "").replace("\\", "/")
    print("   Pistas:")
    if "fia_harness" in filename:
        print("   - Falta un recurso del paquete instalado (instalación corrupta o versión")
        print("     antigua): reinstala o actualiza con `pip install -U fia-harness`")
        print("     (o `uvx fia-harness@latest init`).")
    else:
        print('   - Usa una ruta absoluta y local, fuera de OneDrive: '
              'fia-harness init -d "C:\\dev\\mi-proyecto"')
        print("   - Revisa la Protección contra ransomware (Carpetas controladas) y los")
        print("     permisos de escritura de la carpeta.")
    return 1


def run_init(target_dir: Path) -> int:
    _print_banner()
    try:
        return _init_project(target_dir)
    except OSError as error:
        return _init_failure_hint(target_dir, error)


def _init_project(target_dir: Path) -> int:
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

    location = _absolute(target_dir)
    print()
    print("✅ Proyecto montado. Siguientes pasos:")
    print(f"   1. Completa {location / 'PRD.md'}")
    print(f"   2. cd {location} && python bootstrap.py   (Fase M0)")
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
    init_parser.add_argument("--assets", default=None, metavar="URL|MANIFIESTO",
                             help="Descarga el pack de assets tras montar el proyecto "
                                  "(`fia assets fetch`); p. ej. una URL de UI_ASSETS.json.")

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
        "verify", help="Reporte de verificación (STATE/DEPS/EVIDENCE/PROVENANCE/RECEIPTS/RISK/SCOPE/REPRODUCTION/SEALS/SPEC).")
    verify_parser.add_argument("-d", "--dir", default=".")
    verify_parser.add_argument("--reproduce", nargs="?", const="", default=None, metavar="EV-NNN",
                               help="Reproduce evidencia (opt-in): sin valor, todas las allowlisted.")
    verify_parser.add_argument("--scope-base", default=None, metavar="REF",
                               help="Compara el scope contra una ref de git (p. ej. origin/main).")
    verify_parser.add_argument("--strict-receipts", action="store_true",
                               help="Exige recibos limpios: los dirty se verifican contra el árbol (CI).")

    receipt_parser = subparsers.add_parser(
        "receipt", help="Emite o verifica el recibo de una fase F (v3.3, regla de oro nº16).")
    receipt_sub = receipt_parser.add_subparsers(dest="receipt_command", required=True)
    receipt_create = receipt_sub.add_parser("create", help="Emite el recibo de una fase en curso.")
    receipt_create.add_argument("fase", help="Código de fase (p. ej. F9).")
    receipt_create.add_argument("--base", default=None, metavar="REF",
                                help="Punto de partida de la fase (diff REF...HEAD).")
    receipt_create.add_argument("--evidence", action="append", default=[], metavar="EV-NNN",
                                help="Evidencia referenciada (repetible).")
    receipt_create.add_argument("--tests", default="0/0", metavar="P/T",
                                help="Tests pasados/total (p. ej. 248/248).")
    receipt_create.add_argument("--lint", default="skip", choices=["pass", "fail", "skip"])
    receipt_create.add_argument("--allow-dirty", action="store_true",
                                help="Permite emitir el recibo con cambios sin commitear.")
    receipt_create.add_argument("-d", "--dir", default=".")
    receipt_verify = receipt_sub.add_parser("verify", help="Verifica el recibo de una fase.")
    receipt_verify.add_argument("fase", help="Código de fase (p. ej. F9).")
    receipt_verify.add_argument("-d", "--dir", default=".")

    route_parser = subparsers.add_parser(
        "route", help="Clasifica una tarea y propone carril Lite/Full (fail-closed, v3.3).")
    route_parser.add_argument("descripcion", help="Descripción de la tarea.")
    route_parser.add_argument("-d", "--dir", default=".",
                              help="No usado por el router (sin estado); se acepta por consistencia.")

    assets_parser = subparsers.add_parser(
        "assets", help="Manifiesto y descarga verificada de packs de assets UI (v3.5).")
    assets_sub = assets_parser.add_subparsers(dest="assets_command", required=True)
    assets_fetch = assets_sub.add_parser("fetch", help="Descarga y verifica los assets de un manifiesto.")
    assets_fetch.add_argument("manifest", nargs="?", default=None,
                              help="URL o ruta del manifiesto (por defecto: UI_ASSETS.json del proyecto).")
    assets_fetch.add_argument("-d", "--dir", default=".")
    assets_manifest = assets_sub.add_parser("manifest", help="Genera un manifiesto desde un directorio local.")
    assets_manifest.add_argument("--dir-source", required=True, metavar="DIR",
                                 help="Directorio con los assets a publicar.")
    assets_manifest.add_argument("--base-url", required=True, metavar="URL",
                                 help="URL base donde se alojarán los assets.")
    assets_manifest.add_argument("-o", "--out", default="UI_ASSETS.json", metavar="ARCHIVO")
    assets_manifest.add_argument("-d", "--dir", default=".",
                                 help="No usado al generar; se acepta por consistencia.")

    ui_parser = subparsers.add_parser(
        "ui", help="Entorno UI/UX avanzado: instalación asistida del pack (v3.6).")
    ui_sub = ui_parser.add_subparsers(dest="ui_command", required=True)
    ui_setup = ui_sub.add_parser(
        "setup", help="Descarga el pack UI/UX (o solo las recetas) con verificación SHA-256.")
    ui_setup.add_argument("--recetas", action="store_true",
                          help="Instala solo las recetas (library/UI_LIBRARY.md).")
    ui_setup.add_argument("--url", default=None, metavar="URL",
                          help="Manifiesto alternativo (por defecto: pack oficial; "
                               "también env FIA_UI_PACK_URL).")
    ui_setup.add_argument("-d", "--dir", default=".")
    ui_status = ui_sub.add_parser("status", help="Estado local del entorno UI/UX (sin red).")
    ui_status.add_argument("-d", "--dir", default=".")

    args = parser.parse_args(argv)
    target = Path(args.dir)

    if args.command == "init":
        code = run_init(target)
        if code == 0 and args.assets:
            from fia_harness.core.assets import fetch_manifest
            print()
            print(f"-> Descargando pack de assets: {args.assets}")
            return fetch_manifest(target, args.assets)
        return code
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
        return cmd_verify(target, args.reproduce, args.scope_base, args.strict_receipts)
    if args.command == "receipt":
        if args.receipt_command == "create":
            commands.cmd_receipt_create(target, args.fase, args.base, args.evidence,
                                        args.tests, args.lint, args.allow_dirty)
            return 0
        commands.cmd_receipt_verify(target, args.fase)
        return 0
    if args.command == "route":
        from fia_harness.core.router import cmd_route
        return cmd_route(args.descripcion)
    if args.command == "assets":
        from fia_harness.core.assets import cmd_assets_fetch, cmd_assets_manifest
        if args.assets_command == "fetch":
            ref = args.manifest or str(Path(args.dir) / "UI_ASSETS.json")
            return cmd_assets_fetch(Path(args.dir), ref)
        return cmd_assets_manifest(Path(args.dir_source), args.base_url, Path(args.out))
    if args.command == "ui":
        from fia_harness.core.ui import cmd_ui_setup, cmd_ui_status
        if args.ui_command == "setup":
            return cmd_ui_setup(Path(args.dir), recipes_only=args.recetas, url=args.url)
        return cmd_ui_status(Path(args.dir))

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
