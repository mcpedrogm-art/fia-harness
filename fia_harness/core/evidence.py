"""Evidence Engine: registro, almacén y validación de evidencia (F5).

Modelo decidido en F4 (`docs/EVIDENCE_CAPTURE_DECISION.md`, ADR-005): híbrido —
`fia run` opcional en local + artifacts de CI anclados por el digest de la
plataforma. Este módulo NO decide `trusted` (eso será de `verify`, F6): aquí se
crean, guardan y validan los registros y la integridad de su cadena.

Almacén: `evidence/EV-NNN.json` + artifacts `evidence/EV-NNN.<stream>.txt`.

Regla de cierre de fase: una fase F no puede cerrarse con prosa sola. Se acepta un
bloque ``` con la salida cruda (existencia), `Evidencia: <archivo>` (existencia de
archivo) o `Evidencia: EV-NNN` (procedencia + integridad verificadas).
"""

import datetime
import json
import re
import sys
from pathlib import Path

from fia_harness.core.console import fail, fix_windows_console_encoding
from fia_harness.core.fingerprints import sha256_hex

EVIDENCE_DIR = "evidence"
EVIDENCE_ID_RE = re.compile(r"^EV-\d+$")
SOURCES = ("local-run", "ci-artifact")
REQUIRED_FIELDS = ("id", "type", "source", "command", "cwd", "exit_code",
                   "started_at", "finished_at", "duration_s",
                   "stdout_sha256", "stderr_sha256", "artifacts", "environment")
# Los artifacts de evidencia son bytes exactos: su integridad ES el hash. Git no
# debe normalizar sus finales de línea (hallazgo F7: CRLF→LF rompía la cadena en CI).
GITATTRIBUTES = "* -text\n"


def evidence_dir(project_dir: Path) -> Path:
    return project_dir / EVIDENCE_DIR


def _ensure_store(directory: Path):
    """Crea el almacén y su `.gitattributes` (artifacts tratados como binarios)."""
    directory.mkdir(parents=True, exist_ok=True)
    attributes = directory / ".gitattributes"
    if not attributes.exists():
        attributes.write_text(GITATTRIBUTES, encoding="utf-8", newline="\n")


def next_evidence_id(project_dir: Path) -> str:
    numbers = []
    for path in evidence_dir(project_dir).glob("EV-*.json"):
        match = re.match(r"^EV-(\d+)\.json$", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return f"EV-{(max(numbers) + 1) if numbers else 1:03d}"


def load_record(project_dir: Path, evidence_id: str):
    path = evidence_dir(project_dir) / f"{evidence_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def list_records(project_dir: Path):
    records = []
    for path in sorted(evidence_dir(project_dir).glob("EV-*.json")):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            records.append({"id": path.stem, "type": "?", "source": "?",
                            "exit_code": "?", "command": ["<JSON inválido>"]})
    return records


def save_record(project_dir: Path, record: dict):
    directory = evidence_dir(project_dir)
    _ensure_store(directory)
    (directory / f"{record['id']}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_streams(project_dir: Path, evidence_id: str, stdout: bytes, stderr: bytes):
    directory = evidence_dir(project_dir)
    _ensure_store(directory)
    (directory / f"{evidence_id}.stdout.txt").write_bytes(stdout)
    (directory / f"{evidence_id}.stderr.txt").write_bytes(stderr)


def create_record(evidence_id: str, record_type: str, source: str, command, cwd,
                  exit_code: int, started_at: str, finished_at: str, duration_s: float,
                  stdout: bytes, stderr: bytes, environment: dict) -> dict:
    """Construye el registro EV con hashes y artifacts (los bytes se guardan aparte)."""
    artifacts = [{"name": f"{evidence_id}.{stream}.txt", "sha256": sha256_hex(data)}
                 for stream, data in (("stdout", stdout), ("stderr", stderr))]
    return {
        "id": evidence_id,
        "type": record_type,
        "source": source,
        "command": list(command),
        "cwd": str(cwd),
        "exit_code": exit_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_s": duration_s,
        "stdout_sha256": sha256_hex(stdout),
        "stderr_sha256": sha256_hex(stderr),
        "artifacts": artifacts,
        "environment": dict(environment),
    }


def validate_record(project_dir: Path, record: dict) -> list:
    """Valida el registro y su cadena: campos, artifacts presentes y hashes
    (integridad local y, si hay, digest de CI)."""
    errors = []
    evidence_id = record.get("id", "?")
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"{evidence_id}: falta el campo '{field}'")
    if record.get("source") not in SOURCES:
        errors.append(f"{evidence_id}: 'source' debe ser uno de {SOURCES}")
    directory = evidence_dir(project_dir)
    digests = (record.get("ci") or {}).get("digests", {})
    for artifact in record.get("artifacts", []):
        name = artifact.get("name", "")
        path = directory / name
        if not path.exists():
            errors.append(f"{evidence_id}: artifact '{name}' no existe")
            continue
        current = sha256_hex(path.read_bytes())
        if current != artifact.get("sha256"):
            errors.append(f"{evidence_id}: artifact '{name}' no coincide con su hash "
                          f"(manipulado, corrupto o normalizado por git; los artifacts "
                          f"deben viajar como binarios: {EVIDENCE_DIR}/.gitattributes)")
        ci_digest = digests.get(name)
        if ci_digest and current != ci_digest:
            errors.append(f"{evidence_id}: artifact '{name}' no coincide con el digest "
                          f"de CI publicado por la plataforma")
    return errors


def ingest_manifest(project_dir: Path, manifest_path: str) -> int:
    """Adjunta los digests publicados por la plataforma CI a un registro EV.

    Formato del manifiesto:
    {"evidence": "EV-001", "artifacts": {"EV-001.stdout.txt": "<sha256>", ...}}
    """
    path = Path(manifest_path)
    if not path.exists():
        fail(f"No existe el manifiesto: {manifest_path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"El manifiesto no es JSON válido: {exc}")
    evidence_id = manifest.get("evidence", "")
    if not EVIDENCE_ID_RE.match(str(evidence_id)):
        fail("El manifiesto debe indicar 'evidence': 'EV-NNN'.")
    record = load_record(project_dir, evidence_id)
    if record is None:
        fail(f"No existe la evidencia '{evidence_id}' en {EVIDENCE_DIR}/.")
    record["ci"] = {"manifest": path.name, "digests": manifest.get("artifacts", {})}
    save_record(project_dir, record)
    print(f"✅ Digests de CI adjuntados a {evidence_id}: "
          f"{len(record['ci']['digests'])} artifact(s)")
    return 0


def cmd_evidence(project_dir: Path, evidence_id=None, ingest=None) -> int:
    """`fia evidence`: lista registros, muestra uno con su cadena validada, o
    adjunta digests de CI desde un manifiesto."""
    fix_windows_console_encoding()
    if ingest:
        return ingest_manifest(project_dir, ingest)
    if evidence_id:
        record = load_record(project_dir, evidence_id)
        if record is None:
            fail(f"No existe la evidencia '{evidence_id}' en {EVIDENCE_DIR}/.")
        print(json.dumps(record, indent=2, ensure_ascii=False))
        errors = validate_record(project_dir, record)
        if errors:
            for error in errors:
                print(f"❌ {error}", file=sys.stderr)
            fail(f"Cadena de evidencia {evidence_id} inválida: {len(errors)} problema(s).")
        print(f"✅ Cadena de evidencia {evidence_id} íntegra: "
              f"{len(record.get('artifacts', []))} artifact(s) verificados.")
        return 0
    records = list_records(project_dir)
    if not records:
        print(f"Sin evidencia registrada en {EVIDENCE_DIR}/. Usa: fia run -- <comando>")
        return 0
    print("=== Evidencia registrada ===")
    for record in records:
        command = " ".join(record.get("command", []))
        print(f"{record.get('id', '?'):8} {record.get('type', '?'):6} "
              f"{record.get('source', '?'):11} exit={record.get('exit_code', '?')} "
              f"{record.get('started_at', '?')}  {command}")
    return 0


def evidence_kind(checkpoint) -> str:
    """Nivel de evidencia de un checkpoint: inline | file | record | none."""
    if checkpoint is None:
        return "none"
    if (checkpoint.get("evidence") or "").strip():
        return "inline"
    ref = checkpoint.get("evidence_file")
    if ref and EVIDENCE_ID_RE.match(str(ref)):
        return "record"
    if ref:
        return "file"
    return "none"


def trust_level(record: dict) -> str:
    """`trusted` = con digests de CI (ancla externa, ADR-005); `local` = sin ancla."""
    return "trusted" if (record.get("ci") or {}).get("digests") else "local"


def evidence_report(state: dict, project_dir: Path) -> list:
    """Nivel de evidencia por fase F cerrada, separando existencia de procedencia.

    Cada entrada: {phase, kind, trust, evidence_errors, provenance_errors}.
    Las fases cerradas sin checkpoint no aparecen (ya fallan en STATE).
    """
    checkpoints_by_phase = {c.get("phase"): c for c in state.get("checkpoints", [])}
    report = []
    for key in ("process_phases", "execution_phases"):
        for phase in state.get(key, []):
            phase_id = phase.get("id", "")
            if phase.get("status") != "done" or not phase_id.startswith("F"):
                continue
            checkpoint = checkpoints_by_phase.get(phase_id)
            if checkpoint is None:
                continue
            entry = {"phase": phase_id, "kind": evidence_kind(checkpoint), "trust": "—",
                     "evidence_errors": [], "provenance_errors": []}
            if entry["kind"] == "none":
                entry["evidence_errors"].append(
                    f"{phase_id} está cerrada sin evidencia cruda de validación: "
                    f"pega un bloque ``` con la salida de tests/build en su checkpoint, "
                    f"referencia 'Evidencia: EV-NNN' (fia run) o añade "
                    f"'Evidencia: <archivo>'. Si el proyecto es anterior a v2.1 "
                    f"(la fase se cerró sin esta regla), reábrela con "
                    f"--reopen {phase_id} --reason \"...\" y vuelve a cerrarla con su "
                    f"evidencia real (si tiene dependientes cerradas, empieza por la última).")
            elif entry["kind"] == "file":
                ref = checkpoint.get("evidence_file")
                path = project_dir / ref
                if not (path.exists() and path.stat().st_size > 0):
                    entry["evidence_errors"].append(
                        f"{phase_id}: la evidencia '{ref}' no existe o está vacía")
            elif entry["kind"] == "record":
                ref = checkpoint.get("evidence_file")
                record = load_record(project_dir, ref)
                if record is None:
                    entry["evidence_errors"].append(
                        f"{phase_id}: la evidencia '{ref}' no está registrada en "
                        f"{EVIDENCE_DIR}/ (usa: fia run -- <comando>)")
                else:
                    entry["trust"] = trust_level(record)
                    entry["provenance_errors"] = [f"{phase_id}: {e}"
                                                  for e in validate_record(project_dir, record)]
            report.append(entry)
    return report


def validate_closed_phase_evidence(state: dict, project_dir) -> list:
    """Violaciones de la regla de evidencia en fases F cerradas (existencia + cadena)."""
    return [error for entry in evidence_report(state, project_dir)
            for error in entry["evidence_errors"] + entry["provenance_errors"]]
