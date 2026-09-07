"""Tests del empaquetado PyPI (`fia-harness init`).

Dos garantías:
1. Anti-drift: las copias dentro del paquete (`fia_harness/data/...`) deben
   ser byte-idénticas a los originales de la raíz del repo. Si alguien edita
   `bootstrap.py` y olvida sincronizar el paquete, estos tests rompen.
2. E2E: `fia-harness init` sobre una carpeta temporal produce un proyecto que
   arranca de verdad: `bootstrap.py` genera el estado y `--check` sale en verde.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "fia_harness"

TEMPLATE_NAMES = [
    "INICIO_PROYECTO.md",
    "SECURITY.md",
    "AEO_GEO_SEO.md",
    "UI_UX_EXCLUSIVA.md",
    "SKILLS_MCP.md",
    "TASK_TEMPLATE.md",
    "TASK_LITE_TEMPLATE.md",
    "QUICKSTART_LITE.md",
]


class PackageDataSyncTest(unittest.TestCase):
    """Las copias del paquete nunca divergen de los archivos reales del kit."""

    def test_scripts_match_repo_root(self):
        for name in ("bootstrap.py", "task_generator.py"):
            packaged = (PKG / "data" / "scripts" / name).read_text(encoding="utf-8")
            original = (ROOT / name).read_text(encoding="utf-8")
            self.assertEqual(packaged, original,
                             f"{name}: la copia del paquete difiere de la raíz; sincronízalas")

    def test_templates_match_repo_root(self):
        for name in TEMPLATE_NAMES:
            packaged = (PKG / "data" / "templates" / name).read_text(encoding="utf-8")
            original = (ROOT / name).read_text(encoding="utf-8")
            self.assertEqual(packaged, original,
                             f"{name}: la copia del paquete difiere de la raíz; sincronízalas")

    def test_rag_module_matches_repo_root(self):
        packaged = (PKG / "data" / "rag" / "RAG_VECTOR_EXTENSION.md").read_text(encoding="utf-8")
        original = (ROOT / "PROYECTOS RAG Y VECTORIALES" / "RAG_VECTOR_EXTENSION.md").read_text(encoding="utf-8")
        self.assertEqual(packaged, original,
                         "RAG_VECTOR_EXTENSION.md: la copia del paquete difiere de la raíz")


class InitEndToEndTest(unittest.TestCase):
    """`fia-harness init` produce un proyecto que el bootstrap arranca en verde."""

    def _run(self, cmd, cwd):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                              encoding="utf-8", env=env)

    def test_init_monta_estructura_completa(self):
        from fia_harness import cli
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            rc = cli.main(["init", "-d", str(target)])
            self.assertEqual(rc, 0)
            expected = ["docs/INICIO_PROYECTO.md", "docs/TASK_TEMPLATE.md",
                        "docs/RAG_VECTOR_EXTENSION.md", "bootstrap.py",
                        "task_generator.py", "PRD.md", "src", "tests", "infra"]
            for rel in expected:
                self.assertTrue((target / rel).exists(), f"falta {rel}")
            for name in TEMPLATE_NAMES:
                self.assertTrue((target / "docs" / name).exists(), f"falta docs/{name}")

    def test_init_es_idempotente_y_no_pisa(self):
        from fia_harness import cli
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            self.assertEqual(cli.main(["init", "-d", str(target)]), 0)
            prd = target / "PRD.md"
            prd.write_text("# Mi PRD personal\n\n## Problema\nMi problema real\n",
                           encoding="utf-8")
            self.assertEqual(cli.main(["init", "-d", str(target)]), 0)
            self.assertIn("Mi PRD personal", prd.read_text(encoding="utf-8"))

    def test_proyecto_generado_arranca_en_verde(self):
        from fia_harness import cli
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            self.assertEqual(cli.main(["init", "-d", str(target)]), 0)
            boot = self._run([sys.executable, "bootstrap.py"], target)
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)
            self.assertTrue((target / "CONTEXT.md").exists())
            self.assertTrue((target / "PROGRESS.md").exists())
            self.assertTrue((target / "progress.json").exists())
            check = self._run([sys.executable, "task_generator.py", "--check"], target)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertIn("Estado del harness válido", check.stdout)

    def test_scripts_no_rompen_con_consola_cp1252(self):
        from fia_harness import cli
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            self.assertEqual(cli.main(["init", "-d", str(target)]), 0)
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "cp1252"  # consola Windows típica
            boot = subprocess.run([sys.executable, "bootstrap.py"], cwd=target,
                                  capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)
            self.assertNotIn("UnicodeEncodeError", boot.stdout + boot.stderr)
            check = subprocess.run([sys.executable, "task_generator.py", "--check"], cwd=target,
                                   capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main()
