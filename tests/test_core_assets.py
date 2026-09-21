"""Tests del pack de assets (`fia_harness.core.assets`, v3.5)."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fia_harness import cli
from fia_harness.core import assets


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")


class AssetsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.project = self.root / "proyecto"
        self.project.mkdir()
        self.source = self.root / "pack"
        _write(self.source / "media" / "hero.bin", b"hero-bytes")
        _write(self.source / "media" / "fondo ñ.png", b"fondo-bytes")

    def _manifest(self, base_url=None):
        base = base_url or self.source.as_uri()
        out = self.root / "UI_ASSETS.json"
        with contextlib.redirect_stdout(io.StringIO()):
            assets.build_manifest(self.source, base, out)
        return json.loads(out.read_text(encoding="utf-8")), out

    def test_build_manifest_con_hashes_y_urls(self):
        manifest, _ = self._manifest(base_url="https://cdn.example.com/pack")
        entries = {e["path"]: e for e in manifest["assets"]}
        self.assertIn("media/hero.bin", entries)
        self.assertTrue(entries["media/hero.bin"]["url"]
                        .startswith("https://cdn.example.com/pack/media/hero.bin"))
        self.assertEqual(len(entries["media/hero.bin"]["sha256"]), 64)
        self.assertIn("media/fondo%20%C3%B1.png", entries["media/fondo ñ.png"]["url"])

    def test_fetch_file_url_verifica_e_idempotente(self):
        _, path = self._manifest()  # URLs file://
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = assets.fetch_manifest(self.project, str(path))
        self.assertEqual(code, 0)
        self.assertEqual((self.project / "media" / "hero.bin").read_bytes(), b"hero-bytes")
        with contextlib.redirect_stdout(out):
            code = assets.fetch_manifest(self.project, str(path))
        self.assertEqual(code, 0)
        self.assertIn("ya en su sitio", out.getvalue())

    def test_fetch_hash_incorrecto_falla_sin_dejar_restos(self):
        manifest, path = self._manifest()
        manifest["assets"][0]["sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()), \
                    contextlib.redirect_stdout(io.StringIO()):
                assets.fetch_manifest(self.project, str(path))
        self.assertFalse((self.project / "media" / "hero.bin").exists())
        self.assertFalse(list(self.project.rglob("*.part")))

    def test_fetch_path_traversal_falla(self):
        manifest, path = self._manifest()
        manifest["assets"][0]["path"] = "../fuera.bin"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()), \
                    contextlib.redirect_stdout(io.StringIO()):
                assets.fetch_manifest(self.project, str(path))
        self.assertFalse((self.root / "fuera.bin").exists())

    def test_manifest_inexistente_falla(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                assets.fetch_manifest(self.project, str(self.root / "no-existe.json"))

    def test_manifest_version_no_soportada_falla(self):
        path = self.root / "UI_ASSETS.json"
        path.write_text(json.dumps({
            "version": 99,
            "assets": [{"path": "a", "url": "file:///a", "sha256": "0" * 64}],
        }), encoding="utf-8")
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                assets.fetch_manifest(self.project, str(path))

    def test_cli_assets_fetch(self):
        _, path = self._manifest()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["assets", "fetch", str(path), "-d", str(self.project)])
        self.assertEqual(code, 0)
        self.assertTrue((self.project / "media" / "hero.bin").exists())

    def test_init_con_assets(self):
        _, path = self._manifest()
        target = self.root / "nuevo"
        with contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(["init", "-d", str(target), "--assets", str(path)])
        self.assertEqual(code, 0)
        self.assertTrue((target / "media" / "hero.bin").exists())
        self.assertTrue((target / "docs" / "UI_ASSETS.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
