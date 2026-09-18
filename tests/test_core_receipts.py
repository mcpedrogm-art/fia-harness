"""Tests del recibo de fase (`fia_harness.core.receipts`, v3.3, regla de oro nº16)."""

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from fia_harness import cli
from fia_harness.core import commands
from fia_harness.core import receipts
from fia_harness.core import state as st
from fia_harness.core import verify
from fia_harness.core.fingerprints import sha256_hex
from fia_harness.parser.markdown import extract_checkpoints

MD = """# PROGRESS.md

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap | Plantillas | — | [x] Listo |
| F1 | Backend | API | M0 | [~] En curso |

## Checkpoints de Contexto Recientes
- **M0:** listo.
"""

DONE_MD = MD.replace(
    "| F1 | Backend | API | M0 | [~] En curso |",
    "| F1 | Backend | API | M0 | [x] Listo |").replace(
    "- **M0:** listo.\n",
    "- **M0:** listo.\n- **F1:** API lista.\n"
    "    ```\n    Ran 10 tests\n    OK\n    ```\n")

TASK = "# TASK-F1\n\n## Alcance permitido (scope)\n- src/**\n"


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(project_dir, *args):
    subprocess.run(["git", *args], cwd=project_dir, check=True, capture_output=True, text=True)


def _grandfather(project_dir):
    state = st.load_state_json(project_dir)
    for checkpoint in state.get("checkpoints", []):
        checkpoint["recorded_at"] = "2026-09-15T00:00:00"
    st.write_state(project_dir, state)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _git(self.dir, "init", "-q")
        _git(self.dir, "config", "user.email", "t@t")
        _git(self.dir, "config", "user.name", "t")
        _write(self.dir / "PROGRESS.md", MD)
        _write(self.dir / "TASK-F1.md", TASK)
        _write(self.dir / "DECISIONS.md", "# DECISIONS.md\n\n## Aprobaciones\n")
        _write(self.dir / "src" / "app.py", "print('v1')\n")
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "base")
        commands.cmd_sync(self.dir)
        _write(self.dir / "src" / "app.py", "print('v2')\n")  # trabajo de la fase

    def _create(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            commands.cmd_receipt_create(self.dir, "F1", **kwargs)

    def _receipt(self):
        path = receipts.receipt_path(self.dir, "F1")
        return path, json.loads(path.read_text(encoding="utf-8"))

    def test_crea_recibo_y_verifica_dirty(self):
        self._create(allow_dirty=True, tests_raw="10/10")
        path, receipt = self._receipt()
        self.assertTrue(path.exists())
        self.assertEqual(receipt["checks"]["tests"], {"passed": 10, "total": 10})
        self.assertEqual(receipt["mode"], "FULL")
        self.assertEqual([f["path"] for f in receipt["files"]], ["src/app.py"])
        errors, note = receipts.verify_phase(self.dir, "F1")
        self.assertEqual(errors, [])
        self.assertIn("dirty", note)

    def test_determinismo_mismo_arbol_mismo_hash(self):
        self._create(allow_dirty=True)
        path, first = self._receipt()
        path.unlink()
        self._create(allow_dirty=True)
        _, second = self._receipt()
        self.assertEqual(first["receipt_sha256"], second["receipt_sha256"])

    def test_manipulacion_de_archivo_detectada(self):
        self._create(allow_dirty=True)
        _write(self.dir / "src" / "app.py", "print('v3')\n")
        errors, _ = receipts.verify_phase(self.dir, "F1")
        self.assertTrue(any("contenido modificado" in e for e in errors), errors)

    def test_hash_manipulado_detectado(self):
        self._create(allow_dirty=True)
        path, receipt = self._receipt()
        receipt["receipt_sha256"] = "0" * 64
        path.write_text(json.dumps(receipt), encoding="utf-8")
        errors, _ = receipts.verify_phase(self.dir, "F1")
        self.assertTrue(any("receipt_sha256" in e for e in errors), errors)

    def test_recibo_limpio_se_verifica_contra_commit(self):
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "fase")
        self._create(base="HEAD~1")
        errors, note = receipts.verify_phase(self.dir, "F1")
        self.assertEqual(errors, [])
        self.assertIn("verificado contra", note)
        path, receipt = self._receipt()
        receipt["files"][0]["content_sha256"] = "1" * 64  # forja coherente
        receipt["receipt_sha256"] = receipts.compute_sha256(receipt)
        path.write_text(json.dumps(receipt), encoding="utf-8")
        errors, _ = receipts.verify_phase(self.dir, "F1")
        self.assertTrue(any("distinto al commit" in e for e in errors), errors)

    def test_evidencia_inexistente_falla(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self._create(allow_dirty=True, evidence_ids=["EV-999"])

    def test_fase_done_sin_recibo_falla_check(self):
        _write(self.dir / "PROGRESS.md", DONE_MD)
        commands.cmd_sync(self.dir)
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                commands.cmd_check(self.dir)

    def test_fase_done_con_recibo_pasa_check(self):
        self._create(allow_dirty=True)
        done = DONE_MD.replace(
            "- **F1:** API lista.\n",
            "- **F1:** API lista.\n"
            "    Recibo: evidence/receipts/receipt-F1.json\n")
        _write(self.dir / "PROGRESS.md", done)
        commands.cmd_sync(self.dir)
        with contextlib.redirect_stdout(io.StringIO()):
            commands.cmd_check(self.dir)

    def test_grandfathering_fase_antigua_sin_recibo_pasa(self):
        _write(self.dir / "PROGRESS.md", DONE_MD)
        commands.cmd_sync(self.dir)
        _grandfather(self.dir)
        with contextlib.redirect_stdout(io.StringIO()):
            commands.cmd_check(self.dir)

    def test_seccion_receipts_en_verify(self):
        self._create(allow_dirty=True)
        done = DONE_MD.replace(
            "- **F1:** API lista.\n",
            "- **F1:** API lista.\n"
            "    Recibo: evidence/receipts/receipt-F1.json\n")
        _write(self.dir / "PROGRESS.md", done)
        commands.cmd_sync(self.dir)
        report = verify.build_report(self.dir)
        self.assertEqual(report["sections"]["RECEIPTS"]["errors"], [])
        self.assertIn("1 local(dirty)", report["sections"]["RECEIPTS"]["note"])

    def test_strict_receipts_falla_si_dirty_cambia(self):
        self._create(allow_dirty=True)
        done = DONE_MD.replace(
            "- **F1:** API lista.\n",
            "- **F1:** API lista.\n"
            "    Recibo: evidence/receipts/receipt-F1.json\n")
        _write(self.dir / "PROGRESS.md", done)
        commands.cmd_sync(self.dir)
        _write(self.dir / "src" / "app.py", "print('v3')\n")  # trabajo posterior
        self.assertEqual(verify.build_report(self.dir)["sections"]["RECEIPTS"]["errors"], [])
        strict = verify.build_report(self.dir, strict_receipts=True)
        self.assertTrue(any("contenido modificado" in e
                            for e in strict["sections"]["RECEIPTS"]["errors"]))

    def test_borrado_se_representa_y_verifica(self):
        _write(self.dir / "src" / "viejo.py", "print('old')\n")
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "extra")
        (self.dir / "src" / "viejo.py").unlink()
        self._create(allow_dirty=True)
        _, receipt = self._receipt()
        deleted = [f for f in receipt["files"] if f.get("deleted")]
        self.assertEqual([f["path"] for f in deleted], ["src/viejo.py"])
        self.assertIsNone(deleted[0]["content_sha256"])
        errors, _ = receipts.verify_phase(self.dir, "F1")
        self.assertEqual(errors, [])
        _write(self.dir / "src" / "viejo.py", "print('vuelve')\n")
        errors, _ = receipts.verify_phase(self.dir, "F1")
        self.assertTrue(any("debería estar borrado" in e for e in errors), errors)

    def test_borrado_en_recibo_limpio_verifica_commit(self):
        _write(self.dir / "src" / "viejo.py", "print('old')\n")
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "extra")
        (self.dir / "src" / "viejo.py").unlink()
        _git(self.dir, "add", "-A")
        _git(self.dir, "commit", "-qm", "fase con borrado")
        self._create(base="HEAD~1")
        _, receipt = self._receipt()
        self.assertFalse(receipt["dirty"])
        self.assertTrue(any(f.get("deleted") for f in receipt["files"]))
        errors, note = receipts.verify_phase(self.dir, "F1")
        self.assertEqual(errors, [])
        self.assertIn("verificado contra", note)

    def test_nombre_no_ascii_se_registra_con_hash(self):
        _write(self.dir / "src" / "mi archivo ñ.py", "print('x')\n")
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "unicode")
        _write(self.dir / "src" / "mi archivo ñ.py", "print('y')\n")
        self._create(allow_dirty=True)
        _, receipt = self._receipt()
        entry = next(f for f in receipt["files"] if f["path"].endswith("ñ.py"))
        self.assertIsNotNone(entry["content_sha256"])
        self.assertFalse(entry.get("deleted"))
        errors, _ = receipts.verify_phase(self.dir, "F1")
        self.assertEqual(errors, [])

    def test_renombrado_registra_baja_y_alta(self):
        _write(self.dir / "src" / "a.py", "print('a')\n")
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "base rename")
        _git(self.dir, "mv", "src/a.py", "src/b.py")
        self._create(allow_dirty=True)
        _, receipt = self._receipt()
        paths = {(f["path"], f.get("deleted", False)) for f in receipt["files"]}
        self.assertIn(("src/a.py", True), paths)
        self.assertIn(("src/b.py", False), paths)
        errors, _ = receipts.verify_phase(self.dir, "F1")
        self.assertEqual(errors, [])

    def test_cli_create_y_verify(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["receipt", "create", "F1", "--allow-dirty",
                             "--tests", "10/10", "-d", str(self.dir)])
        self.assertEqual(code, 0)
        with contextlib.redirect_stdout(out):
            code = cli.main(["receipt", "verify", "F1", "-d", str(self.dir)])
        self.assertEqual(code, 0)
        self.assertIn("PASS", out.getvalue())

    def test_reemision_limpia_tras_commit(self):
        self._create(allow_dirty=True)
        done = DONE_MD.replace(
            "- **F1:** API lista.\n",
            "- **F1:** API lista.\n"
            "    Recibo: evidence/receipts/receipt-F1.json\n")
        _write(self.dir / "PROGRESS.md", done)
        commands.cmd_sync(self.dir)
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "cierre fase")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self._create(base="HEAD~1")  # re-emisión en done con árbol limpio
        _, receipt = self._receipt()
        self.assertFalse(receipt["dirty"])
        errors, note = receipts.verify_phase(self.dir, "F1")
        self.assertEqual(errors, [])
        self.assertIn("verificado contra", note)

    def test_gobernanza_no_marca_dirty(self):
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "fase")
        _write(self.dir / "PROGRESS.md", MD + "\n<!-- nota de gobernanza -->\n")
        self._create(base="HEAD~1")  # sin --allow-dirty: solo cambió gobernanza
        _, receipt = self._receipt()
        self.assertFalse(receipt["dirty"])


class NoGitTests(unittest.TestCase):
    def test_create_requiere_git(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        project = Path(tmp.name)
        _write(project / "PROGRESS.md", MD)
        _write(project / "TASK-F1.md", TASK)
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                commands.cmd_receipt_create(project, "F1", allow_dirty=True)


class SealedDocsReceiptTests(unittest.TestCase):
    """Regresión v3.4.3: receipt create fallaba en proyectos con docs sellados
    (el estado compilado no llevaba `sealed_docs`)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _git(self.dir, "init", "-q")
        _git(self.dir, "config", "user.email", "t@t")
        _git(self.dir, "config", "user.name", "t")
        _write(self.dir / "PROGRESS.md", MD)
        _write(self.dir / "TASK-F1.md", TASK)
        _write(self.dir / "DECISIONS.md", "# DECISIONS.md\n\n## Aprobaciones\n")
        _write(self.dir / "src" / "app.py", "print('v1')\n")
        for name in ("INICIO_PROYECTO.md", "SECURITY.md", "TASK_TEMPLATE.md"):
            _write(self.dir / name, f"# {name}\nv1\n")
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "base")
        with contextlib.redirect_stdout(io.StringIO()):
            commands.cmd_seal(self.dir, [])
            commands.cmd_sync(self.dir)
        _write(self.dir / "src" / "app.py", "print('v2')\n")

    def test_receipt_create_con_documentos_sellados(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            commands.cmd_receipt_create(self.dir, "F1", allow_dirty=True, tests_raw="10/10")
        self.assertIn("Recibo emitido", out.getvalue())
        path = receipts.receipt_path(self.dir, "F1")
        receipt = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["checks"]["golden_rules"], "pass")
        errors, _ = receipts.verify_phase(self.dir, "F1")
        self.assertEqual(errors, [])


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_crlf_y_lf_dan_el_mismo_hash(self):
        (self.dir / "lf.txt").write_bytes(b"linea1\nlinea2\n")
        (self.dir / "crlf.txt").write_bytes(b"linea1\r\nlinea2\r\n")
        self.assertEqual(receipts.content_sha256(self.dir / "lf.txt"),
                         receipts.content_sha256(self.dir / "crlf.txt"))

    def test_bom_ignorado(self):
        (self.dir / "con_bom.txt").write_bytes(b"\xef\xbb\xbfhola\n")
        (self.dir / "sin_bom.txt").write_bytes(b"hola\n")
        self.assertEqual(receipts.content_sha256(self.dir / "con_bom.txt"),
                         receipts.content_sha256(self.dir / "sin_bom.txt"))

    def test_binario_crudo(self):
        data = b"\x00\x01\r\n\x02"
        (self.dir / "bin.dat").write_bytes(data)
        self.assertEqual(receipts.content_sha256(self.dir / "bin.dat"), sha256_hex(data))


class ParserReceiptTests(unittest.TestCase):
    def test_extrae_recibo_del_checkpoint(self):
        text = ("# P\n\n## Checkpoints\n- **F1:** ok.\n"
                "    Recibo: evidence/receipts/receipt-F1.json\n")
        checkpoints = extract_checkpoints(text)
        self.assertEqual(checkpoints[0]["receipt_ref"],
                         "evidence/receipts/receipt-F1.json")

    def test_sin_recibo_es_none(self):
        checkpoints = extract_checkpoints("# P\n\n## Checkpoints\n- **F1:** ok.\n")
        self.assertIsNone(checkpoints[0]["receipt_ref"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
