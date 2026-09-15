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
            self.assertIn("task_generator.py --check", wf)

    def test_generate_github_workflow_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            wf = d / ".github" / "workflows" / "harness.yml"
            wf.parent.mkdir(parents=True)
            wf.write_text("custom", encoding="utf-8")
            scaffold.generate_github_workflow(d)
            self.assertEqual(wf.read_text(encoding="utf-8"), "custom")

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
            self.assertEqual(state["schema"], "harness-state/1")
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
