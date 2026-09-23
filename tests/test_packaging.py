"""Tests del empaquetado PyPI (`fia-harness init`).

Dos garantías:
1. Anti-drift: las copias dentro del paquete (`fia_harness/data/...`) deben
   ser byte-idénticas a los originales de la raíz del repo. Si alguien edita
   `bootstrap.py` y olvida sincronizar el paquete, estos tests rompen.
2. E2E: `fia-harness init` sobre una carpeta temporal produce un proyecto que
   arranca de verdad: `bootstrap.py` genera el estado y `--check` sale en verde.
"""

import contextlib
import io
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
    "UI_RECIPES.md",
    "UI_ASSETS.json",
    "QUICKSTART_LITE.md",
    "AGENTS.md",
    "PRD_TEMPLATE.md",
    "MODELOS.md",
    "TYPESAFE_EXTENSION.md",
]


class ScriptFacadesTest(unittest.TestCase):
    """ADR-001: el paquete es la única fuente de verdad; los scripts de la raíz son
    fachadas finas que lo importan (ya no hay copias que sincronizar)."""

    def test_no_hay_copias_de_scripts_en_el_paquete(self):
        self.assertFalse((PKG / "data" / "scripts").exists(),
                         "fia_harness/data/scripts ya no debe existir (ADR-001)")

    def test_scripts_de_la_raiz_son_fachadas(self):
        for name in ("bootstrap.py", "task_generator.py"):
            content = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("from fia_harness", content, f"{name} no importa el paquete")
            self.assertLess(len(content.splitlines()), 40,
                            f"{name} dejó de ser una fachada fina")

    def test_fachadas_del_repo_coinciden_con_la_plantilla_del_paquete(self):
        from fia_harness.facades import facade_files
        for name, template in facade_files().items():
            content = (ROOT / name).read_text(encoding="utf-8")
            self.assertEqual(content.replace("\r\n", "\n").rstrip("\n"),
                             template.rstrip("\n"),
                             f"{name}: la fachada del repo difiere de la plantilla del paquete")

    def test_parser_config_se_empaqueta(self):
        self.assertTrue((PKG / "data" / "parser" / "synonyms.json").exists(),
                        "falta la config del parser PRD en el paquete (F2)")

    def test_templates_match_repo_root(self):
        for name in TEMPLATE_NAMES:
            packaged = (PKG / "data" / "templates" / name).read_text(encoding="utf-8")
            original = (ROOT / "templates" / name).read_text(encoding="utf-8")
            self.assertEqual(packaged, original,
                             f"{name}: la copia del paquete difiere de la raíz; sincronízalas")

    def test_package_data_cubre_todas_las_plantillas(self):
        """Bug real v3.5.0: `data/templates/*.md` dejó fuera UI_ASSETS.json del wheel
        y `fia init` fallaba en instalaciones de PyPI. Guardarraíl: cada plantilla
        debe estar cubierta por algún glob de `[tool.setuptools.package-data]`."""
        import fnmatch
        import re

        from fia_harness import cli

        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        block = re.search(r"\[tool\.setuptools\.package-data\](.*?)(?=\n\[|\Z)",
                          text, re.DOTALL)
        self.assertIsNotNone(block, "falta [tool.setuptools.package-data] en pyproject.toml")
        globs = re.findall(r'"([^"]+)"', block.group(1))
        self.assertTrue(globs, "package-data sin globs")
        for name in cli.TEMPLATE_NAMES:
            rel = f"data/templates/{name}"
            self.assertTrue(any(fnmatch.fnmatch(rel, pattern) for pattern in globs),
                            f"{name}: ningún glob de package-data lo incluye ({globs})")
        self.assertTrue(any(fnmatch.fnmatch(f"data/rag/{cli.RAG_NAME}", pattern)
                            for pattern in globs),
                        f"{cli.RAG_NAME}: ningún glob de package-data lo incluye")

    def test_rag_module_matches_repo_root(self):
        packaged = (PKG / "data" / "rag" / "RAG_VECTOR_EXTENSION.md").read_text(encoding="utf-8")
        original = (ROOT / "templates" / "RAG_VECTOR_EXTENSION.md").read_text(encoding="utf-8")
        self.assertEqual(packaged, original,
                         "RAG_VECTOR_EXTENSION.md: la copia del paquete difiere de la raíz")


class InitEndToEndTest(unittest.TestCase):
    """`fia-harness init` produce un proyecto que el bootstrap arranca en verde."""

    def _run(self, cmd, cwd):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        # Las fachadas de la raíz importan el paquete (ADR-001): el proyecto temporal
        # no está instalado, así que le damos el repo por PYTHONPATH.
        env["PYTHONPATH"] = str(ROOT)
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

    def test_init_con_ruta_invalida_da_error_claro(self):
        from fia_harness import cli
        with tempfile.TemporaryDirectory() as td:
            blocker = Path(td) / "archivo.txt"
            blocker.write_text("x", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["init", "-d", str(blocker / "sub")])
            self.assertEqual(code, 1)
            self.assertIn("No se pudo preparar el proyecto", out.getvalue())
            self.assertIn("-d", out.getvalue())

    def test_init_muestra_cd_con_ruta_absoluta(self):
        from fia_harness import cli
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "proyecto"
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["init", "-d", str(target)])
            self.assertEqual(code, 0)
            self.assertIn(f"cd {target.resolve()}", out.getvalue())

    def test_error_de_recurso_del_paquete_da_pista_correcta(self):
        from fia_harness import cli
        error = FileNotFoundError(2, "no such file",
                                  r"C:\cache\fia_harness\data\templates\UI_ASSETS.json")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli._init_failure_hint(Path("x"), error)
        self.assertEqual(code, 1)
        self.assertIn("recurso del paquete", out.getvalue())

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
            env["PYTHONPATH"] = str(ROOT)
            boot = subprocess.run([sys.executable, "bootstrap.py"], cwd=target,
                                  capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertEqual(boot.returncode, 0, boot.stdout + boot.stderr)
            self.assertNotIn("UnicodeEncodeError", boot.stdout + boot.stderr)
            check = subprocess.run([sys.executable, "task_generator.py", "--check"], cwd=target,
                                   capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main()
