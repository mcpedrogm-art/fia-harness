"""Informe de estado del proyecto (`fia status` / `--stats`).

Se separa de `core.commands` para mantener ese módulo dentro del límite de tamaño
(criterio del plan F1: extraer cuando un módulo concreto lo necesite).
"""

from pathlib import Path

from fia_harness.core import evidence as ev
from fia_harness.core import state as st
from fia_harness.core.approvals import APPROVAL_ENTRY_RE
from fia_harness.core.console import fail, fix_windows_console_encoding, warn
from fia_harness.parser.markdown import load_file


def _count_approvals(project_dir: Path) -> int:
    decisions_path = project_dir / "DECISIONS.md"
    if not decisions_path.exists():
        return 0
    return len(APPROVAL_ENTRY_RE.findall(decisions_path.read_text(encoding="utf-8")))


def cmd_stats(project_dir: Path):
    """--stats: resumen legible del estado del proyecto (schema, fases, checkpoints,
    aprobaciones, sellos, snapshots) leído de progress.json."""
    fix_windows_console_encoding()
    state = st.load_state_json(project_dir)
    if state is None:
        md_text = load_file(project_dir / st.DEFAULT_FILES["progress"], required=False)
        if md_text:
            state = st.compile_state_from_md(md_text)
            warn(f"{st.STATE_FILE} no existe; resumen calculado desde PROGRESS.md.")
        else:
            fail(f"No hay estado que resumir: falta {st.STATE_FILE} y {st.DEFAULT_FILES['progress']}.")

    def counts(phases):
        c = {"done": 0, "in_progress": 0, "blocked": 0, "pending": 0}
        for p in phases:
            c[p.get("status", "pending")] += 1
        return c

    process = state.get("process_phases", [])
    execution = state.get("execution_phases", [])
    pc = counts(process)
    ec = counts(execution)
    next_phase = next((p["id"] for p in execution
                       if p.get("status") in ("pending", "in_progress", "blocked")), None)

    print("=== FIA HARNESS — Estado del proyecto ===")
    print(f"Schema del estado:       {st.schema_of(state) or '—'}")
    print(f"Fases de proceso (M):    {len(process):>3}  (done {pc['done']}, pendiente {pc['pending']})")
    print(f"Fases de ejecución (F):  {len(execution):>3}  (done {ec['done']}, en curso {ec['in_progress']}, "
          f"bloqueada {ec['blocked']}, pendiente {ec['pending']})")
    print(f"Próxima fase pendiente:  {next_phase or '—'}")
    print(f"Checkpoints de contexto: {len(state.get('checkpoints', []))}")
    print(f"Aprobaciones registradas:{_count_approvals(project_dir)}")
    print(f"Snapshots de SPEC.md:    {len(state.get('spec_hashes', []))}")
    print(f"Documentos sellados:     {len(state.get('sealed_docs', {}))}")
    print(f"Evidencia registrada:    {len(ev.list_records(project_dir))}")
