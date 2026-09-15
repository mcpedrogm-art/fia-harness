"""Tests unitarios de los comandos de estado (`fia_harness.core.commands`)."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fia_harness.core import commands
from fia_harness.core import state as st
from fia_harness.core.state import REQUIRED_SEALED

VALID_MD = """# PROGRESS.md

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap | Plantillas | — | [x] Listo |
| F0 | Repo | Funcionando | — | [ ] Pendiente |

## Checkpoints de Contexto Recientes
- **M0:** Arranque completado.
"""


def _write(path, text):
    path.write_text(text, encoding="utf-8")


class CommandsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "PROGRESS.md", VALID_MD)

    def test_sync_y_check_verde(self):
        commands.cmd_sync(self.dir)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            commands.cmd_check(self.dir)
        self.assertIn("válido", out.getvalue())

    def test_check_sin_state_falla_y_optional_pasa(self):
        with self.assertRaises(SystemExit):
            commands.cmd_check(self.dir)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            commands.cmd_check(self.dir, state_optional=True)
        self.assertIn("válido", out.getvalue())

    def test_seal_y_stats(self):
        for name in REQUIRED_SEALED:
            _write(self.dir / name, f"# {name}\n")
        commands.cmd_seal(self.dir, [])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            commands.cmd_stats(self.dir)
        self.assertIn("Documentos sellados", out.getvalue())

    def test_approval_registra_y_congela_spec(self):
        _write(self.dir / "DECISIONS.md", "# D\n\n## Aprobaciones\n")
        _write(self.dir / "SPEC.md", "# SPEC v1\n")
        commands.cmd_approval(self.dir, "aprobar", "M2", "chat", "Humano")
        text = (self.dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("**APPROVAL-001**", text)
        state = json.loads((self.dir / "progress.json").read_text(encoding="utf-8"))
        self.assertEqual(len(state["spec_hashes"]), 1)

    def test_reopen_requiere_motivo(self):
        with self.assertRaises(SystemExit):
            commands.cmd_reopen(self.dir, "F0", "")

    def test_stats_sin_state_cae_a_md(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            commands.cmd_stats(self.dir)
        self.assertIn("Fases de ejecución", out.getvalue())
        self.assertIn("calculado desde PROGRESS.md", err.getvalue())

    def _legacy_state_md(self):
        state = st.compile_state_from_md(VALID_MD)
        state.pop("schema_version")
        state["schema"] = st.LEGACY_SCHEMA
        return state

    def test_check_acepta_estado_legacy_con_aviso(self):
        (self.dir / st.STATE_FILE).write_text(json.dumps(self._legacy_state_md()),
                                              encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            commands.cmd_check(self.dir)
        self.assertIn("válido", out.getvalue())
        self.assertIn("schema legado", err.getvalue())

    def test_sync_migra_legacy_con_backup(self):
        (self.dir / st.STATE_FILE).write_text(json.dumps(self._legacy_state_md()),
                                              encoding="utf-8")
        commands.cmd_sync(self.dir)
        self.assertTrue((self.dir / (st.STATE_FILE + ".bak")).exists())
        self.assertEqual(st.load_state_json(self.dir)["schema_version"], st.SCHEMA_VERSION)

    def test_check_detecta_artefacto_editado_a_mano(self):
        commands.cmd_sync(self.dir)
        stored = st.load_state_json(self.dir)
        stored["compiled_at"] = "2020-01-01T00:00:00"  # altera el artefacto, no la autoridad
        (self.dir / st.STATE_FILE).write_text(json.dumps(stored), encoding="utf-8")
        with self.assertRaises(SystemExit):
            commands.cmd_check(self.dir)


if __name__ == "__main__":
    unittest.main(verbosity=2)
