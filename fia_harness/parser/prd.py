"""Extracción de metadatos del PRD de entrada (heurística → recomendación).

Hoy es una heurística por expresiones regulares con aviso explícito de campos sin
resolver (`unresolved`). Los niveles de confianza alta/media/ninguna y la config
versionada de sinónimos llegan en F2 (Parser Engine); este módulo es su hogar.
"""

import re
from pathlib import Path

# Archivos de control/soporte del harness que NUNCA deben considerarse PRD en la
# búsqueda difusa: un CHANGELOG.md, un NOTES.md o un README.md suelto en la raíz
# no es un documento de negocio. Incluye los 9 nombres de REQUIRED_TEMPLATES del
# bootstrap (superset verificado por tests): una plantilla del kit nunca es PRD.
NON_PRD_FILES = {
    "README.md", "CONTEXT.md", "PROGRESS.md", "SPEC.md", "DECISIONS.md",
    "QUICK_CONTEXT.md", "PROGRESS_ARCHIVE.md", "SESSION.md", "AGENTS.md",
    "DESIGN_DIRECTION.md", "CHANGELOG.md", "CHANGELOG_FIXES.md", "TODO.md",
    "NOTES.md", "RAG_VECTOR_EXTENSION.md", "INICIO_PROYECTO.md",
    "SECURITY.md", "AEO_GEO_SEO.md", "UI_UX_EXCLUSIVA.md", "SKILLS_MCP.md",
    "TASK_TEMPLATE.md", "TASK_LITE_TEMPLATE.md", "QUICKSTART_LITE.md",
    "PRD_TEMPLATE.md", "MODELOS.md",
}

# Palabras clave para activar el módulo de extensión RAG/vectorial si el PRD lo pide.
RAG_KEYWORDS = re.compile(
    r"\b(rag|embeddings?|vectorial|pgvector|pinecone|qdrant|milvus|weaviate|"
    r"chroma(?:db)?|faiss|llamaindex|langchain|b[uú]squeda\s+sem[aá]ntica|"
    r"similitud\s+sem[aá]ntica|bases?\s+de\s+datos\s+vectoria(?:l|les))\b",
    re.IGNORECASE,
)


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
        if path.name in NON_PRD_FILES:
            continue
        if path.name.startswith("TASK-"):
            continue
        return path

    return None


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
