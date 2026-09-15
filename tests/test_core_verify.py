"""Tests del Verification Engine (`fia_harness.core.verify`)."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fia_harness import cli
from fia_harness.core import commands
from fia_harness.core import evidence as ev
from fia_harness.core import state as st
from fia_harness.core import verify

VALID_MD = """# PROGRESS.md

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap | Plantillas | — | [x] Listo |
| F0 | Repo | Funcionando | — | [ ] Pendiente |

## Checkpoints de Contexto Recientes
- **M0:** Arranque completado.
"""

F0_DONE_MD = VALID_MD.replace(
    "| F0 | Repo | Funcionando | — | [ ] Pendiente |",
    "| F0 | Repo | Funcionando | — | [x] Listo |").replace(
    "## Checkpoints de Contexto Recientes\n- **M0:** Arranque completado.\n",
    "## Checkpoints de Contexto Recientes\n- **M0:** Arranque completado.\n"
    "- **F0:** Repo listo.\n    ```\n    Ran 2 tests\n    OK\n    ```\n")

F0_EV_MD = F0_DONE_MD.replace(
    "- **F0:** Repo listo.\n    ```\n    Ran 2 tests\n    OK\n    ```\n",
    "- **F0:** Repo listo.\n    Evidencia: EV-001\n")

F0_NO_EVIDENCE_MD = F0_DONE_MD.replace(
    "- **F0:** Repo listo.\n    ```\n    Ran 2 tests\n    OK\n    ```\n",
    "- **F0:** Repo listo.\n")


def _write(path, text):
    path.write_text(text, encoding="utf-8")


def _make_record(project_dir, evidence_id="EV-001"):
    stdout, stderr = b"", b"Ran 2 tests\nOK\n"
    ev.write_streams(project_dir, evidence_id, stdout, stderr)
    record = ev.create_record(
        evidence_id=evidence_id, record_type="test", source="local-run",
        command=["python", "-m", "unittest"], cwd=project_dir, exit_code=0,
        started_at="2026-09-15T10:00:00+00:00", finished_at="2026-09-15T10:00:01+00:00",
        duration_s=1.0, stdout=stdout, stderr=stderr,
        environment={"python": "3.11.15", "os": "test"})
    ev.save_record(project_dir, record)
    return record


class VerifyBase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "PROGRESS.md", F0_DONE_MD)
        _write(self.dir / "TASK-F0.md", "# TASK-F0\nInforme.\n")
        _write(self.dir / "DECISIONS.md", "# DECISIONS.md\n\n## Aprobaciones\n")
        for name in st.REQUIRED_SEALED:
            _write(self.dir / name, f"# {name}\nv1\n")
        commands.cmd_seal(self.dir, [])
        commands.cmd_sync(self.dir)

    def _status(self, report, section):
        return "PASS" if not report["sections"][section]["errors"] else "FAIL"


class ReportTests(VerifyBase):
    def test_proyecto_valido_pasa(self):
        report = verify.build_report(self.dir)
        self.assertEqual(report["reasons"], [])
        for section in verify.SECTION_ORDER:
            self.assertEqual(self._status(report, section), "PASS", section)
        self.assertIn("1 solo existencia", report["sections"]["PROVENANCE"]["note"])

    def test_evidencia_inline_no_es_procedencia(self):
        report = verify.build_report(self.dir)
        self.assertIn("0 con procedencia", report["sections"]["PROVENANCE"]["note"])

    def test_sin_progress_json_falla_y_marca_no_evaluable(self):
        (self.dir / st.STATE_FILE).unlink()
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "STATE"), "FAIL")
        self.assertEqual(self._status(report, "EVIDENCE"), "FAIL")
        self.assertTrue(any("no evaluable" in r for r in report["reasons"]), report["reasons"])

    def test_deriva_md_json_falla_state(self):
        _write(self.dir / "PROGRESS.md", F0_DONE_MD.replace("Repo listo", "Repo listo (editado)"))
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "STATE"), "FAIL")
        self.assertTrue(any("desincronizados" in r for r in report["reasons"]), report["reasons"])

    def test_artefacto_editado_a_mano_falla_state(self):
        stored = st.load_state_json(self.dir)
        stored["compiled_at"] = "2020-01-01T00:00:00"
        _write(self.dir / st.STATE_FILE, json.dumps(stored, ensure_ascii=False))
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "STATE"), "FAIL")
        self.assertTrue(any("huella" in r for r in report["reasons"]), report["reasons"])

    def test_evidencia_ausente_falla_evidence(self):
        _write(self.dir / "PROGRESS.md", F0_NO_EVIDENCE_MD)
        state = st.compile_state_from_md(F0_NO_EVIDENCE_MD)
        state = st.carry_over_aux_fields(state, st.load_state_json(self.dir))
        st.write_state(self.dir, state)
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "EVIDENCE"), "FAIL")
        self.assertEqual(self._status(report, "STATE"), "PASS")

    def test_sello_alterado_falla_seals(self):
        _write(self.dir / "SECURITY.md", "# SECURITY.md\nalterado\n")
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "SEALS"), "FAIL")
        self.assertTrue(any("SEALS" in r for r in report["reasons"]), report["reasons"])

    def test_spec_alterada_sin_aprobacion_falla_spec(self):
        _write(self.dir / "SPEC.md", "# SPEC v1\n")
        commands.cmd_approval(self.dir, "aprobar spec", "M2", "chat", "Humano")
        _write(self.dir / "SPEC.md", "# SPEC v2 alterada\n")
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "SPEC SNAPSHOT"), "FAIL")


class ProvenanceTests(VerifyBase):
    def _switch_to_ev(self, create_record=True):
        if create_record:
            _make_record(self.dir)
        _write(self.dir / "PROGRESS.md", F0_EV_MD)
        commands.cmd_sync(self.dir)

    def test_ev_valida_da_procedencia(self):
        self._switch_to_ev()
        report = verify.build_report(self.dir)
        self.assertEqual(report["reasons"], [])
        self.assertIn("1 con procedencia (0 trusted)", report["sections"]["PROVENANCE"]["note"])

    def test_ev_manipulada_falla_provenance(self):
        self._switch_to_ev()
        (self.dir / "evidence" / "EV-001.stderr.txt").write_bytes(b"OK falso\n")
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "PROVENANCE"), "FAIL")
        self.assertTrue(any("manipulado" in r for r in report["reasons"]), report["reasons"])

    def test_ev_inexistente_falla_evidence(self):
        # Estado escrito a mano (sin --sync): el registro EV-001 no existe.
        _write(self.dir / "PROGRESS.md", F0_EV_MD)
        state = st.compile_state_from_md(F0_EV_MD)
        state = st.carry_over_aux_fields(state, st.load_state_json(self.dir))
        st.write_state(self.dir, state)
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "EVIDENCE"), "FAIL")
        self.assertTrue(any("no está registrada" in r for r in report["reasons"]), report["reasons"])

    def test_digest_ci_correcto_da_trusted(self):
        self._switch_to_ev()
        record = ev.load_record(self.dir, "EV-001")
        digests = {a["name"]: a["sha256"] for a in record["artifacts"]}
        manifest = self.dir / "ci_manifest.json"
        _write(manifest, json.dumps({"evidence": "EV-001", "artifacts": digests}))
        ev.ingest_manifest(self.dir, str(manifest))
        report = verify.build_report(self.dir)
        self.assertEqual(report["reasons"], [])
        self.assertIn("1 con procedencia (1 trusted)", report["sections"]["PROVENANCE"]["note"])

    def test_digest_ci_incorrecto_falla_provenance(self):
        self._switch_to_ev()
        manifest = self.dir / "ci_manifest.json"
        _write(manifest, json.dumps({"evidence": "EV-001",
                                     "artifacts": {"EV-001.stderr.txt": "0" * 64}}))
        ev.ingest_manifest(self.dir, str(manifest))
        report = verify.build_report(self.dir)
        self.assertEqual(self._status(report, "PROVENANCE"), "FAIL")
        self.assertTrue(any("digest" in r for r in report["reasons"]), report["reasons"])


class CmdVerifyTests(VerifyBase):
    def test_cli_verify_pass(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["verify", "-d", str(self.dir)])
        self.assertEqual(code, 0)
        self.assertIn("PASS — merge eligible", out.getvalue())

    def test_cli_verify_fail_lista_razones(self):
        _write(self.dir / "SECURITY.md", "# SECURITY.md\nalterado\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["verify", "-d", str(self.dir)])
        self.assertEqual(code, 1)
        self.assertIn("FAIL — merge blocked", out.getvalue())
        self.assertIn("Reasons:", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
