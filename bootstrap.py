#!/usr/bin/env python3
"""
BOOTSTRAP.PY - Inicializador Automático de Harness para Proyectos de IA
Este script automatiza el arranque (Fase M0) de un nuevo proyecto:
1. Verifica la existencia de un PRD/MVP en la raíz.
2. Copia las plantillas de control desde `/docs` a la raíz.
3. Genera la estructura básica de carpetas (src, tests, docs, infra).
4. Crea un borrador inicial de CONTEXT.md extrayendo metadatos clave del PRD.
5. Prepara el entorno inicializando un PROGRESS.md listo para comenzar.
6. Si el PRD menciona búsqueda semántica / RAG, activa el módulo RAG_VECTOR_EXTENSION.md.
7. Genera progress.json: el estado compilado y validable que verifica el CI.
8. Emite .github/workflows/harness.yml: las Reglas de Oro como checks de merge
   (gitleaks, auditoría de dependencias, validación de estado y aprobaciones).
"""

import datetime
import json
import os
import re
import sys
import shutil
from pathlib import Path

HARNESS_VERSION = "2.0.0"

# Configuración de archivos de control obligatorios del Harness
REQUIRED_TEMPLATES = {
    "INICIO_PROYECTO.md": "INICIO_PROYECTO.md",
    "SECURITY.md": "SECURITY.md",
    "AEO_GEO_SEO.md": "AEO_GEO_SEO.md",
    "UI_UX_EXCLUSIVA.md": "UI_UX_EXCLUSIVA.md",
    "SKILLS_MCP.md": "SKILLS_MCP.md",
    "TASK_TEMPLATE.md": "TASK_TEMPLATE.md",
    "TASK_LITE_TEMPLATE.md": "TASK_LITE_TEMPLATE.md",
    "QUICKSTART_LITE.md": "QUICKSTART_LITE.md"
}

# Carpetas del proyecto estándar
DEFAULT_FOLDERS = ["src", "tests", "docs", "infra"]

# Fases de proceso del harness: fuente única para PROGRESS.md Y progress.json.
# Las dos salidas se generan de estos datos, así que nacen sincronizadas.
PROCESS_PHASES = [
    {"id": "M0", "title": "",
     "objective": "Bootstrap del harness y lectura del PRD/MVP (Fase 0)",
     "deliverable": "Plantillas activas, carpetas creadas y CONTEXT.md con el resumen del PRD",
     "depends_on": [], "depends_on_notes": "—", "status": "done"},
    {"id": "M1", "title": "",
     "objective": "Entrevista de Descubrimiento Técnico (Fase 1)",
     "deliverable": "`SECURITY.md` y `AEO_GEO_SEO.md` completados; decisiones registradas en `CONTEXT.md`",
     "depends_on": ["M0"], "depends_on_notes": "", "status": "pending"},
    {"id": "M2", "title": "",
     "objective": "Especificación Técnica (Fase 2)",
     "deliverable": "`SPEC.md` redactado y aprobado explícitamente por el humano",
     "depends_on": ["M1"], "depends_on_notes": "", "status": "pending"},
    {"id": "M3", "title": "",
     "objective": "Plan de Fases de Ejecución (Fase 3)",
     "deliverable": "Tabla de fases `F0`-`Fn` añadida más abajo, derivada de `SPEC.md`",
     "depends_on": ["M2"], "depends_on_notes": "", "status": "pending"},
]

CHECKPOINT_M0_SUMMARY = ("Estructura del proyecto configurada con éxito. Archivos del harness "
                         "activos y mapeados en la raíz. Listos para iniciar la entrevista técnica (M1).")

# Archivos de control/soporte del harness que NUNCA deben considerarse PRD en la
# búsqueda difusa: un CHANGELOG.md, un NOTES.md o un README.md suelto en la raíz
# no es un documento de negocio.
NON_PRD_FILES = {
    "README.md", "CONTEXT.md", "PROGRESS.md", "SPEC.md", "DECISIONS.md",
    "QUICK_CONTEXT.md", "PROGRESS_ARCHIVE.md", "SESSION.md", "AGENTS.md",
    "DESIGN_DIRECTION.md", "CHANGELOG.md", "CHANGELOG_FIXES.md", "TODO.md",
    "NOTES.md", "RAG_VECTOR_EXTENSION.md", "INICIO_PROYECTO.md",
    "SECURITY.md", "AEO_GEO_SEO.md", "UI_UX_EXCLUSIVA.md", "SKILLS_MCP.md",
    "TASK_TEMPLATE.md", "TASK_LITE_TEMPLATE.md", "QUICKSTART_LITE.md",
}

# Módulo de extensión opcional para proyectos con búsqueda semántica / RAG.
# bootstrap.py lo activa (lo copia de /docs a la raíz) solo si el PRD lo pide.
RAG_MODULE_NAME = "RAG_VECTOR_EXTENSION.md"
RAG_KEYWORDS = re.compile(
    r"\b(rag|embeddings?|vectorial|pgvector|pinecone|qdrant|milvus|weaviate|"
    r"chroma(?:db)?|faiss|llamaindex|langchain|b[uú]squeda\s+sem[aá]ntica|"
    r"similitud\s+sem[aá]ntica|bases?\s+de\s+datos\s+vectoria(?:l|les))\b",
    re.IGNORECASE,
)

def print_banner():
    banner = f"""
======================================================================
     🚀 IA HARNESS BOOTSTRAPPER v{HARNESS_VERSION} — FASE M0 ACTIVADA
======================================================================
    """
    print(banner)

def find_prd_file(root_dir: Path) -> Path:
    """Busca un archivo PRD, MVP, brief o especificación de requisitos en la raíz."""
    candidates = [
        "PRD.md", "prd.md", "MVP.md", "mvp.md",
        "brief.md", "BRIEF.md", "requisitos.md", "REQUISITOS.md"
    ]
    for candidate in candidates:
        path = root_dir / candidate
        if path.exists():
            return path

    # Búsqueda difusa: cualquier md en la raíz que no sea un archivo de control del
    # harness (plantillas, archivos de control, tareas TASK-*, changelogs...).
    for path in root_dir.glob("*.md"):
        if path.name in REQUIRED_TEMPLATES or path.name in NON_PRD_FILES:
            continue
        if path.name.startswith("TASK-"):
            continue
        return path

    return None

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

def extract_prd_metadata(prd_path: Path) -> dict:
    """Extrae secciones principales del PRD mediante expresiones regulares para pre-rellenar CONTEXT.md.

    Además de los valores extraídos, devuelve `unresolved`: la lista de campos para
    los que NO se encontró una sección reconocible en el PRD. bootstrap.py debe avisar
    explícitamente de estos campos en vez de dejar pasar un placeholder en silencio
    (coherente con la Regla de Oro nº2 de INICIO_PROYECTO.md: "nunca asumir en silencio").
    """
    metadata = {
        "title": None,
        "problem": "No especificado. Por favor, completa este campo.",
        "users": "No especificado. Por favor, completa este campo.",
        "features": [],
        "out_of_scope": [],
        "unresolved": [],
    }

    if not prd_path or not prd_path.exists():
        metadata["unresolved"] = ["title", "problem", "users", "features", "out_of_scope"]
        metadata["title"] = "Nuevo Proyecto"
        return metadata

    content = prd_path.read_text(encoding="utf-8")

    # Título: primer H1; si no existe, se usa el nombre de archivo como pista mejor que "Nuevo Proyecto"
    title_match = re.search(r"^#\s+(.*)", content, re.MULTILINE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()
    else:
        metadata["title"] = prd_path.stem.replace("_", " ").replace("-", " ").strip().title()
        metadata["unresolved"].append("title")

    # Extracción simple de Problema
    prob_pattern = re.search(r"(?:##|###)\s*(?:Problema|Problem|¿Por qué\?|Por qué|Introducción|Contexto)\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if prob_pattern:
        metadata["problem"] = prob_pattern.group(1).strip()
    else:
        metadata["unresolved"].append("problem")

    # Extracción simple de Usuarios
    user_pattern = re.search(r"(?:##|###)\s*(?:Usuarios|Público|Audiencia|Target|Users|A quién va dirigido)\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if user_pattern:
        metadata["users"] = user_pattern.group(1).strip()
    else:
        metadata["unresolved"].append("users")

    # Extracción simple de Características/Features (Must have)
    features_pattern = re.search(r"(?:##|###)\s*(?:Funcionalidades|Requisitos|Features|Scope|Alcance|Must Have)\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if features_pattern:
        lines = features_pattern.group(1).strip().split("\n")
        metadata["features"] = [l.strip("* - ") for l in lines if l.strip().startswith(("*", "-", "1.", "2."))]
    if not metadata["features"]:
        metadata["unresolved"].append("features")

    # Extracción simple de Fuera de alcance (Out of scope)
    out_scope_pattern = re.search(r"(?:##|###)\s*(?:Fuera de alcance|Excluido|Out of scope|Out of Scope|No incluido)\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if out_scope_pattern:
        lines = out_scope_pattern.group(1).strip().split("\n")
        metadata["out_of_scope"] = [l.strip("* - ") for l in lines if l.strip().startswith(("*", "-", "1.", "2."))]
    if not metadata["out_of_scope"]:
        metadata["unresolved"].append("out_of_scope")

    return metadata

def generate_context_file(root_dir: Path, prd_path: Path, metadata: dict):
    """Crea el archivo CONTEXT.md inicial y lo guarda en la raíz."""
    print("\n-> Generando archivo de control CONTEXT.md...")
    context_path = root_dir / "CONTEXT.md"
    
    if context_path.exists():
        print("   [.] CONTEXT.md ya existe en la raíz. Saltando generación para no sobreescribir.")
        return
        
    prd_reference = f"basado en `{prd_path.name}`" if prd_path else "creado desde plantilla vacía"
    unresolved = set(metadata.get("unresolved", []))

    def flag(campo: str, texto: str) -> str:
        if campo in unresolved:
            return f"{texto}\n\n> ⚠️ **Sin confirmar:** no se detectó esta sección en el PRD; revisar y completar a mano antes de aprobar la Fase 1."
        return texto

    title = metadata.get("title") or "Nuevo Proyecto"
    features_md = "\n".join([f"*  [ ] {f}" for f in metadata["features"]]) if metadata["features"] else "*  [ ] _(sin detectar — completar a mano)_"
    out_scope_md = "\n".join([f"*  {o}" for o in metadata["out_of_scope"]]) if metadata["out_of_scope"] else "*  Ninguno declarado aún."

    context_content = f"""# CONTEXT.md — Resumen Vivo del Proyecto

**Proyecto:** {title}
**Estado:** Activo · Generado automáticamente {prd_reference}

## 1. Visión del Negocio
### Problema que resuelve:
{flag("problem", metadata['problem'])}

### Usuario Objetivo:
{flag("users", metadata['users'])}

## 2. Alcance del MVP (Must-Have)
{flag("features", features_md)}

## 3. Fuera de Alcance (Out of Scope)
{out_scope_md}

## 4. Decisiones Confirmadas (Fase 1)
*Este bloque será rellenado automáticamente por el Agente de IA al terminar la Entrevista Técnica (Fase 1).*
*   **Stack:** Pendiente de entrevista técnica.
*   **Base de datos:** Pendiente de entrevista técnica.
*   **Seguridad / Auth:** Pendiente de entrevista técnica.
*   **Visibilidad:** Pendiente de entrevista técnica.
*   **Modo de trabajo:** Pendiente de entrevista técnica (Completo / Lite — ver `QUICKSTART_LITE.md`).

## 5. Instrucción para el Agente / Prompt de Arranque
> **Instrucción de Ingeniería de IA:** Lee este archivo como el punto de inicio de verdad absoluto del proyecto. Tu primer paso es iniciar la **Fase 1: Entrevista de Descubrimiento Técnico** ejecutando las preguntas descritas en `INICIO_PROYECTO.md` para completar la configuración de `SECURITY.md`, `AEO_GEO_SEO.md` y redactar `SPEC.md`. No programes nada todavía.
"""
    with open(context_path, "w", encoding="utf-8") as f:
        f.write(context_content)
    print("   [+] Archivo CONTEXT.md generado con éxito.")

def generate_progress_file(root_dir: Path):
    """Genera un archivo PROGRESS.md inicial en la raíz.

    Usa DOS espacios de nombres de fase, con el MISMO esquema de tabla
    (`Fase | Objetivo | Entregable | Depende de | Estado`) para que una tabla se
    pueda pegar literalmente dentro de la otra sin reformatear nada:

    - `M0`-`M3`: fases del PROCESO/harness (lectura de PRD, entrevista, SPEC.md,
      plan de fases). Son las mismas para cualquier proyecto y SÍ se conocen en el
      momento del bootstrap, así que se pre-rellenan aquí.
    - `F0`-`Fn`: fases de EJECUCIÓN del proyecto real (modelo de datos, backend,
      frontend...). Dependen por completo de `SPEC.md`, que todavía no existe en
      este punto — por eso NO se adivinan aquí. Se añaden en la Fase M3
      (`INICIO_PROYECTO.md`, sección "FASE 3 — Plan de Fases de Ejecución"),
      copiando la tabla que el agente redacta allí.

    `task_generator.py` solo genera `TASK-Fx.md` para códigos `F<N>` — las fases
    `M<N>` son pasos de descubrimiento/documentación, no tareas de código, y se
    ejecutan siguiendo `INICIO_PROYECTO.md` directamente.
    """
    print("-> Generando archivo de control PROGRESS.md...")
    progress_path = root_dir / "PROGRESS.md"

    if progress_path.exists():
        print("   [.] PROGRESS.md ya existe en la raíz. Saltando generación.")
        return

    process_rows = "\n".join(
        f"| {phase['id']} | {phase['objective']} | {phase['deliverable']} | "
        f"{', '.join(phase['depends_on']) if phase['depends_on'] else '—'} | "
        f"{'[x] Listo' if phase['status'] == 'done' else '[ ] Pendiente'} |"
        for phase in PROCESS_PHASES
    )

    progress_content = f"""# PROGRESS.md — Hoja de Ruta e Historial de Fases

**Fase activa:** M1

## Fases del Proceso (Harness — ver `INICIO_PROYECTO.md`)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
{process_rows}

## Fases de Ejecución del Proyecto (F0-Fn — se añaden en M3, derivadas de SPEC.md)

<!--
Al completar la Fase 3 (INICIO_PROYECTO.md), pega aquí la tabla de fases
resultante SIN cambiar el orden de columnas, añadiendo solo la columna Estado
(todas empiezan en "[ ] Pendiente"). Ejemplo de fila:
| F0 | Bootstrap del repo, tooling, linting, CI básico | Repo inicial funcionando | SPEC aprobado | [ ] Pendiente |
`task_generator.py` detecta automáticamente la primera fila F<N> pendiente de
esta tabla; no toca la tabla de fases M0-M3 de arriba.
-->

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |

## Checkpoints de Contexto Recientes
- **M0 (Bootstrap):** {CHECKPOINT_M0_SUMMARY}
"""
    with open(progress_path, "w", encoding="utf-8") as f:
        f.write(progress_content)
    print("   [+] Archivo PROGRESS.md generado con éxito.")


def generate_state_file(root_dir: Path, progress_path: Path):
    """Genera progress.json compilándolo del PROGRESS.md recién escrito con la MISMA
    lógica de task_generator.py (importado como módulo vecino), de modo que el
    artefacto nace sincronizado por construcción, no por duplicación de código."""
    state_path = root_dir / "progress.json"
    if state_path.exists():
        print("   [.] progress.json ya existe en la raíz. Saltando generación.")
        return
    try:
        script_dir = Path(__file__).resolve().parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        import task_generator as tg
    except ImportError:
        print("   [⚠️] task_generator.py no está junto a bootstrap.py: no se puede compilar "
              "progress.json. Cópialo a la raíz (INSTRUCCIONES, paso 2) y ejecuta "
              "`python task_generator.py --sync`.", file=sys.stderr)
        return

    state = tg.compile_state_from_md(progress_path.read_text(encoding="utf-8"),
                                     updated=datetime.date.today().isoformat())
    errors = tg.validate_state(state, root_dir)
    if errors:
        for error in errors:
            print(f"   [⚠️] {error}", file=sys.stderr)
        print("   [⚠️] El estado inicial es inválido: progress.json NO se ha generado. "
              "Corrige PROGRESS.md y ejecuta `python task_generator.py --sync`.", file=sys.stderr)
        return
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("   [+] Estado compilado y validable generado: progress.json")


GITHUB_WORKFLOW = """\
# Generado por bootstrap.py (kit FIA Harness v2). bootstrap.py nunca lo sobrescribe:
# personalízalo libremente para tu stack. Requiere task_generator.py en la raíz
# (cópialo junto a bootstrap.py según INSTRUCCIONES DE APLICACION.txt).

name: Harness — reglas de oro

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  estado:
    name: Estado del harness válido (reglas 4, 5 y 7)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Validar estado, cierre de fases y aprobaciones
        run: python task_generator.py --check

  secretos:
    name: Sin secretos en el repositorio (regla 8)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  calidad:
    name: Tests y auditoría de dependencias (regla 7)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        if: ${{ hashFiles('package.json') != '' }}
        with:
          node-version: "20"
      - name: Instalar dependencias Node
        if: ${{ hashFiles('package.json') != '' }}
        run: npm ci || npm install
      - name: Tests Node
        if: ${{ hashFiles('package.json') != '' }}
        run: npm test --if-present
      - name: Auditoría Node (falla en nivel high o superior)
        if: ${{ hashFiles('package.json') != '' }}
        run: npm audit --audit-level=high
      - uses: actions/setup-python@v5
        if: ${{ hashFiles('requirements.txt') != '' || hashFiles('pyproject.toml') != '' }}
        with:
          python-version: "3.11"
      - name: Instalar dependencias Python
        if: ${{ hashFiles('requirements.txt') != '' }}
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Tests Python
        if: ${{ hashFiles('tests/**/test_*.py') != '' }}
        run: |
          python -m pytest --version >/dev/null 2>&1 && pytest -q || python -m unittest discover -s tests -p "test_*.py" -v
      - name: Auditoría Python (falla en vulnerabilidades conocidas)
        if: ${{ hashFiles('requirements.txt') != '' }}
        run: |
          pip install pip-audit
          pip-audit -r requirements.txt
"""


def generate_github_workflow(root_dir: Path):
    """Emite .github/workflows/harness.yml: convierte las Reglas de Oro 5 (estado),
    7 (tests) y 8 (secretos/commit) en checks de merge mecánicos. Si el archivo ya
    existe, no se toca — la personalización del usuario manda."""
    workflow_path = root_dir / ".github" / "workflows" / "harness.yml"
    if workflow_path.exists():
        print("   [.] .github/workflows/harness.yml ya existe. No sobrescrito.")
        return
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(GITHUB_WORKFLOW, encoding="utf-8", newline="\n")
    print("   [+] CI de reglas de oro generado: .github/workflows/harness.yml")
    print("       (gitleaks + auditoría de dependencias + validación del estado en cada push/PR)")

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
              f"(carpeta 'PROYECTOS RAG Y VECTORIALES') antes de la Fase 2.", file=sys.stderr)


def main():
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
    if metadata.get("unresolved"):
        campo_nombre = {
            "title": "título del proyecto",
            "problem": "problema de negocio",
            "users": "usuario objetivo",
            "features": "funcionalidades must-have",
            "out_of_scope": "fuera de alcance",
        }
        print("\n[⚠️] No se pudo extraer del PRD la sección correspondiente a:")
        for campo in metadata["unresolved"]:
            print(f"     - {campo_nombre.get(campo, campo)} → CONTEXT.md quedó con un valor por defecto.")
        print("    Revisa y completa estos campos a mano en CONTEXT.md antes de aprobar la Fase 1.")

    # 3.2 Módulo de extensión RAG, solo si el PRD lo pide
    maybe_activate_rag_module(root_dir, prd_path)

    # 4. Generar archivos iniciales de control
    generate_context_file(root_dir, prd_path, metadata)
    generate_progress_file(root_dir)
    generate_state_file(root_dir, root_dir / "PROGRESS.md")
    generate_github_workflow(root_dir)

    # 5. Crear DECISIONS.md inicial si no existe (con sección de aprobaciones selladas)
    decisions_path = root_dir / "DECISIONS.md"
    if not decisions_path.exists():
        decisions_content = (
            "# DECISIONS.md — Registro de Decisiones de Arquitectura (ADR)\n\n"
            "## Registro\n"
            "*   **ADR-000:** Uso de Harness de IA basado en Capas de Contexto para el "
            "desarrollo (Fase M0, kit v" + HARNESS_VERSION + ").\n\n"
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

if __name__ == "__main__":
    main()
