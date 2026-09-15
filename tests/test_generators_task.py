"""Tests unitarios de la generación de TASK-Fx.md (`fia_harness.generators.task`)."""

import tempfile
import unittest
from pathlib import Path

from fia_harness.generators import task

SNIPPET = "antes\n<!-- INJECT:SECURITY_CHECKLIST -->\nviejo\n<!-- /INJECT -->\ndespués\n"


class InjectTests(unittest.TestCase):
    def test_sustituye_bloque_completo(self):
        out, found = task.inject(SNIPPET, "security", "NUEVO")
        self.assertTrue(found)
        self.assertIn("NUEVO", out)
        self.assertNotIn("viejo", out)

    def test_marcador_ausente_devuelve_found_false(self):
        out, found = task.inject("sin nada", "security", "X")
        self.assertFalse(found)
        self.assertEqual(out, "sin nada")


class DetectLiteTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_declarado_lite(self):
        self.assertTrue(task.detect_lite_mode("Modo de trabajo: Lite", self.dir, False))

    def test_mencion_como_opcion_no_activa(self):
        self.assertFalse(task.detect_lite_mode("(Completo / Lite)", self.dir, False))

    def test_quick_context_activa(self):
        (self.dir / "QUICK_CONTEXT.md").write_text("x", encoding="utf-8")
        self.assertTrue(task.detect_lite_mode("", self.dir, False))

    def test_flag_forzado_gana(self):
        self.assertTrue(task.detect_lite_mode("Modo de trabajo: Completo", self.dir, True))


class StripTemplateHeaderTests(unittest.TestCase):
    def test_recorta_cabecera_meta(self):
        self.assertEqual(task.strip_template_meta_header("# META\nx\n# TASK-<N>\ny", "t"),
                         "# TASK-<N>\ny")

    def test_sin_encabezado_devuelve_integro(self):
        self.assertEqual(task.strip_template_meta_header("hola", "t"), "hola")


class BuildTaskFileTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        root = Path(__file__).resolve().parent.parent
        for name in ("TASK_TEMPLATE.md", "TASK_LITE_TEMPLATE.md", "SECURITY.md",
                     "AEO_GEO_SEO.md", "UI_UX_EXCLUSIVA.md"):
            (self.dir / name).write_text((root / name).read_text(encoding="utf-8"),
                                         encoding="utf-8")

    def test_genera_task_con_objetivo_y_checklists(self):
        row = {"phase": "F1", "title": "Modelo de datos", "objective": "BBDD creada",
               "dependencies": "F0", "status_raw": "[ ]"}
        content = task.build_task_file(
            self.dir, row, {"security": True, "visibility": False, "ui_ux": False}, False)
        self.assertTrue(content.startswith("# TASK-F1"), content.splitlines()[0])
        self.assertIn("BBDD creada", content)
        self.assertIn("Checklist de Seguridad Obligatorio", content)
        self.assertIn("No aplica: esta tarea no toca superficie pública", content)

    def test_modo_lite_no_inyecta_marcadores(self):
        row = {"phase": "F1", "title": "Modelo", "objective": "BBDD",
               "dependencies": "—", "status_raw": "[ ]"}
        content = task.build_task_file(
            self.dir, row, {"security": True, "visibility": False, "ui_ux": False}, True)
        self.assertTrue(content.startswith("# TASK-QUICK"), content.splitlines()[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
