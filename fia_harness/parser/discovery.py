"""Localización del documento de entrada (PRD/MVP/brief) de un proyecto.

La búsqueda difusa excluye los archivos de control del harness: un CHANGELOG.md,
un NOTES.md o un README.md suelto en la raíz no es un documento de negocio.
"""

from pathlib import Path

# Archivos de control/soporte del harness que NUNCA deben considerarse PRD.
# Incluye los 9 nombres de REQUIRED_TEMPLATES del bootstrap (superset verificado
# por tests): una plantilla del kit nunca es PRD.
NON_PRD_FILES = {
    "README.md", "CONTEXT.md", "PROGRESS.md", "SPEC.md", "DECISIONS.md",
    "QUICK_CONTEXT.md", "PROGRESS_ARCHIVE.md", "SESSION.md", "AGENTS.md",
    "DESIGN_DIRECTION.md", "CHANGELOG.md", "CHANGELOG_FIXES.md", "TODO.md",
    "NOTES.md", "RAG_VECTOR_EXTENSION.md", "TYPESAFE_EXTENSION.md", "INICIO_PROYECTO.md",
    "SECURITY.md", "AEO_GEO_SEO.md", "UI_UX_EXCLUSIVA.md", "SKILLS_MCP.md",
    "TASK_TEMPLATE.md", "TASK_LITE_TEMPLATE.md", "QUICKSTART_LITE.md",
    "PRD_TEMPLATE.md", "MODELOS.md", "UI_RECIPES.md",
}


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
