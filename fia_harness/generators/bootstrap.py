"""BOOTSTRAP.PY - Inicializador Automático de Harness para Proyectos de IA

Este módulo automatiza el arranque (Fase M0) de un nuevo proyecto:
1. Verifica la existencia de un PRD/MVP en la raíz.
2. Copia las plantillas de control desde `/docs` a la raíz.
3. Genera la estructura básica de carpetas (src, tests, docs, infra).
4. Crea un borrador inicial de CONTEXT.md extrayendo metadatos clave del PRD.
5. Prepara el entorno inicializando un PROGRESS.md listo para comenzar.
6. Si el PRD menciona búsqueda semántica / RAG, activa el módulo RAG_VECTOR_EXTENSION.md.
7. Genera progress.json: el estado compilado y validable que verifica el CI.
8. Emite .github/workflows/harness.yml: las Reglas de Oro como checks de merge
   (gitleaks, auditoría de dependencias, validación de estado y aprobaciones).

En v3 la lógica vive en el paquete (ADR-001): el `bootstrap.py` de la raíz es una
fachada fina que delega aquí.
"""

import datetime
import json
import shutil
import sys
from pathlib import Path

from fia_harness import __version__
from fia_harness.core import state as st
from fia_harness.core.console import fix_windows_console_encoding
from fia_harness.generators import scaffold
from fia_harness.parser.prd import RAG_KEYWORDS, extract_prd_metadata, find_prd_file

# Configuración de archivos de control obligatorios del Harness
REQUIRED_TEMPLATES = {
    "INICIO_PROYECTO.md": "INICIO_PROYECTO.md",
    "SECURITY.md": "SECURITY.md",
    "AEO_GEO_SEO.md": "AEO_GEO_SEO.md",
    "UI_UX_EXCLUSIVA.md": "UI_UX_EXCLUSIVA.md",
    "SKILLS_MCP.md": "SKILLS_MCP.md",
    "TASK_TEMPLATE.md": "TASK_TEMPLATE.md",
    "TASK_LITE_TEMPLATE.md": "TASK_LITE_TEMPLATE.md",
    "UI_RECIPES.md": "UI_RECIPES.md",
    "UI_ASSETS.json": "UI_ASSETS.json",
    "QUICKSTART_LITE.md": "QUICKSTART_LITE.md",
    "AGENTS.md": "AGENTS.md",
}

# Carpetas del proyecto estándar
DEFAULT_FOLDERS = ["src", "tests", "docs", "infra"]

# Módulo de extensión opcional para proyectos con búsqueda semántica / RAG.
# bootstrap.py lo activa (lo copia de /docs a la raíz) solo si el PRD lo pide.
RAG_MODULE_NAME = "RAG_VECTOR_EXTENSION.md"


def print_banner():
    banner = f"""
======================================================================
     🚀 IA HARNESS BOOTSTRAPPER v{__version__} — FASE M0 ACTIVADA
======================================================================
    """
    print(banner)


def create_directory_structure(root_dir: Path):
    """Crea la estructura de carpetas estándar si no existe."""
    print("-> Creando estructura de directorios del proyecto...")
    for folder in DEFAULT_FOLDERS:
        folder_path = root_dir / folder
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"   [+] Creada carpeta: /{folder}")
        else:
            print(f"   [.] Ya existe carpeta: /{folder}")


def copy_templates_to_active(root_dir: Path, docs_dir: Path):
    """Copia y activa los archivos de plantilla desde /docs hacia sus ubicaciones finales."""
    print("\n-> Buscando y copiando plantillas del Harness...")
    if not docs_dir.exists():
        print(f"❌ Error: La carpeta de documentación base '/docs' no existe en {docs_dir.absolute()}", file=sys.stderr)
        print("Asegúrate de copiar tu repositorio de plantillas/harness antes de ejecutar el bootstrap.", file=sys.stderr)
        sys.exit(1)

    for template_filename, target_filename in REQUIRED_TEMPLATES.items():
        source_path = docs_dir / template_filename
        target_path = root_dir / target_filename

        if source_path.exists():
            if not target_path.exists():
                shutil.copy2(source_path, target_path)
                print(f"   [+] Copiado y activado: {target_filename}")
            else:
                print(f"   [.] Ya existe en raíz (no sobrescrito): {target_filename}")
        else:
            # Si el archivo ya está en la raíz, lo damos por bueno
            if target_path.exists():
                print(f"   [.] {target_filename} ya está presente en la raíz.")
            else:
                print(f"   [⚠️] Alerta: No se encontró la plantilla {template_filename} en /docs", file=sys.stderr)


def generate_state_file(root_dir: Path, progress_path: Path):
    """Genera progress.json compilándolo del PROGRESS.md recién escrito con la MISMA
    lógica de core.state, de modo que el artefacto nace sincronizado por construcción,
    no por duplicación de código."""
    state_path = root_dir / "progress.json"
    if state_path.exists():
        print("   [.] progress.json ya existe en la raíz. Saltando generación.")
        return

    state = st.compile_state_from_md(progress_path.read_text(encoding="utf-8"),
                                     updated=datetime.date.today().isoformat())
    # Sellar los documentos normativos (SHA-256) desde M0: el CI los verifica en
    # cada --check para que el agente no pueda relajar sus propias reglas en silencio.
    state["sealed_docs"] = st.compute_doc_hashes(root_dir, st.REQUIRED_SEALED)
    errors = (st.validate_state(state, root_dir)
              + st.validate_sealed_docs(state, root_dir)
              + st.validate_spec_snapshot(state, root_dir))
    if errors:
        for error in errors:
            print(f"   [⚠️] {error}", file=sys.stderr)
        print("   [⚠️] El estado inicial es inválido: progress.json NO se ha generado. "
              "Corrige PROGRESS.md y ejecuta `python task_generator.py --sync`.", file=sys.stderr)
        return
    st.write_state(root_dir, state)
    print("   [+] Estado compilado y validable generado: progress.json")


def maybe_activate_rag_module(root_dir: Path, prd_path: Path):
    """Si el PRD menciona búsqueda semántica / RAG / bases vectoriales, activa el
    módulo de extensión copiándolo de /docs a la raíz. Si el PRD lo pide pero el
    módulo no está en /docs, lo avisa explícitamente (Regla de Oro nº2: nunca
    asumir en silencio) para que se copie desde el kit maestro antes de la Fase 2,
    donde `INICIO_PROYECTO.md` lo exige en SPEC.md."""
    if not prd_path or not prd_path.exists():
        return

    if not RAG_KEYWORDS.search(prd_path.read_text(encoding="utf-8")):
        return

    print(f"\n[✓] El PRD menciona búsqueda semántica / RAG / datos vectoriales.")
    target = root_dir / RAG_MODULE_NAME
    source = root_dir / "docs" / RAG_MODULE_NAME

    if target.exists():
        print(f"   [.] {RAG_MODULE_NAME} ya está presente en la raíz.")
        return
    if source.exists():
        shutil.copy2(source, target)
        print(f"   [+] Módulo de extensión RAG copiado y activado: {RAG_MODULE_NAME}")
        print("       Resume sus decisiones en SPEC.md (Fase 2, punto 12 de INICIO_PROYECTO.md).")
    else:
        print(f"   [⚠️] {RAG_MODULE_NAME} no está en /docs. Cópialo desde el kit maestro "
              f"(carpeta `templates/` del repo de FIA Harness) antes de la Fase 2.", file=sys.stderr)


def main():
    fix_windows_console_encoding()
    print_banner()
    root_dir = Path(".")
    docs_dir = root_dir / "docs"

    # 1. Crear carpetas base
    create_directory_structure(root_dir)

    # 2. Copiar archivos del Harness desde /docs a la raíz
    copy_templates_to_active(root_dir, docs_dir)

    # 3. Detectar archivo de negocio (PRD / MVP)
    prd_path = find_prd_file(root_dir)
    if prd_path:
        print(f"\n[✓] PRD/MVP del cliente detectado en: `{prd_path.name}`")
        metadata = extract_prd_metadata(prd_path)
    else:
        print("\n[⚠️] No se detectó ningún PRD.md o MVP.md en la raíz del proyecto.")
        print("    Se generará un CONTEXT.md con placeholders vacíos.")
        metadata = {
            "title": "Nuevo Proyecto",
            "problem": "Escribe aquí el problema de negocio que soluciona tu producto...",
            "users": "Escribe aquí quiénes serán los usuarios finales del sistema...",
            "features": [],
            "out_of_scope": [],
            "unresolved": ["title", "problem", "users", "features", "out_of_scope"],
        }

    # 3.1 Regla de oro nº2 (INICIO_PROYECTO.md): "nunca asumir en silencio".
    #     Si algún campo se rellenó con un valor por defecto/heurístico, se avisa
    #     explícitamente aquí en vez de dejarlo pasar como si fuera dato real.
    campo_nombre = {
        "title": "título del proyecto",
        "problem": "problema de negocio",
        "users": "usuario objetivo",
        "features": "funcionalidades must-have",
        "out_of_scope": "fuera de alcance",
    }
    if metadata.get("unresolved"):
        print("\n[⚠️] No se pudo extraer del PRD la sección correspondiente a:")
        for campo in metadata["unresolved"]:
            print(f"     - {campo_nombre.get(campo, campo)} → CONTEXT.md quedó con un valor por defecto.")
        print("    Revisa y completa estos campos a mano en CONTEXT.md antes de aprobar la Fase 1.")

    # 3.1.b Confianza media (F2): se detectó por heurística, no por encabezado exacto.
    media = [campo for campo, conf in (metadata.get("confidence") or {}).items()
             if (conf or {}).get("level") == "media"]
    if media:
        print("\n[⚠️] Campos detectados con confianza media (heurística; revisar antes de aprobar la Fase 1):")
        for campo in media:
            print(f"     - {campo_nombre.get(campo, campo)} → {metadata['confidence'][campo].get('method', '')}")

    # 3.2 Módulo de extensión RAG, solo si el PRD lo pide
    maybe_activate_rag_module(root_dir, prd_path)

    # 4. Generar archivos iniciales de control
    scaffold.generate_context_file(root_dir, prd_path, metadata)
    scaffold.generate_progress_file(root_dir)
    generate_state_file(root_dir, root_dir / "PROGRESS.md")
    scaffold.generate_github_workflow(root_dir)

    # 5. Crear DECISIONS.md inicial si no existe (con sección de aprobaciones selladas)
    decisions_path = root_dir / "DECISIONS.md"
    if not decisions_path.exists():
        decisions_content = (
            "# DECISIONS.md — Registro de Decisiones de Arquitectura (ADR)\n\n"
            "## Registro\n"
            "*   **ADR-000:** Uso de Harness de IA basado en Capas de Contexto para el "
            "desarrollo (Fase M0, kit v" + __version__ + ").\n\n"
            "## Aprobaciones\n\n"
            "*Registra aquí cada aprobación humana con: "
            "`python task_generator.py --approval \"acción aprobada\" --phase F2 --ref \"chat/PR\"`. "
            "Cada TASK que use capacidades externas debe citar su identificador APPROVAL-NNN "
            "en el informe final (Fase L, punto 18); `task_generator.py --check` verifica que "
            "todo identificador citado exista aquí.*\n"
        )
        with open(decisions_path, "w", encoding="utf-8") as f:
            f.write(decisions_content)
        print("   [+] Archivo DECISIONS.md inicial generado (con sección de Aprobaciones).")

    print("\n🎉 ¡Bootstrap del Harness completado con éxito!")
    print("👉 Próximo paso: Alimenta al agente con este repositorio. El agente leerá CONTEXT.md y comenzará la Fase 1.")
