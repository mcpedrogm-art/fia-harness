"""Sellado de documentos normativos (SHA-256) y su verificación.

Un documento sellado no puede cambiar sin un nuevo `--seal`: es el anti-tamper más
fuerte del kit junto al snapshot de SPEC.md (que vive en `core.state`).
"""

from pathlib import Path

from fia_harness.core.fingerprints import sha256_hex

# Documentos normativos que el CI exige sellados (SHA-256 en progress.json).
# Si el agente los edita para relajar sus propias reglas, --check lo detecta.
REQUIRED_SEALED = ["INICIO_PROYECTO.md", "SECURITY.md", "TASK_TEMPLATE.md"]


def compute_doc_hashes(project_dir: Path, names) -> dict:
    """Devuelve {nombre: sha256} de los documentos existentes del proyecto."""
    hashes = {}
    for name in names:
        path = project_dir / name
        if path.exists():
            hashes[name] = sha256_hex(path.read_bytes())
    return hashes


def validate_sealed_docs(state: dict, project_dir: Path):
    """Los documentos normativos sellados no pueden haber cambiado sin un nuevo
    --seal. Si el documento no está presente en el proyecto, no aplica (proyectos
    no bootstrapeados o docs retirados). Si está y no está sellado → violación."""
    errors = []
    sealed = state.get("sealed_docs", {})
    for name in REQUIRED_SEALED:
        path = project_dir / name
        if not path.exists():
            continue
        if name not in sealed:
            errors.append(f"Documento normativo '{name}' no sellado "
                          f"(ejecuta: python task_generator.py --seal)")
            continue
        if sha256_hex(path.read_bytes()) != sealed[name]:
            errors.append(f"'{name}' cambió desde el sellado: revisa el cambio "
                          f"y vuelve a sellarlo (--seal)")
    return errors
