"""Recibo de fase (v3.3): manifiesto canónico, hash y verificación (regla #16).

Un recibo ata el contenido final de los archivos de una fase a un commit y a los
checks ejecutados en ese momento. Detecta manipulación post-cierre; **no** prueba
verdad local (la frontera local/trusted de ADR-005 se mantiene). Los archivos de
gobernanza implícitos (`scope.IMPLICIT_ALLOWED`) no entran en el manifiesto: su
integridad ya vive en `progress.json` y sus huellas.

Diseño: `docs/RECEIPT_DESIGN.md` · ADR-009.
"""

import datetime
import fnmatch
import json
from pathlib import Path

from fia_harness.adapters import git
from fia_harness.core import evidence as ev
from fia_harness.core import scope
from fia_harness.core.fingerprints import sha256_hex

RECEIPT_VERSION = "1.0"
RECEIPTS_DIR = Path("evidence") / "receipts"
MANIFEST_FIELDS = ("version", "task_ref", "mode", "commit_or_tree_ref", "dirty",
                   "files", "checks", "evidence_refs")
CHECK_VALUES = ("pass", "fail", "skip")
RECEIPT_GRANDFATHER_BEFORE = "2026-09-18"  # cierres anteriores = legacy (ADR-009)


def receipt_path(project_dir: Path, phase: str) -> Path:
    return project_dir / RECEIPTS_DIR / f"receipt-{phase.upper()}.json"


def resolve_receipt(project_dir: Path, ref, phase: str) -> Path:
    if ref:
        path = Path(ref)
        return path if path.is_absolute() else project_dir / path
    return receipt_path(project_dir, phase)


def normalize_content(data: bytes) -> bytes:
    """BOM UTF-8 fuera y CRLF→LF; los binarios (byte nulo) se hashean crudos."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    if b"\x00" in data[:8192]:
        return data
    return data.replace(b"\r\n", b"\n")


def content_sha256(path: Path) -> str:
    return sha256_hex(normalize_content(path.read_bytes()))


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def manifest_of(receipt: dict) -> dict:
    return {key: receipt.get(key) for key in MANIFEST_FIELDS}


def compute_sha256(receipt: dict) -> str:
    """Hash canónico del manifiesto (sin `generated_at` ni `receipt_sha256`)."""
    return sha256_hex(canonical_json(manifest_of(receipt)).encode("utf-8"))


def is_governance_path(path: str, project_dir: Path, repo_root: Path) -> bool:
    """True si el archivo es gobernanza implícita (no entra en el manifiesto).

    Acepta rutas relativas a la raíz del repo (caso normal) y, en proyectos cuyo
    estado vive en subcarpeta, la ruta relativa al proyecto."""
    if any(fnmatch.fnmatch(path, pattern) for pattern in scope.IMPLICIT_ALLOWED):
        return True
    try:
        relative = (repo_root / path).resolve().relative_to(project_dir.resolve()).as_posix()
    except ValueError:
        return False
    return any(fnmatch.fnmatch(relative, pattern) for pattern in scope.IMPLICIT_ALLOWED)


def build_manifest(phase: str, files, checks: dict, evidence_refs, mode: str,
                   dirty: bool, commit_ref: str) -> dict:
    return {
        "version": RECEIPT_VERSION,
        "task_ref": f"TASK-{phase.upper()}.md",
        "mode": mode,
        "commit_or_tree_ref": commit_ref,
        "dirty": bool(dirty),
        "files": sorted(files, key=lambda item: item["path"]),
        "checks": checks,
        "evidence_refs": sorted(set(evidence_refs)),
    }


def write_receipt(project_dir: Path, phase: str, manifest: dict) -> Path:
    receipt = dict(manifest)
    receipt["generated_at"] = datetime.datetime.now().replace(microsecond=0).isoformat()
    receipt["receipt_sha256"] = compute_sha256(receipt)
    path = receipt_path(project_dir, phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def _read_receipt(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_receipt(project_dir: Path, ref):
    """Carga un recibo por referencia (ruta relativa al proyecto) o None."""
    if ref is None:
        return None
    path = Path(ref)
    if not path.is_absolute():
        path = project_dir / path
    return _read_receipt(path)


def _files_against_worktree(project_dir: Path, repo_root: Path, manifest: dict):
    errors = []
    for item in manifest.get("files", []):
        path = repo_root / item.get("path", "")
        if item.get("deleted"):
            if path.exists():
                errors.append(f"debería estar borrado y existe: {item.get('path')}")
            continue
        if not path.exists():
            errors.append(f"archivo ausente: {item.get('path')}")
        elif content_sha256(path) != item.get("content_sha256"):
            errors.append(f"contenido modificado: {item.get('path')}")
    return errors


def _files_against_commit(project_dir: Path, manifest: dict):
    errors = []
    ref = manifest.get("commit_or_tree_ref")
    for item in manifest.get("files", []):
        data = git.show_file(project_dir, ref, item.get("path", ""))
        if item.get("deleted"):
            if data is not None:
                errors.append(f"debería estar borrado en {str(ref)[:12]}: {item.get('path')}")
            continue
        if data is None:
            errors.append(f"no verificable en {str(ref)[:12]}: {item.get('path')}")
        elif sha256_hex(normalize_content(data)) != item.get("content_sha256"):
            errors.append(f"contenido distinto al commit {str(ref)[:12]}: {item.get('path')}")
    return errors


def verify_phase(project_dir: Path, phase: str, ref=None, strict_dirty: bool = True):
    """Verifica un recibo: (errors, note).

    Recibo limpio: se verifica contra su commit (histórico, estable).
    Recibo `dirty` (local, sin commit): con `strict_dirty` se compara con el árbol
    de trabajo actual; sin él se aplaza la verificación estricta (nota) y solo se
    comprueban hash propio y evidencias. `fia receipt verify` es siempre estricto;
    `fia verify --strict-receipts` (CI) también."""
    phase = (phase or "").upper()
    path = resolve_receipt(project_dir, ref, phase)
    if not path.exists():
        return [f"{phase}: no existe el recibo ({path.name})"], ""
    receipt = _read_receipt(path)
    if receipt is None:
        return [f"{phase}: el recibo no es JSON válido ({path.name})"], ""
    missing = [key for key in MANIFEST_FIELDS if key not in receipt]
    if missing:
        return [f"{phase}: recibo incompleto (faltan: {', '.join(missing)})"], ""
    errors = []
    if compute_sha256(receipt) != receipt.get("receipt_sha256"):
        errors.append(f"{phase}: receipt_sha256 no coincide con el manifiesto (manipulado)")
    repo_root = git.toplevel(project_dir)
    if repo_root is None:
        errors.append(f"{phase}: se requiere un repositorio git para verificar el recibo")
        note = "sin git"
    elif receipt.get("dirty"):
        if strict_dirty:
            errors += [f"{phase}: {error}" for error in _files_against_worktree(project_dir, repo_root, receipt)]
            note = "local (dirty): verificado contra el árbol de trabajo"
        else:
            note = "local (dirty): verificación estricta pendiente de commit"
    else:
        errors += [f"{phase}: {error}" for error in _files_against_commit(project_dir, receipt)]
        note = f"verificado contra {str(receipt.get('commit_or_tree_ref'))[:12]}"
    for evidence_id in receipt.get("evidence_refs", []):
        if ev.load_record(project_dir, evidence_id) is None:
            errors.append(f"{phase}: evidencia referenciada inexistente: {evidence_id}")
    return errors, note


def validate_phase_receipts(state: dict, project_dir: Path) -> list:
    """Regla de oro #16 (barata): fases F cerradas no legacy con recibo referenciado,
    presente y con hash coherente. La verificación completa vive en
    `fia receipt verify` y en la sección RECEIPTS de `fia verify`.

    Sin `recorded_at` (p. ej. `--check --state-optional`) no se aplica: mismo
    grandfathering conservador que `quality.py`."""
    errors = []
    checkpoints = {checkpoint.get("phase"): checkpoint
                   for checkpoint in state.get("checkpoints", [])}
    for phase in state.get("execution_phases", []):
        phase_id = phase.get("id", "")
        if not phase_id.startswith("F") or phase.get("status") != "done":
            continue
        checkpoint = checkpoints.get(phase_id) or {}
        recorded = checkpoint.get("recorded_at") or ""
        if not recorded or recorded[:10] < RECEIPT_GRANDFATHER_BEFORE:
            continue
        ref = checkpoint.get("receipt_ref")
        if not ref:
            errors.append(f"{phase_id}: cerrada sin recibo (Regla de Oro nº16): emite el recibo "
                          f"con `fia receipt create {phase_id}` y añade "
                          f"'Recibo: {RECEIPTS_DIR.as_posix()}/receipt-{phase_id}.json' a su checkpoint")
            continue
        receipt = _read_receipt(resolve_receipt(project_dir, ref, phase_id))
        if receipt is None:
            errors.append(f"{phase_id}: el recibo referenciado no existe o no es JSON válido ({ref})")
            continue
        if compute_sha256(receipt) != receipt.get("receipt_sha256"):
            errors.append(f"{phase_id}: receipt_sha256 no coincide con el manifiesto (recibo manipulado)")
    return errors
