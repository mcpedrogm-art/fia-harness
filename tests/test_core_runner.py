"""Tests del wrapper de ejecución `fia run` (`fia_harness.core.runner`)."""

import contextlib
import io
import os
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

    def test_comando_inexistente_da_error_claro(self):
        stderr = io.StringIO()
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(stderr):
                runner.cmd_run(self.dir, ["comando-que-no-existe-xyz"])
        self.assertIn("No se encontró el comando", stderr.getvalue())

    @unittest.skipUnless(os.name == "nt", "PATHEXT es de Windows")
    def test_resuelve_cmd_de_windows(self):
        tools = self.dir / "tools"
        tools.mkdir()
        (tools / "saluda.cmd").write_text("@echo hola-desde-cmd\r\n", encoding="ascii")
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{tools}{os.pathsep}{old_path}"
        self.addCleanup(os.environ.__setitem__, "PATH", old_path)
        code = runner.cmd_run(self.dir, ["saluda"])
        self.assertEqual(code, 0)
        stdout = (self.dir / "evidence" / "EV-001.stdout.txt").read_text(encoding="utf-8")
        self.assertIn("hola-desde-cmd", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
