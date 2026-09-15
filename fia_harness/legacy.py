"""Entrypoints legacy de los scripts v2.2, ahora servidos por el paquete.

`main_task_generator` reproduce exactamente la CLI de `task_generator.py` de v2.2
(argparse con flags: --sync, --check, --seal, --approval, --reopen, --stats...) para
que proyectos y CI existentes sigan funcionando sin cambios. El arranque de
proyectos vive en `generators.bootstrap.main`.
"""

import argparse
import datetime
import json
import re
from pathlib import Path

from fia_harness.core import state as st
from fia_harness.core.commands import (cmd_approval, cmd_check, cmd_reopen, cmd_seal,
                                       cmd_stats, cmd_sync, print_errors_and_fail)
from fia_harness.core.console import fail, fix_windows_console_encoding, warn
from fia_harness.core.policy import analyze_phase_requirements
from fia_harness.generators.task import _fallback_title, build_task_file, detect_lite_mode
from fia_harness.parser.markdown import (detect_next_phase, get_phase_row, is_row_done,
                                         load_file, parse_progress_table)


def main_task_generator(argv=None):
    fix_windows_console_encoding()
    parser = argparse.ArgumentParser(
        description="Generador de TASK-Fx.md y control de estado para el Harness de IA.")
    parser.add_argument("--phase", "-p", type=str, help="Código de fase (ej: F1). Si se omite, se toma la primera fase pendiente de PROGRESS.md.")
    parser.add_argument("--lite", "-l", action="store_true", help="Forzar la plantilla Modo Lite.")
    parser.add_argument("--dir", "-d", type=str, default=".", help="Directorio raíz del proyecto.")
    parser.add_argument("--sync", action="store_true", help="Compila y valida PROGRESS.md en progress.json (artefacto que verifica el CI).")
    parser.add_argument("--check", action="store_true", help="Valida el estado (progreso, TASKs, aprobaciones, sellos, snapshot de SPEC) sin modificar nada. Es lo que ejecuta el CI.")
    parser.add_argument("--state-optional", action="store_true", help="Permite --check sin progress.json (valida solo sobre PROGRESS.md).")
    parser.add_argument("--seal", nargs="*", metavar="DOC", help="Sella documentos normativos (SHA-256) en progress.json. Sin argumentos, sella el set obligatorio.")
    parser.add_argument("--approval", type=str, metavar="ACCION", help="Registra una aprobación humana con sello APPROVAL-NNN en DECISIONS.md.")
    parser.add_argument("--ref", type=str, default="", help="Referencia de la aprobación (chat, PR, reunión) para --approval.")
    parser.add_argument("--approved-by", type=str, default="Humano", help="Quién otorga la aprobación (para --approval).")
    parser.add_argument("--reopen", metavar="FASE", help="Reabre una fase cerrada (done → in_progress) dejando constancia en DECISIONS.md.")
    parser.add_argument("--reason", type=str, default="", help="Motivo de la reapertura (para --reopen).")
    parser.add_argument("--stats", action="store_true", help="Resumen del estado del proyecto (fases, checkpoints, aprobaciones, sellos, snapshots).")
    args = parser.parse_args(argv)

    project_dir = Path(args.dir)

    if args.approval:
        cmd_approval(project_dir, args.approval, args.phase, args.ref, args.approved_by)
        return
    if args.sync:
        cmd_sync(project_dir)
        return
    if args.seal is not None:
        cmd_seal(project_dir, args.seal)
        return
    if args.check:
        cmd_check(project_dir, state_optional=args.state_optional)
        return
    if args.reopen:
        cmd_reopen(project_dir, args.reopen, args.reason)
        return
    if args.stats:
        cmd_stats(project_dir)
        return

    progress_content = load_file(project_dir / st.DEFAULT_FILES["progress"])
    context_content = load_file(project_dir / st.DEFAULT_FILES["context"], required=False)

    rows = parse_progress_table(progress_content)
    if not rows:
        fail(
            f"No se pudo leer ninguna fase con formato 'F<N>'/'M<N>' en ninguna tabla de "
            f"{st.DEFAULT_FILES['progress']}. Revisa que exista una tabla Markdown con una "
            f"columna de cabecera que contenga 'Fase'."
        )

    # Auto-sincronización del artefacto de estado: PROGRESS.md es la superficie de
    # edición; si alguien lo editó a mano y diverge de progress.json, se recompila
    # y valida aquí (el CI lo verifica también con --check, sin auto-reparación).
    state_path = project_dir / st.STATE_FILE
    if state_path.exists():
        try:
            stored = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{st.STATE_FILE} no es JSON válido ({exc}). Ejecuta: python task_generator.py --sync")
        compiled = st.compile_state_from_md(progress_content)
        if st.state_fingerprint(stored) != st.state_fingerprint(compiled):
            updated_state = st.carry_over_aux_fields(compiled, stored)
            updated_state["updated"] = datetime.date.today().isoformat()
            errors = st.collect_validation_errors(updated_state, project_dir)
            if errors:
                print_errors_and_fail(
                    errors,
                    "PROGRESS.md cambió respecto a progress.json y el nuevo estado es inválido. "
                    "Corrige PROGRESS.md y ejecuta --sync.")
            st.write_state(project_dir, updated_state)
            warn("PROGRESS.md había cambiado respecto a progress.json: estado recompilado y validado.")

    phase = args.phase
    if phase:
        if re.fullmatch(r"M\d+", phase, re.IGNORECASE):
            fail(
                f"'{phase}' es una fase de PROCESO (lectura de PRD, entrevista, SPEC.md, plan "
                f"de fases), no una fase de ejecución de código. No se genera TASK_TEMPLATE para "
                f"fases M — sigue directamente los pasos de INICIO_PROYECTO.md para esa fase."
            )
        row = get_phase_row(rows, phase)
        if row is None:
            disponibles = ", ".join(r["phase"] for r in rows)
            fail(f"La fase '{phase}' no aparece en {st.DEFAULT_FILES['progress']}. Fases encontradas: {disponibles}.")
    else:
        phase = detect_next_phase(rows)
        if phase is None:
            f_rows = [r for r in rows if re.fullmatch(r"F\d+", r["phase"])]
            m_rows = [r for r in rows if re.fullmatch(r"M\d+", r["phase"])]
            if not f_rows:
                m_pending = [r["phase"] for r in m_rows if not is_row_done(r)]
                if m_pending:
                    print(f"ℹ️  Todavía no hay tabla de fases de ejecución (F#) en {st.DEFAULT_FILES['progress']}.")
                    print(f"   Quedan fases de proceso pendientes: {', '.join(m_pending)}.")
                    print("   Complétalas siguiendo INICIO_PROYECTO.md; la Fase M3 debe añadir la tabla F0-Fn.")
                else:
                    print(f"ℹ️  Las fases de proceso (M#) están cerradas pero {st.DEFAULT_FILES['progress']} "
                          f"todavía no tiene una tabla de fases de ejecución (F#). Añádela en la Fase M3 "
                          f"(ver INICIO_PROYECTO.md, sección 'FASE 3 — Plan de Fases de Ejecución').")
            else:
                print("✅ No queda ninguna fase de ejecución (F#) pendiente en PROGRESS.md. Nada que generar.")
            return
        print(f"-> Detectada siguiente fase de ejecución pendiente en PROGRESS.md: {phase}")
        row = get_phase_row(rows, phase)

    if not row["objective"]:
        warn(f"No se encontró texto de objetivo/entregable para {phase} en la tabla de PROGRESS.md; "
             f"el TASK generado lo dejará marcado como '<pendiente de completar>'.")

    is_lite = detect_lite_mode(context_content, project_dir, args.lite)

    print(f"-> Analizando requisitos de la fase {phase} ('{_fallback_title(row)}')...")
    reqs = analyze_phase_requirements(row)
    print(f"   - Seguridad: {'SÍ' if reqs['security'] else 'NO'}")
    print(f"   - Visibilidad (SEO/AEO/GEO): {'SÍ' if reqs['visibility'] else 'NO'}")
    print(f"   - UI/UX: {'SÍ' if reqs['ui_ux'] else 'NO'}")
    print("   (heurística por palabras clave: revisa manualmente si el resultado no encaja con la fase real)")

    task_content = build_task_file(project_dir, row, reqs, is_lite)

    task_filename = "TASK-QUICK.md" if is_lite else f"TASK-{phase}.md"
    task_output_path = project_dir / task_filename
    task_output_path.write_text(task_content, encoding="utf-8")

    print(f"\n🎉 Archivo de tarea generado: {task_output_path}")
    print(f"   Modo: {'Lite (TASK-QUICK.md)' if is_lite else 'Completo (' + task_filename + ')'}")
    if is_lite:
        warn("Modo Lite: TASK_LITE_TEMPLATE.md no usa el sistema de marcadores de inyección; "
             "revisa a mano las secciones 5, 6 y 8 contra SKILLS_MCP.md / UI_UX_EXCLUSIVA.md / SECURITY.md.")
