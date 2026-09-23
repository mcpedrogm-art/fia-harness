"""Tests unitarios del bootstrap y del scaffold (`fia_harness.generators`)."""

import json
import tempfile
import unittest
from pathlib import Path

from fia_harness.generators import bootstrap, scaffold


class ScaffoldTests(unittest.TestCase):
    def test_generate_progress_file_es_idempotente(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            scaffold.generate_progress_file(d)
            first = (d / "PROGRESS.md").read_text(encoding="utf-8")
            scaffold.generate_progress_file(d)  # no sobrescribe
            self.assertEqual(first, (d / "PROGRESS.md").read_text(encoding="utf-8"))
            self.assertIn("| M0 |", first)
            self.assertIn("[x] Listo |", first)

    def test_generate_github_workflow_instala_el_paquete(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            scaffold.generate_github_workflow(d)
            wf = (d / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
            self.assertIn("pip install fia-harness", wf)
            self.assertIn("fia verify", wf)

    def test_generate_github_workflow_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            wf = d / ".github" / "workflows" / "harness.yml"
            wf.parent.mkdir(parents=True)
            wf.write_text("custom", encoding="utf-8")
            scaffold.generate_github_workflow(d)
            self.assertEqual(wf.read_text(encoding="utf-8"), "custom")

    def test_generate_github_workflow_detecta_stack_en_subcarpetas(self):
        """El CI generado no se salta pasos en silencio: detecta el stack en
        cualquier subcarpeta (monorepo) y avisa con ::warning:: si no lo encuentra."""
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            scaffold.generate_github_workflow(d)
            wf = (d / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
            self.assertIn("Detectar stack", wf)
            self.assertIn("steps.stack.outputs.node_dir", wf)
            self.assertIn("steps.stack.outputs.py_dir", wf)
            self.assertIn("working-directory: ${{ steps.stack.outputs.py_dir }}", wf)
            self.assertIn("::warning", wf)
            self.assertNotIn("--if-present", wf)
            self.assertNotIn("hashFiles('tests/**/test_*.py')", wf)

    def test_generate_github_workflow_no_enmascara_fallos_de_pytest(self):
        """El fallback a unittest solo se usa si pytest no está instalado; un
        fallo real de pytest no debe disparar el fallback (ni quedar en verde)."""
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            scaffold.generate_github_workflow(d)
            wf = (d / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
            self.assertIn("elif python -m pytest --version", wf)
            self.assertNotIn("&& pytest -q ||", wf)

    def test_generate_context_file_marca_unresolved(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            metadata = {"title": "T", "problem": "p", "users": "u", "features": [],
                        "out_of_scope": [], "unresolved": ["features"]}
            scaffold.generate_context_file(d, None, metadata)
            ctx = (d / "CONTEXT.md").read_text(encoding="utf-8")
            self.assertIn("Sin confirmar", ctx)
            self.assertIn("Proyecto:** T", ctx)


class BootstrapStateTests(unittest.TestCase):
    def test_generate_state_file_compila_y_sella(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            scaffold.generate_progress_file(d)
            for name in ("INICIO_PROYECTO.md", "SECURITY.md", "TASK_TEMPLATE.md"):
                (d / name).write_text(f"# {name}\n", encoding="utf-8")
            bootstrap.generate_state_file(d, d / "PROGRESS.md")
            state = json.loads((d / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual(state["schema_version"], "3.0")
            self.assertEqual(sorted(state["sealed_docs"]),
                             ["INICIO_PROYECTO.md", "SECURITY.md", "TASK_TEMPLATE.md"])

    def test_generate_state_file_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "progress.json").write_text("{}", encoding="utf-8")
            bootstrap.generate_state_file(d, d / "PROGRESS.md")
            self.assertEqual((d / "progress.json").read_text(encoding="utf-8"), "{}")

    def test_rag_module_name(self):
        self.assertEqual(bootstrap.RAG_MODULE_NAME, "RAG_VECTOR_EXTENSION.md")

    def test_typesafe_module_name(self):
        self.assertEqual(bootstrap.TYPESAFE_MODULE_NAME, "TYPESAFE_EXTENSION.md")


class ExtensionModuleActivationTests(unittest.TestCase):
    """Los módulos condicionales se activan solo si el PRD los menciona."""

    def _project(self, d, module_name, prd_text):
        d = Path(d)
        (d / "docs").mkdir()
        (d / "docs" / module_name).write_text("# módulo\n", encoding="utf-8")
        prd = d / "PRD.md"
        prd.write_text(prd_text, encoding="utf-8")
        return d, prd

    def test_activa_typesafe_si_el_prd_lo_menciona(self):
        with tempfile.TemporaryDirectory() as d:
            project, prd = self._project(
                d, bootstrap.TYPESAFE_MODULE_NAME,
                "# Trading\nUsa TypeSafe (Jev) para clasificar señales y rutar órdenes.\n")
            bootstrap.maybe_activate_typesafe_module(project, prd)
            self.assertTrue((project / bootstrap.TYPESAFE_MODULE_NAME).exists())

    def test_no_activa_typesafe_sin_mencion(self):
        with tempfile.TemporaryDirectory() as d:
            project, prd = self._project(
                d, bootstrap.TYPESAFE_MODULE_NAME, "# App de notas\nSin IA de decisiones.\n")
            bootstrap.maybe_activate_typesafe_module(project, prd)
            self.assertFalse((project / bootstrap.TYPESAFE_MODULE_NAME).exists())

    def test_activa_rag_si_el_prd_lo_menciona(self):
        with tempfile.TemporaryDirectory() as d:
            project, prd = self._project(
                d, bootstrap.RAG_MODULE_NAME,
                "# Docs\nBúsqueda semántica con embeddings y pgvector.\n")
            bootstrap.maybe_activate_rag_module(project, prd)
            self.assertTrue((project / bootstrap.RAG_MODULE_NAME).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
