"""Tests del wrapper de ejecución `fia run` (`fia_harness.core.runner`)."""

import sys
import tempfile
import unittest
from pathlib import Path

from fia_harness.core import evidence as ev
from fia_harness.core import runner


class CmdRunTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_corrida_verde_registra_evidencia(self):
        code = runner.cmd_run(self.dir, [sys.executable, "-c", "print('hola')"])
        self.assertEqual(code, 0)
        record = ev.load_record(self.dir, "EV-001")
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["source"], "local-run")
        self.assertEqual(ev.validate_record(self.dir, record), [])
        stdout = (self.dir / "evidence" / "EV-001.stdout.txt").read_text(encoding="utf-8")
        self.assertIn("hola", stdout)

    def test_corrida_roja_propaga_exit_code(self):
        code = runner.cmd_run(self.dir, [sys.executable, "-c", "import sys; sys.exit(3)"])
        self.assertEqual(code, 3)
        record = ev.load_record(self.dir, "EV-001")
        self.assertEqual(record["exit_code"], 3)

    def test_sin_comando_falla(self):
        with self.assertRaises(SystemExit):
            runner.cmd_run(self.dir, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
