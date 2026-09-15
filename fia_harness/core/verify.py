"""Verification Engine (`fia verify`, F6; gates de riesgo/calidad en v3.1).

`verify` no confía en afirmaciones del agente: inspecciona artefactos y compone el
reporte STATE / DEPENDENCIES / EVIDENCE / PROVENANCE / RISK / SEALS / SPEC SNAPSHOT.
No modifica nada y es fail-closed (exit 1 si algo no cierra).

- PROVENANCE (ADR-005): `trusted` (digests de CI verificados) vs `local`.
- RISK (v3.1): fases con señales de riesgo exigen decisión humana registrada.
- QUALITY (v3.1): avisos que **nunca** bloquean (informe TASK incompleto, riesgo futuro).
"""

from pathlib import Path

from fia_harness.core import approvals
from fia_harness.core import evidence as ev
from fia_harness.core import quality
from fia_harness.core import state as st
from fia_harness.core.console import fix_windows_console_encoding
from fia_harness.parser.markdown import load_file

SECTION_ORDER = ("STATE", "DEPENDENCIES", "EVIDENCE", "PROVENANCE", "RISK",
                 "SEALS", "SPEC SNAPSHOT")


def _finalize(sections: dict, advisories=()) -> dict:
    reasons = [f"[{name}] {error}"
               for name in SECTION_ORDER for error in sections[name]["errors"]]
    return {"sections": sections, "reasons": reasons, "advisories": list(advisories)}


def build_report(project_dir: Path) -> dict:
    """Compone el reporte sin imprimir ni salir: secciones con errores + razones."""
    sections = {name: {"errors": [], "note": ""} for name in SECTION_ORDER}
    md_text = load_file(project_dir / st.DEFAULT_FILES["progress"], required=False)
    stored = st.load_state_json(project_dir)

    if stored is None:
        sections["STATE"]["errors"].append("falta progress.json (ejecuta --sync)")
        for name in SECTION_ORDER[1:]:
            sections[name]["errors"].append("no evaluable: falta progress.json")
        return _finalize(sections)

    if not md_text:
        sections["STATE"]["errors"].append("falta PROGRESS.md")
    else:
        compiled = st.compile_state_from_md(md_text)
        if st.state_fingerprint(stored) != st.state_fingerprint(compiled):
            sections["STATE"]["errors"].append(
                "PROGRESS.md y progress.json están desincronizados (deriva)")
    if st.is_legacy_state(stored):
        sections["STATE"]["errors"].append(
            f"progress.json usa el schema legado '{st.LEGACY_SCHEMA}' (ejecuta --sync)")
    else:
        sections["STATE"]["errors"] += st.validate_state_integrity(stored)

    sections["STATE"]["errors"] += st.validate_state_structure(stored, project_dir)
    sections["STATE"]["errors"] += approvals.validate_approvals(stored, project_dir)
    sections["DEPENDENCIES"]["errors"] += st.validate_dependencies(stored)

    report = ev.evidence_report(stored, project_dir)
    with_provenance = [e for e in report if e["kind"] == "record" and not e["provenance_errors"]]
    existence_only = [e for e in report if e["kind"] in ("inline", "file")]
    trusted = [e for e in with_provenance if e["trust"] == "trusted"]
    for entry in report:
        sections["EVIDENCE"]["errors"] += entry["evidence_errors"]
        sections["PROVENANCE"]["errors"] += entry["provenance_errors"]
    sections["PROVENANCE"]["note"] = (
        f"{len(with_provenance)} con procedencia ({len(trusted)} trusted) · "
        f"{len(existence_only)} solo existencia")

    sections["RISK"]["errors"] += quality.validate_risk_decisions(stored, project_dir)
    sections["SEALS"]["errors"] += st.validate_sealed_docs(stored, project_dir)
    sections["SPEC SNAPSHOT"]["errors"] += st.validate_spec_snapshot(stored, project_dir)
    return _finalize(sections, quality.quality_advisories(stored, project_dir))


def cmd_verify(project_dir: Path) -> int:
    """`fia verify`: imprime el reporte y devuelve 0 (PASS) o 1 (FAIL).

    La sección QUALITY es informativa: sus avisos nunca cambian el exit code."""
    fix_windows_console_encoding()
    report = build_report(project_dir)
    print("FIA Verification Report")
    print()
    for name in SECTION_ORDER:
        section = report["sections"][name]
        status = "PASS" if not section["errors"] else "FAIL"
        note = f" — {section['note']}" if section["note"] else ""
        print(f"{name:<14} {status}{note}")
    advisories = report["advisories"]
    print(f"{'QUALITY':<14} " + (f"WARN — {len(advisories)} aviso(s) (no bloquean)"
                                 if advisories else "OK"))
    print()
    if not report["reasons"]:
        print("RESULT\n  PASS — merge eligible")
    else:
        print("RESULT\n  FAIL — merge blocked")
        print("\nReasons:")
        for reason in report["reasons"]:
            print(f"  {reason}")
    if advisories:
        print("\nAdvisories (no bloquean):")
        for advisory in advisories:
            print(f"  {advisory}")
    return 1 if report["reasons"] else 0
