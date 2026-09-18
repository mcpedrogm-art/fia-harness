"""Tests unitarios de la extracción del PRD (`fia_harness.parser.prd`)."""

import json
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
                     "TASK_LITE_TEMPLATE.md", "UI_RECIPES.md", "QUICKSTART_LITE.md",
                     "AGENTS.md"):
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


class ExtractFieldConfidenceTests(unittest.TestCase):
    """F2: niveles de confianza explícitos y métodos trazables."""

    def test_heading_exacto_es_alta(self):
        result = prd.extract_field("# App\n\n## Problema\nTexto.\n", "problem")
        self.assertEqual((result.confidence, result.method), ("alta", "heading:Problema"))
        self.assertEqual(result.value, "Texto.")

    def test_heading_parcial_es_media(self):
        result = prd.extract_field("# App\n\n## Problema y contexto\nTexto.\n", "problem")
        self.assertEqual(result.confidence, "media")
        self.assertTrue(result.method.startswith("heading_partial:"))

    def test_densidad_es_media(self):
        content = "# App\n\n## El dolor del cliente\nEl problema y la necesidad son reales.\n"
        result = prd.extract_field(content, "problem")
        self.assertEqual(result.confidence, "media")
        self.assertTrue(result.method.startswith("density:"))

    def test_sin_secciones_es_ninguna(self):
        result = prd.extract_field("# App\nsolo prosa sin secciones\n", "problem")
        self.assertEqual((result.confidence, result.method), ("ninguna", "none"))

    def test_titulo_h1_es_alta_y_sin_h1_ninguna(self):
        self.assertEqual(prd.extract_field("# Mi App\n", "title").confidence, "alta")
        self.assertEqual(prd.extract_field("sin h1\n", "title").confidence, "ninguna")

    def test_acentos_y_mayusculas_se_normalizan(self):
        result = prd.extract_field("# App\n\n## INTRODUCCION\nTexto.\n", "problem")
        self.assertEqual(result.confidence, "alta")  # sinónimo "Introducción"

    def test_campo_desconocido_falla(self):
        with self.assertRaises(ValueError):
            prd.extract_field("# App\n", "inexistente")

    def test_sinonimo_nuevo_en_config_no_toca_codigo(self):
        config = json.loads(json.dumps(prd.load_config()))  # copia profunda
        config["fields"]["problem"].append("Motivación")
        result = prd.extract_field("# App\n\n## Motivación\nTexto.\n", "problem", config)
        self.assertEqual((result.confidence, result.method), ("alta", "heading:Motivación"))

    def test_config_versionada_carga_y_tiene_los_campos(self):
        config = prd.load_config()
        self.assertIn("version", config)
        for field in ("problem", "users", "features", "out_of_scope"):
            self.assertTrue(config["fields"][field], f"sin sinónimos para {field}")

    def test_config_ausente_falla_claramente(self):
        with self.assertRaises(RuntimeError):
            prd.load_config("C:/ruta/que/no/existe/synonyms.json")

    def test_metadata_incluye_confianza_para_todos_los_campos(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "PRD.md"
            p.write_text("# App\n\n## Problema\np\n", encoding="utf-8")
            meta = prd.extract_prd_metadata(p)
        for field in prd.ALL_FIELDS:
            self.assertIn(field, meta["confidence"], field)
            self.assertIn(meta["confidence"][field]["level"], prd.CONFIDENCE_LEVELS)

    def test_unresolved_es_lo_que_tiene_confianza_ninguna(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "PRD.md"
            p.write_text("# App\n\n## Problema\np\n", encoding="utf-8")
            meta = prd.extract_prd_metadata(p)
        self.assertEqual(sorted(meta["unresolved"]), ["features", "out_of_scope", "users"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
