"""Huellas del estado: proyección de autoridad, deriva e integridad del artefacto.

- `state_fingerprint`: huella de la **autoridad** (fases + contenido de checkpoints).
  Detecta deriva entre PROGRESS.md y progress.json y es independiente del schema,
  así que sirve para la doble lectura `harness-state/1` ↔ 3.0 (ADR-002).
- `state_sha256`: huella del artefacto completo (sin su propio campo). Detecta
  ediciones manuales o corrupción de progress.json.
"""

import hashlib
import json

_PHASE_AUTHORITY = ("id", "title", "objective", "depends_on", "depends_on_notes", "status")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def authority_projection(state: dict) -> dict:
    """Solo la autoridad del estado (fases y contenido de checkpoints): sin schema,
    sin IDs de metadata, sin timestamps y sin sellos — comparable entre schemas.
    Normaliza `None`/`''` en evidencia: los estados antiguos usaban `None`."""
    return {
        "process_phases": [{k: p.get(k) for k in _PHASE_AUTHORITY}
                           for p in state.get("process_phases", [])],
        "execution_phases": [{k: p.get(k) for k in _PHASE_AUTHORITY}
                             for p in state.get("execution_phases", [])],
        "checkpoints": [{
            "phase": c.get("phase"),
            "summary": c.get("summary"),
            "evidence": c.get("evidence") or "",
            "evidence_file": c.get("evidence_file") or None,
        } for c in state.get("checkpoints", [])],
    }


def state_fingerprint(state: dict) -> str:
    """Huella canónica de la autoridad del estado (detección de deriva MD ↔ JSON)."""
    return json.dumps(authority_projection(state), sort_keys=True, ensure_ascii=False)


def state_sha256(state: dict) -> str:
    """SHA-256 del artefacto completo, excluyendo su propia huella."""
    payload = {k: v for k, v in state.items() if k != "state_sha256"}
    return sha256_hex(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def validate_state_integrity(state: dict) -> list:
    """El artefacto debe coincidir con su huella. Los estados sin huella (legacy) no
    aplican: la migración a 3.0 la introduce."""
    stored = state.get("state_sha256")
    if not stored:
        return []
    if stored != state_sha256(state):
        return ["progress.json no coincide con su huella (state_sha256): el artefacto "
                "fue editado a mano o está corrupto. Ejecuta --sync."]
    return []
