"""Evidencia de cierre de fase (mínimo en F1; se amplía en F5 con procedencia).

Hoy verifica la existencia de evidencia cruda: una fase de ejecución (F) no puede
cerrarse con prosa sola. Exige un bloque ``` con la salida de validación o
`Evidencia: <archivo>` apuntando a un archivo existente y no vacío.

La cadena completa `claim → command → execution → result → artifact → hash`
llega en F5/F6 (Evidence + Verification Engine).

Política de migración para proyectos anteriores a v2.1 (sin esta regla): ADR-004 —
fail-closed, sin flag de escape; la recuperación es añadir la evidencia real o
reabrir la fase y volver a cerrarla con evidencia.
"""


def validate_closed_phase_evidence(state: dict, project_dir) -> list:
    """Devuelve las violaciones de la regla de evidencia cruda en fases F cerradas."""
    errors = []
    checkpoints_by_phase = {c.get("phase"): c for c in state.get("checkpoints", [])}
    for key in ("process_phases", "execution_phases"):
        for phase in state.get(key, []):
            phase_id = phase.get("id", "")
            if phase.get("status") != "done" or not phase_id.startswith("F"):
                continue
            cp = checkpoints_by_phase.get(phase_id)
            if cp is None:
                continue
            evidence = (cp.get("evidence") or "").strip()
            if evidence:
                continue
            evidence_file = cp.get("evidence_file")
            if evidence_file:
                ev_path = project_dir / evidence_file
                if ev_path.exists() and ev_path.stat().st_size > 0:
                    continue
                errors.append(f"{phase_id}: la evidencia '{evidence_file}' no existe o está vacía")
            else:
                errors.append(f"{phase_id} está cerrada sin evidencia cruda de validación: "
                              f"pega un bloque ``` con la salida de tests/build en su checkpoint "
                              f"o añade 'Evidencia: <archivo>'. Si el proyecto es anterior a "
                              f"v2.1 (la fase se cerró sin esta regla), reábrela con "
                              f"--reopen {phase_id} --reason \"...\" y vuelve a cerrarla con su "
                              f"evidencia real (si tiene dependientes cerradas, empieza por la última).")
    return errors
