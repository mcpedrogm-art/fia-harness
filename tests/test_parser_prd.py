"""Tests unitarios de la extracción del PRD (`fia_harness.parser.prd`)."""

import tempfile
import unittest
from pathlib import Path

from fia_harness.parser import prd


class FindPrdFileTests(unittest.TestCase):
    def _tmp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_nombre_estandar_prioritario(self):
        d = self._tmp()
        (d / "Notas.md").write_text("x", encoding="utf-8")
        (d / "PRD.md").write_text("x", encoding="utf-8")
        self.assertEqual(prd.find_prd_file(d).name, "PRD.md")

    def test_todas_las_plantillas_del_kit_quedan_excluidas(self):
        d = self._tmp()
        for name in ("INICIO_PROYECTO.md", "SECURITY.md", "AEO_GEO_SEO.md",
                     "UI_UX_EXCLUSIVA.md", "SKILLS_MCP.md", "TASK_TEMPLATE.md",
                     "TASK_LITE_TEMPLATE.md", "QUICKSTART_LITE.md", "AGENTS.md"):
            (d / name).write_text("x", encoding="utf-8")
        self.assertIsNone(prd.find_prd_file(d))

    def test_tasks_no_son_prd(self):
        d = self._tmp()
        (d / "TASK-F1.md").write_text("x", encoding="utf-8")
        self.assertIsNone(prd.find_prd_file(d))


class ExtractPrdMetadataTests(unittest.TestCase):
    def _extract(self, content):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "PRD.md"
            p.write_text(content, encoding="utf-8")
            return prd.extract_prd_metadata(p)

    def test_extrae_secciones_y_sin_unresolved(self):
        meta = self._extract(
            "# App\n\n## Problema\np\n\n## Usuarios\nu\n\n## Funcionalidades\n* f\n\n## Fuera de alcance\n* o\n")
        self.assertEqual(meta["title"], "App")
        self.assertEqual(meta["unresolved"], [])

    def test_sin_secciones_marca_unresolved(self):
        meta = self._extract("# App\nsolo texto\n")
        self.assertEqual(sorted(meta["unresolved"]),
                         ["features", "out_of_scope", "problem", "users"])

    def test_sin_prd_devuelve_placeholders(self):
        meta = prd.extract_prd_metadata(None)
        self.assertEqual(meta["title"], "Nuevo Proyecto")
        self.assertEqual(len(meta["unresolved"]), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
