"""Tests unitarios del Evidence Engine (`fia_harness.core.evidence`)."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fia_harness.core import evidence as ev
from fia_harness.core import state as st

VALID_MD = """# PROGRESS.md

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap | Plantillas | — | [x] Listo |
| F0 | Repo | Funcionando | — | [ ] Pendiente |

## Checkpoints de Contexto Recientes
- **M0:** Arranque completado.
"""


def _write(path, text):
    path.write_text(text, encoding="utf-8")


def _make_record(project_dir, evidence_id="EV-001", stdout=b"Ran 2 tests\nOK\n", stderr=b""):
    ev.write_streams(project_dir, evidence_id, stdout, stderr)
    record = ev.create_record(
        evidence_id=evidence_id, record_type="test", source="local-run",
        command=["python", "-m", "unittest"], cwd=project_dir, exit_code=0,
        started_at="2026-09-15T10:00:00+00:00", finished_at="2026-09-15T10:00:01+00:00",
        duration_s=1.0, stdout=stdout, stderr=stderr,
        environment={"python": "3.11.15", "os": "test"})
    ev.save_record(project_dir, record)
    return record


class StoreTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_next_id_incremental(self):
        self.assertEqual(ev.next_evidence_id(self.dir), "EV-001")
        _make_record(self.dir, "EV-001")
        self.assertEqual(ev.next_evidence_id(self.dir), "EV-002")

    def test_save_y_load(self):
        _make_record(self.dir, "EV-001")
        record = ev.load_record(self.dir, "EV-001")
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(len(ev.list_records(self.dir)), 1)

    def test_el_almacen_protege_los_artifacts_como_binarios(self):
        # Hallazgo F7: sin esto, git normaliza CRLF→LF y la cadena rompe en CI.
        _make_record(self.dir, "EV-001")
        attributes = self.dir / "evidence" / ".gitattributes"
        self.assertTrue(attributes.exists())
        self.assertEqual(attributes.read_text(encoding="utf-8"), "* -text\n")

    def test_load_inexistente(self):
        self.assertIsNone(ev.load_record(self.dir, "EV-999"))


class ValidateChainTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_cadena_integra(self):
        record = _make_record(self.dir)
        self.assertEqual(ev.validate_record(self.dir, record), [])

    def test_artifact_manipulado(self):
        record = _make_record(self.dir)
        (self.dir / "evidence" / "EV-001.stderr.txt").write_bytes(b"FAILED")
        errors = ev.validate_record(self.dir, record)
        self.assertTrue(any("manipulado" in e for e in errors), errors)

    def test_artifact_ausente(self):
        record = _make_record(self.dir)
        (self.dir / "evidence" / "EV-001.stdout.txt").unlink()
        errors = ev.validate_record(self.dir, record)
        self.assertTrue(any("no existe" in e for e in errors), errors)

    def test_digest_ci_que_no_coincide(self):
        record = _make_record(self.dir)
        record["ci"] = {"manifest": "m.json", "digests": {"EV-001.stdout.txt": "0" * 64}}
        errors = ev.validate_record(self.dir, record)
        self.assertTrue(any("digest" in e for e in errors), errors)

    def test_campos_faltantes(self):
        record = _make_record(self.dir)
        record.pop("exit_code")
        errors = ev.validate_record(self.dir, record)
        self.assertTrue(any("exit_code" in e for e in errors), errors)


class CheckpointRuleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        md = VALID_MD.replace("| F0 | Repo | Funcionando | — | [ ] Pendiente |",
                              "| F0 | Repo | Funcionando | — | [x] Listo |")
        md = md.replace("## Checkpoints de Contexto Recientes\n- **M0:** Arranque completado.\n",
                        "## Checkpoints de Contexto Recientes\n- **M0:** Arranque completado.\n"
                        "- **F0:** Repo listo.\n    Evidencia: EV-001\n")
        _write(self.dir / "PROGRESS.md", md)
        _write(self.dir / "TASK-F0.md", "# TASK-F0\n")
        self.md = md

    def _evidence_errors(self):
        errors = st.validate_state(st.compile_state_from_md(self.md), self.dir)
        return [e for e in errors if "evidencia" in e.lower() or "EV-001" in e]

    def test_evidencia_ev_valida_pasa(self):
        _make_record(self.dir)
        self.assertEqual(self._evidence_errors(), [])

    def test_evidencia_ev_inexistente_falla(self):
        self.assertTrue(any("no está registrada" in e for e in self._evidence_errors()))

    def test_evidencia_ev_manipulada_falla(self):
        _make_record(self.dir)
        (self.dir / "evidence" / "EV-001.stderr.txt").write_bytes(b"FAILED")
        self.assertTrue(any("manipulado" in e for e in self._evidence_errors()))


class IngestAndCommandTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_ingest_adjunta_digests(self):
        _make_record(self.dir)
        manifest = self.dir / "ci_manifest.json"
        manifest.write_text(json.dumps({"evidence": "EV-001",
                                        "artifacts": {"EV-001.stdout.txt": "a" * 64}}),
                            encoding="utf-8")
        self.assertEqual(ev.ingest_manifest(self.dir, str(manifest)), 0)
        record = ev.load_record(self.dir, "EV-001")
        self.assertEqual(record["ci"]["digests"]["EV-001.stdout.txt"], "a" * 64)

    def test_ingest_manifiesto_inexistente_falla(self):
        with self.assertRaises(SystemExit):
            ev.ingest_manifest(self.dir, str(self.dir / "no_existe.json"))

    def test_list_y_show(self):
        _make_record(self.dir)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ev.cmd_evidence(self.dir), 0)
        self.assertIn("EV-001", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ev.cmd_evidence(self.dir, "EV-001"), 0)
        self.assertIn("íntegra", out.getvalue())

    def test_show_inexistente_falla(self):
        with self.assertRaises(SystemExit):
            ev.cmd_evidence(self.dir, "EV-999")


if __name__ == "__main__":
    unittest.main(verbosity=2)
