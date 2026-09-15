"""Comandos de estado: sync, check, seal, approval, reopen y stats.

Capa de acción sobre `core.state` (compilar/validar/persistir) y `parser.markdown`
(editar la tabla de fases). La CLI `fia` y las fachadas legacy delegan aquí, de modo
que el comportamiento es idéntico al de v2.2.
"""

import datetime
import json
import re
import sys
from pathlib import Path

from fia_harness.core import state as st
from fia_harness.core.approvals import APPROVAL_ENTRY_RE
from fia_harness.core.console import fail, fix_windows_console_encoding, warn
from fia_harness.core.reports import cmd_stats  # noqa: F401  (re-export histórico)
from fia_harness.parser.markdown import flip_phase_status, load_file


def print_errors_and_fail(errors, mensaje):
    for error in errors:
        print(f"❌ {error}", file=sys.stderr)
    fail(mensaje)


def cmd_sync(project_dir: Path):
    """--sync: compila PROGRESS.md -> progress.json tras validar. Si el estado es
    inválido, no escribe nada (fail-closed). Conserva sellos/snapshots previos."""
    fix_windows_console_encoding()
    md_text = load_file(project_dir / st.DEFAULT_FILES["progress"])
    state = st.compile_state_from_md(md_text, updated=datetime.date.today().isoformat())
    state = st.carry_over_aux_fields(state, st.load_state_json(project_dir))
    errors = st.collect_validation_errors(state, project_dir)
    if errors:
        print_errors_and_fail(
            errors,
            "Estado inválido: corrige PROGRESS.md/DECISIONS.md y vuelve a ejecutar --sync. "
            f"{st.STATE_FILE} NO se ha escrito.")
    st.write_state(project_dir, state)
    print(f"✅ Estado compilado y validado: {project_dir / st.STATE_FILE}")
    print(f"   {len(state['process_phases'])} fases de proceso · "
          f"{len(state['execution_phases'])} de ejecución · {len(state['checkpoints'])} checkpoints")


def cmd_check(project_dir: Path, state_optional: bool = False):
    """--check: valida el estado sin modificar nada. Es el comando que ejecuta el CI
    generado por bootstrap.py (.github/workflows/harness.yml). Doble lectura (ADR-002):
    acepta el schema legado `harness-state/1` con aviso, y en 3.0 verifica además la
    huella de integridad del artefacto."""
    fix_windows_console_encoding()
    md_text = load_file(project_dir / st.DEFAULT_FILES["progress"])
    compiled = st.compile_state_from_md(md_text)
    state_path = project_dir / st.STATE_FILE
    if state_path.exists():
        try:
            stored = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{st.STATE_FILE} no es JSON válido ({exc}). Ejecuta: python task_generator.py --sync")
        if st.state_fingerprint(stored) != st.state_fingerprint(compiled):
            fail(f"PROGRESS.md y {st.STATE_FILE} están desincronizados (¿edición manual sin compilar?). "
                 "Ejecuta: python task_generator.py --sync")
        if st.is_legacy_state(stored):
            warn(f"{st.STATE_FILE} usa el schema legado '{st.LEGACY_SCHEMA}': se valida tal cual. "
                 f"Ejecuta --sync para migrar a {st.SCHEMA_VERSION} (se guardará un backup .bak).")
        else:
            integrity_errors = st.validate_state_integrity(stored)
            if integrity_errors:
                print_errors_and_fail(
                    integrity_errors,
                    f"{st.STATE_FILE} no es íntegro: fue editado a mano o está corrupto. "
                    "Ejecuta --sync para regenerarlo.")
        state = stored
    elif state_optional:
        state = compiled
        warn(f"{st.STATE_FILE} no existe; validando solo sobre PROGRESS.md (--state-optional).")
    else:
        fail(f"{st.STATE_FILE} no existe. Ejecuta: python task_generator.py --sync "
             "(o usa --state-optional para validar solo sobre PROGRESS.md).")
    errors = st.collect_validation_errors(state, project_dir)
    if errors:
        print_errors_and_fail(errors, f"Estado del harness inválido: {len(errors)} problema(s).")
    print(f"✅ Estado del harness válido: {len(state.get('process_phases', []))} fases de proceso, "
          f"{len(state.get('execution_phases', []))} de ejecución, "
          f"{len(state.get('checkpoints', []))} checkpoints, aprobaciones íntegras.")


def cmd_seal(project_dir: Path, extra_names):
    """--seal: sella documentos normativos (SHA-256) en progress.json. Sin argumentos
    sella el set obligatorio (REQUIRED_SEALED); los nombres extra se añaden."""
    fix_windows_console_encoding()
    md_text = load_file(project_dir / st.DEFAULT_FILES["progress"])
    state = st.compile_state_from_md(md_text, updated=datetime.date.today().isoformat())
    state = st.carry_over_aux_fields(state, st.load_state_json(project_dir))
    targets = list(dict.fromkeys(st.REQUIRED_SEALED + list(extra_names or [])))
    sealed = dict(state.get("sealed_docs", {}))
    for name in targets:
        path = project_dir / name
        if not path.exists():
            fail(f"No se puede sellar '{name}': no existe en el proyecto.")
        sealed[name] = st.sha256_hex(path.read_bytes())
    state["sealed_docs"] = sealed
    errors = st.collect_validation_errors(state, project_dir)
    if errors:
        print_errors_and_fail(errors, "Estado inválido tras sellar; revisa y reintenta.")
    st.write_state(project_dir, state)
    print(f"✅ Documentos sellados: {', '.join(sealed.keys())}")


def cmd_approval(project_dir: Path, action: str, phase: str, ref: str, approved_by: str):
    """--approval: registra una aprobación humana con sello rastreable en DECISIONS.md
    y, si existe SPEC.md, congela su hash SHA-256 en progress.json['spec_hashes']."""
    fix_windows_console_encoding()
    decisions_path = project_dir / "DECISIONS.md"
    if not decisions_path.exists():
        fail("DECISIONS.md no existe en este proyecto; ejecuta bootstrap.py primero.")
    text = decisions_path.read_text(encoding="utf-8")
    existing = [int(n) for n in APPROVAL_ENTRY_RE.findall(text)]
    new_id = (max(existing) + 1) if existing else 1
    today = datetime.date.today().isoformat()
    parts = [f"**APPROVAL-{new_id:03d}**", f"({today})"]
    if phase:
        parts.append(f"Fase: {phase}")
    parts.append(f"Acción: {action}")
    parts.append(f"Aprobado por: {approved_by}")
    if ref:
        parts.append(f"Ref: {ref}")
    entry_line = "- " + " · ".join(parts)

    lines = text.splitlines()
    heading_index = next((i for i, l in enumerate(lines) if re.match(r"^##\s*Aprobaciones\b", l)), None)
    if heading_index is None:
        lines += ["", "## Aprobaciones", "", entry_line]
    else:
        section_end = next((i for i in range(heading_index + 1, len(lines))
                            if lines[i].startswith("## ")), len(lines))
        lines.insert(section_end, entry_line)
    decisions_path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    print(f"✅ Aprobación registrada en DECISIONS.md: APPROVAL-{new_id:03d} ({today})")
    print("   Cita este ID en el informe de la TASK (Fase L, punto 18); --check verifica que exista.")

    spec_path = project_dir / "SPEC.md"
    if spec_path.exists():
        entry = {"sha256": st.sha256_hex(spec_path.read_bytes()), "ref": ref,
                 "date": today, "phase": phase or ""}
        state = st.load_state_json(project_dir)
        if state is None and (project_dir / st.DEFAULT_FILES["progress"]).exists():
            state = st.compile_state_from_md(
                (project_dir / st.DEFAULT_FILES["progress"]).read_text(encoding="utf-8"),
                updated=today)
        if state is not None:
            state.setdefault("spec_hashes", []).append(entry)
            st.write_state(project_dir, state)
            print(f"   🔒 Snapshot de SPEC.md congelado en progress.json ({entry['sha256'][:12]}…)")
        else:
            warn("SPEC.md existe pero no se pudo registrar snapshot (falta PROGRESS.md). "
                 "Ejecuta --sync.")


def _record_reopen(project_dir: Path, phase: str, reason: str):
    """Registra la reapertura en DECISIONS.md (sección '## Reaperturas') para dejar
    rastro auditable del cambio done → in_progress."""
    decisions_path = project_dir / "DECISIONS.md"
    if not decisions_path.exists():
        warn("DECISIONS.md no existe; la reapertura no quedará registrada como decisión.")
        return
    entry = f"- **{phase}** ({datetime.date.today().isoformat()}) · Reapertura · Razón: {reason}"
    lines = decisions_path.read_text(encoding="utf-8").splitlines()
    heading = next((i for i, l in enumerate(lines) if re.match(r"^##\s*Reaperturas\b", l)), None)
    if heading is None:
        lines += ["", "## Reaperturas", "", entry]
    else:
        section_end = next((i for i in range(heading + 1, len(lines))
                            if lines[i].startswith("## ")), len(lines))
        lines.insert(section_end, entry)
    decisions_path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


def cmd_reopen(project_dir: Path, phase: str, reason: str):
    """--reopen: reabre una fase cerrada (done → in_progress) dejando constancia en
    DECISIONS.md. Fail-closed: exige motivo, fase done y sin dependientes cerrados."""
    fix_windows_console_encoding()
    if not reason or not reason.strip():
        fail("--reopen exige un motivo (--reason).")
    phase = (phase or "").upper()
    if not st.PHASE_ID_RE.match(phase):
        fail(f"Código de fase inválido para reabrir: {phase!r}")
    progress_path = project_dir / st.DEFAULT_FILES["progress"]
    md_text = load_file(progress_path)
    state = st.compile_state_from_md(md_text)
    phases = {p["id"]: p for key in ("process_phases", "execution_phases")
              for p in state.get(key, [])}
    if phase not in phases:
        fail(f"La fase {phase} no aparece en {st.DEFAULT_FILES['progress']}.")
    if phases[phase].get("status") != "done":
        fail(f"La fase {phase} no está cerrada (estado: {phases[phase].get('status')}). "
             "Solo se puede reabrir una fase done.")
    dependents = [pid for pid, p in phases.items()
                  if phase in p.get("depends_on", []) and p.get("status") == "done"]
    if dependents:
        fail(f"No se puede reabrir {phase}: {', '.join(sorted(dependents))} ya está(n) "
             "cerrada(s) y depende(n) de ella. Reabre antes esas dependencias.")
    new_md = flip_phase_status(md_text, phase, "~")
    if new_md is None:
        fail(f"No se pudo localizar la fila de {phase} en {st.DEFAULT_FILES['progress']}.")
    progress_path.write_text(new_md, encoding="utf-8")
    _record_reopen(project_dir, phase, reason)
    updated = st.carry_over_aux_fields(
        st.compile_state_from_md(new_md, updated=datetime.date.today().isoformat()),
        st.load_state_json(project_dir))
    errors = st.collect_validation_errors(updated, project_dir)
    if errors:
        print_errors_and_fail(errors, "Estado inválido tras reabrir; revisa y ejecuta --sync.")
    st.write_state(project_dir, updated)
    print(f"✅ Fase {phase} reabierta (done → in_progress). Razón: {reason}")
