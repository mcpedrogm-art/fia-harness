"""Tests de la CLI `fia` (`fia_harness.cli`): subcomandos y fachadas generadas."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from fia_harness import cli


class InitTests(unittest.TestCase):
    def test_init_escribe_fachadas_que_importan_el_paquete(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            self.assertEqual(cli.main(["init", "-d", str(target)]), 0)
            for name in ("bootstrap.py", "task_generator.py"):
                content = (target / name).read_text(encoding="utf-8")
                self.assertIn("from fia_harness", content)
                self.assertIn("pip install fia-harness", content)

    def test_init_no_pisa_fachadas_existentes(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            (target / "bootstrap.py").write_text("# mio\n", encoding="utf-8")
            self.assertEqual(cli.main(["init", "-d", str(target)]), 0)
            self.assertEqual((target / "bootstrap.py").read_text(encoding="utf-8"), "# mio\n")


class SubcommandTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        (self.dir / "PROGRESS.md").write_text(
            "# P\n\n| Fase | Objetivo | Entregable | Depende de | Estado |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| M0 | Bootstrap | X | — | [x] Listo |\n"
            "| F0 | Repo | Y | — | [ ] Pendiente |\n\n"
            "## Checkpoints de Contexto Recientes\n- **M0:** listo.\n",
            encoding="utf-8")

    def test_sync_y_check(self):
        self.assertEqual(cli.main(["sync", "-d", str(self.dir)]), 0)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["check", "-d", str(self.dir)]), 0)
        self.assertIn("válido", out.getvalue())

    def test_status(self):
        cli.main(["sync", "-d", str(self.dir)])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["status", "-d", str(self.dir)]), 0)
        self.assertIn("Estado del proyecto", out.getvalue())

    def test_seal_y_approve(self):
        (self.dir / "DECISIONS.md").write_text("# D\n\n## Aprobaciones\n", encoding="utf-8")
        for name in ("INICIO_PROYECTO.md", "SECURITY.md", "TASK_TEMPLATE.md"):
            (self.dir / name).write_text(f"# {name}\n", encoding="utf-8")
        self.assertEqual(cli.main(["seal", "-d", str(self.dir)]), 0)
        self.assertEqual(
            cli.main(["approve", "aprobar spec", "--phase", "M2", "-d", str(self.dir)]), 0)
        text = (self.dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("APPROVAL-001", text)

    def test_reopen_exige_reason(self):
        with self.assertRaises(SystemExit):
            cli.main(["reopen", "F0", "-d", str(self.dir)])

    def test_task_genera_archivo(self):
        root = Path(__file__).resolve().parent.parent
        for name in ("TASK_TEMPLATE.md", "SECURITY.md", "AEO_GEO_SEO.md", "UI_UX_EXCLUSIVA.md"):
            (self.dir / name).write_text((root / name).read_text(encoding="utf-8"),
                                         encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["task", "-p", "F0", "-d", str(self.dir)]), 0)
        self.assertTrue((self.dir / "TASK-F0.md").exists())

    def test_run_registra_evidencia_y_evidence_la_lista(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["run", "-d", str(self.dir), "--",
                             sys.executable, "-c", "print('hola')"])
        self.assertEqual(code, 0)
        self.assertIn("EV-001", out.getvalue())
        self.assertTrue((self.dir / "evidence" / "EV-001.json").exists())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["evidence", "-d", str(self.dir)]), 0)
        self.assertIn("EV-001", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
