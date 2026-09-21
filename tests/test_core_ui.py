"""Tests del entorno UI/UX asistido (`fia_harness.core.ui`, v3.6)."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from fia_harness import cli
from fia_harness.core import assets
from fia_harness.core import ui


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")


class UiTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.project = self.root / "proyecto"
        self.project.mkdir()
        self.source = self.root / "pack"
        _write(self.source / "media" / "hero.bin", b"hero-bytes")
        _write(self.source / "library" / "UI_LIBRARY.md", "# recetas\n")
        out = self.root / "manifest.json"
        with contextlib.redirect_stdout(io.StringIO()):
            assets.build_manifest(self.source, self.source.as_uri(), out)
        self.manifest = out

    def _setup(self, **kwargs):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ui.cmd_ui_setup(self.project, **kwargs)
        return code, out.getvalue()

    def test_setup_completo_y_manifiesto_guardado(self):
        code, out = self._setup(url=str(self.manifest))
        self.assertEqual(code, 0)
        self.assertTrue((self.project / "media" / "hero.bin").exists())
        self.assertTrue((self.project / "library" / "UI_LIBRARY.md").exists())
        saved = json.loads((self.project / "UI_ASSETS.json").read_text(encoding="utf-8"))
        self.assertEqual(len(saved["assets"]), 2)

    def test_setup_solo_recetas(self):
        code, _ = self._setup(url=str(self.manifest), recipes_only=True)
        self.assertEqual(code, 0)
        self.assertTrue((self.project / "library" / "UI_LIBRARY.md").exists())
        self.assertFalse((self.project / "media" / "hero.bin").exists())

    def test_status_ausente_sin_manifiesto(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ui.cmd_ui_status(self.project)
        self.assertIn("ausente", out.getvalue())

    def test_status_completo_y_parcial(self):
        self._setup(url=str(self.manifest))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ui.cmd_ui_status(self.project)
        self.assertIn("completo (2/2", out.getvalue())
        (self.project / "media" / "hero.bin").unlink()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ui.cmd_ui_status(self.project)
        self.assertIn("parcial (1/2", out.getvalue())
        self.assertIn("falta: media/hero.bin", out.getvalue())

    def test_status_modificado(self):
        self._setup(url=str(self.manifest))
        _write(self.project / "media" / "hero.bin", b"tampered")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ui.cmd_ui_status(self.project)
        self.assertIn("modificado: media/hero.bin", out.getvalue())

    def test_override_por_env(self):
        old = os.environ.get("FIA_UI_PACK_URL")
        os.environ["FIA_UI_PACK_URL"] = "https://ejemplo.test/UI_ASSETS.json"
        self.addCleanup(lambda: os.environ.__setitem__("FIA_UI_PACK_URL", old)
                        if old is not None else os.environ.pop("FIA_UI_PACK_URL", None))
        self.assertEqual(ui.pack_url(), "https://ejemplo.test/UI_ASSETS.json")
        self.assertEqual(ui.pack_url("https://otro.test/x.json"), "https://otro.test/x.json")

    def test_url_oficial_por_defecto(self):
        self.assertTrue(ui.UI_PACK_URL.startswith("https://supabase.pgmia.es/"))
        self.assertTrue(ui.UI_PACK_URL.endswith("UI_ASSETS.json"))

    def test_cli_ui_setup_y_status(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["ui", "setup", "--url", str(self.manifest),
                             "-d", str(self.project)])
        self.assertEqual(code, 0)
        with contextlib.redirect_stdout(out):
            code = cli.main(["ui", "status", "-d", str(self.project)])
        self.assertEqual(code, 0)
        self.assertIn("completo", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
