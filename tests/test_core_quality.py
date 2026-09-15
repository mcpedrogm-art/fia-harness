"""Tests de los gates de calidad y riesgo (`fia_harness.core.quality`, v3.1)."""

import tempfile
import unittest
from pathlib import Path

from fia_harness.core import commands
from fia_harness.core import policy
from fia_harness.core import quality
from fia_harness.core import state as st
from fia_harness.core import verify


def _write(path, text):
    path.write_text(text, encoding="utf-8")


def _phase(phase_id="F1", title="Auth y permisos", objective="login con roles", status="done"):
    return {"id": phase_id, "title": title, "objective": objective, "depends_on": [],
            "depends_on_notes": "", "status": status}


def _checkpoint(phase="F1", summary="listo", evidence="Ran 1 test\nOK",
                recorded_at="2026-09-16T10:00:00"):
    return {"id": f"CP-{phase}", "phase": phase, "summary": summary,
            "evidence": evidence, "evidence_file": None, "recorded_at": recorded_at}


def _state(phases, checkpoints):
    return {"schema_version": "3.0", "process_phases": [], "execution_phases": phases,
            "checkpoints": checkpoints}


class RiskSignalsTests(unittest.TestCase):
    def test_detecta_riesgo(self):
        signals = policy.risk_signals({"title": "Auth y permisos", "objective": "login con roles"})
        self.assertIn("auth", signals)
        self.assertIn("login", signals)

    def test_fase_benigna_no_tiene_senales(self):
        self.assertEqual(
            policy.risk_signals({"title": "Frontend core", "objective": "UI navegable"}), [])


class RiskDecisionGateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_fase_de_riesgo_sin_decision_falla(self):
        state = _state([_phase()], [_checkpoint()])
        errors = quality.validate_risk_decisions(state, self.dir)
        self.assertTrue(any("no registra" in e for e in errors), errors)

    def test_decision_citada_en_la_task_pasa(self):
        _write(self.dir / "TASK-F1.md",
               "# TASK-F1\nDecisión humana: APPROVAL-001 (revisión de auth)\n")
        state = _state([_phase()], [_checkpoint()])
        self.assertEqual(quality.validate_risk_decisions(state, self.dir), [])

    def test_decision_citada_en_el_checkpoint_pasa(self):
        state = _state([_phase()], [_checkpoint(summary="Aprobado: APPROVAL-002")])
        self.assertEqual(quality.validate_risk_decisions(state, self.dir), [])

    def test_fase_sin_riesgo_no_exige_decision(self):
        state = _state([_phase(title="Frontend", objective="UI navegable")], [_checkpoint()])
        self.assertEqual(quality.validate_risk_decisions(state, self.dir), [])

    def test_lite_con_riesgo_exige_promocion(self):
        _write(self.dir / "QUICK_CONTEXT.md", "brief")
        state = _state([_phase(status="in_progress")], [])
        errors = quality.validate_risk_decisions(state, self.dir)
        self.assertTrue(any("Modo Lite" in e for e in errors), errors)


class QualityAdvisoriesTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def _task_incompleto(self):
        _write(self.dir / "TASK-F1.md",
               "# TASK-F1\n\n## TASK-F1 — INFORME FINAL\n\n"
               "### 2. Diagnóstico o decisiones de diseño tomadas\n"
               "### 8. Tests: `X/X passed`\n"
               "### 10. Lint: OK / ERROR\n"
               "### 11. Build: OK / ERROR\n"
               "### 12. Seguridad\n")

    def _task_completo(self):
        _write(self.dir / "TASK-F1.md",
               "# TASK-F1\n\n## TASK-F1 — INFORME FINAL\n\n"
               "### 2. Diagnóstico o decisiones de diseño tomadas\n"
               "Se eligió X por Y.\n"
               "### 8. Tests: `10/10 passed`\n"
               "10/10 passed (python -m unittest)\n"
               "### 10. Lint: OK / ERROR\n"
               "OK (sin errores nuevos)\n"
               "### 11. Build: OK / ERROR\n"
               "OK\n"
               "### 12. Seguridad\nNo aplica: sin auth ni datos de usuario.\n")

    def test_informe_incompleto_avisa(self):
        self._task_incompleto()
        state = _state([_phase()], [_checkpoint()])
        advisories = quality.quality_advisories(state, self.dir)
        self.assertTrue(any("informe TASK incompleto" in a for a in advisories), advisories)

    def test_informe_completo_no_avisa(self):
        self._task_completo()
        state = _state([_phase()], [_checkpoint()])
        self.assertEqual(quality.quality_advisories(state, self.dir), [])

    def test_grandfathering_no_avisa_cierres_antiguos(self):
        self._task_incompleto()
        state = _state([_phase()], [_checkpoint(recorded_at="2026-09-15T10:00:00")])
        self.assertEqual(quality.quality_advisories(state, self.dir), [])

    def test_riesgo_pendiente_avisa(self):
        state = _state([_phase(status="pending")], [])
        advisories = quality.quality_advisories(state, self.dir)
        self.assertTrue(any("fase pendiente" in a for a in advisories), advisories)


class VerifyRiskIntegrationTests(unittest.TestCase):
    MD = """# PROGRESS.md

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap | Plantillas | — | [x] Listo |
| F1 | Auth y login | Login con roles | M0 | [x] Listo |

## Checkpoints de Contexto Recientes
- **M0:** listo.
- **F1:** login funcionando.
    ```
    Ran 3 tests
    OK
    ```
"""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "PROGRESS.md", self.MD)
        _write(self.dir / "TASK-F1.md", "# TASK-F1\nInforme: login listo.\n")
        _write(self.dir / "DECISIONS.md", "# DECISIONS.md\n\n## Aprobaciones\n")
        st.write_state(self.dir, st.compile_state_from_md(self.MD))

    def _status(self, report, section):
        return "PASS" if not report["sections"][section]["errors"] else "FAIL"

    def test_verify_falla_sin_decision_humana(self):
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "RISK"), "FAIL")
        self.assertTrue(any("[RISK]" in r for r in report["reasons"]), report["reasons"])

    def test_verify_pasa_con_aprobacion_citada(self):
        commands.cmd_approval(self.dir, "revisión humana de auth", "F1", "chat", "Humano")
        _write(self.dir / "TASK-F1.md", "# TASK-F1\nDecisión humana: APPROVAL-001\n")
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "RISK"), "PASS")
        self.assertEqual(report["reasons"], [])

    def test_los_avisos_no_bloquean(self):
        commands.cmd_approval(self.dir, "revisión humana de auth", "F1", "chat", "Humano")
        _write(self.dir / "TASK-F1.md", "# TASK-F1\nDecisión humana: APPROVAL-001\n")
        state = st.load_state_json(self.dir)
        state["checkpoints"][-1]["recorded_at"] = "2026-09-16T10:00:00"
        st.write_state(self.dir, state)
        report = verify.build_report(self.dir)
        self.assertTrue(report["advisories"])
        self.assertEqual(report["reasons"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
