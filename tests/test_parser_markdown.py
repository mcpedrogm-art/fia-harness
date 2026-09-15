"""Tests unitarios del parser de Markdown (`fia_harness.parser.markdown`)."""

import tempfile
import unittest
from pathlib import Path

from fia_harness.parser import markdown

SAMPLE = """# PROGRESS.md

## Fases

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| **M0** | Bootstrap | Plantillas | — | [x] Listo |
| F1 | Modelo | BBDD | F0 | [~] En curso |

## Checkpoints

- **M0 (Bootstrap):** listo.
    ```
    $ pytest -q
    12 passed
    ```
- **F1 (Modelo):** en curso.
    Evidencia: docs/ev.md
"""


class ParseProgressTableTests(unittest.TestCase):
    def test_lee_tabla_con_negritas_y_estados(self):
        rows = markdown.parse_progress_table(SAMPLE)
        self.assertEqual([r["phase"] for r in rows], ["M0", "F1"])
        self.assertEqual(rows[1]["status_raw"], "[~] En curso")

    def test_detect_next_phase_ignora_m(self):
        rows = markdown.parse_progress_table(SAMPLE)
        self.assertEqual(markdown.detect_next_phase(rows), "F1")

    def test_get_phase_row(self):
        rows = markdown.parse_progress_table(SAMPLE)
        self.assertEqual(markdown.get_phase_row(rows, "M0")["objective"], "Bootstrap / Plantillas")

    def test_is_row_done(self):
        rows = markdown.parse_progress_table(SAMPLE)
        self.assertTrue(markdown.is_row_done(rows[0]))
        self.assertFalse(markdown.is_row_done(rows[1]))


class ExtractCheckpointsTests(unittest.TestCase):
    def test_captura_evidencia_cruda_y_archivo(self):
        cps = {c["phase"]: c for c in markdown.extract_checkpoints(SAMPLE)}
        self.assertIn("12 passed", cps["M0"]["evidence"])
        self.assertEqual(cps["F1"]["evidence_file"], "docs/ev.md")
        self.assertEqual(cps["F1"]["evidence"], "")


class FlipPhaseStatusTests(unittest.TestCase):
    def test_cambia_solo_la_celda_de_estado(self):
        nuevo = markdown.flip_phase_status(SAMPLE, "F1", "x")
        self.assertIn("| F1 | Modelo | BBDD | F0 | [x] En curso |", nuevo)
        self.assertIn("| **M0** | Bootstrap | Plantillas | — | [x] Listo |", nuevo)

    def test_fase_inexistente_devuelve_none(self):
        self.assertIsNone(markdown.flip_phase_status(SAMPLE, "F9", "x"))


class ExtractSectionTests(unittest.TestCase):
    def test_corta_en_el_siguiente_encabezado(self):
        self.assertEqual(markdown.extract_section("## A\nuno\n## B\ndos\n", "A"), "uno")


class LoadFileTests(unittest.TestCase):
    def test_falta_archivo_obligatorio_falla(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                markdown.load_file(Path(d) / "nope.md")

    def test_opcional_devuelve_vacio(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(markdown.load_file(Path(d) / "nope.md", required=False), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
