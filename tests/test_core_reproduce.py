"""Tests de la reproducción de evidencia (`fia_harness.core.reproduce`, v3.2)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from fia_harness.core import evidence as ev
from fia_harness.core import reproduce
from fia_harness.core import state as st
from fia_harness.core import verify


def _write(path, text):
    path.write_text(text, encoding="utf-8")


def _make_record(project_dir, command, exit_code, stdout=b"ok\n", stderr=b""):
    ev.write_streams(project_dir, "EV-001", stdout, stderr)
    record = ev.create_record(
        evidence_id="EV-001", record_type="test", source="local-run", command=command,
        cwd=project_dir, exit_code=exit_code, started_at="t0", finished_at="t1",
        duration_s=0.1, stdout=stdout, stderr=stderr, environment={"python": "test"})
    ev.save_record(project_dir, record)
    return record


class NormalizeTests(unittest.TestCase):
    def test_normaliza_tiempos_timestamps_y_rutas(self):
        text = f"Ran 2 tests in 0.001s\n{Path.cwd()} 2026-09-15T10:00:00\n"
        out = reproduce.normalize_output(text, Path.cwd())
        self.assertIn("in <T>s", out)
        self.assertIn("<timestamp>", out)
        self.assertNotIn(str(Path.cwd()), out)


class AllowlistTests(unittest.TestCase):
    def test_sin_archivo_vacia(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(reproduce.load_allowlist(Path(d)), [])

    def test_carga_prefijos(self):
        with tempfile.TemporaryDirectory() as d:
            _write(Path(d) / "reproduce.json",
                   json.dumps({"allow_prefixes": ["python -m unittest"]}))
            self.assertEqual(reproduce.load_allowlist(Path(d)), ["python -m unittest"])

    def test_is_allowed_por_prefijo(self):
        prefix = f"{sys.executable} -m unittest"
        self.assertTrue(reproduce.is_allowed([sys.executable, "-m", "unittest"], [prefix]))
        self.assertFalse(reproduce.is_allowed(["rm", "-rf", "/"], [prefix]))


class ReproduceRecordTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "reproduce.json",
               json.dumps({"allow_prefixes": [f"{sys.executable} -c"]}))

    def test_reproduce_coincide(self):
        record = _make_record(self.dir, [sys.executable, "-c", "print('ok')"], 0)
        result = reproduce.reproduce_record(self.dir, record)
        self.assertEqual(result["status"], "reproduced", result)

    def test_mismatch_de_exit_code(self):
        record = _make_record(self.dir, [sys.executable, "-c", "print('ok')"], 1)
        result = reproduce.reproduce_record(self.dir, record)
        self.assertEqual(result["status"], "mismatch")
        self.assertIn("exit code", result["detail"])

    def test_mismatch_de_salida(self):
        record = _make_record(self.dir, [sys.executable, "-c", "print('ok')"], 0,
                              stdout=b"otra cosa\n")
        result = reproduce.reproduce_record(self.dir, record)
        self.assertEqual(result["status"], "mismatch")
        self.assertIn("stdout", result["detail"])

    def test_comando_fuera_de_allowlist_se_omite(self):
        record = _make_record(self.dir, ["rm", "-rf", "/"], 0)
        result = reproduce.reproduce_record(self.dir, record)
        self.assertEqual(result["status"], "skipped")

    def test_sin_allowlist_se_omite(self):
        (self.dir / "reproduce.json").unlink()
        record = _make_record(self.dir, [sys.executable, "-c", "print('ok')"], 0)
        result = reproduce.reproduce_record(self.dir, record)
        self.assertEqual(result["status"], "skipped")


class VerifyReproductionIntegrationTests(unittest.TestCase):
    MD = """# PROGRESS.md

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap | Plantillas | — | [x] Listo |

## Checkpoints de Contexto Recientes
- **M0:** listo.
"""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "PROGRESS.md", self.MD)
        st.write_state(self.dir, st.compile_state_from_md(self.MD))
        _write(self.dir / "reproduce.json",
               json.dumps({"allow_prefixes": [f"{sys.executable} -c"]}))

    def test_verify_sin_flag_omite_reproduccion(self):
        report = verify.build_report(self.dir)
        self.assertEqual(report["reasons"], [])
        self.assertIn("omitida", report["sections"]["REPRODUCTION"]["note"])

    def test_verify_reproduce_ok(self):
        _make_record(self.dir, [sys.executable, "-c", "print('ok')"], 0)
        report = verify.build_report(self.dir, reproduce_arg="")
        self.assertEqual(report["reasons"], [])
        self.assertIn("1 reproducida", report["sections"]["REPRODUCTION"]["note"])

    def test_verify_reproduce_mismatch_falla(self):
        _make_record(self.dir, [sys.executable, "-c", "print('ok')"], 7)
        report = verify.build_report(self.dir, reproduce_arg="")
        self.assertTrue(any("[REPRODUCTION]" in r for r in report["reasons"]),
                        report["reasons"])

    def test_verify_reproduce_id_inexistente_falla(self):
        report = verify.build_report(self.dir, reproduce_arg="EV-999")
        self.assertTrue(any("[REPRODUCTION]" in r for r in report["reasons"]),
                        report["reasons"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
