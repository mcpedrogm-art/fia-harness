"""Tests unitarios del modelo de estado (`fia_harness.core.state`)."""

import tempfile
import unittest
from pathlib import Path

from fia_harness.core import state as st

VALID_MD = """# PROGRESS.md

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap | Plantillas | — | [x] Listo |
| F0 | Repo | Funcionando | — | [ ] Pendiente |
| F1 | Datos | BBDD | F0 | [ ] Pendiente |

## Checkpoints de Contexto Recientes
- **M0:** Arranque completado.
"""


def _write(path, text):
    path.write_text(text, encoding="utf-8")


class CompileTests(unittest.TestCase):
    def test_compila_proceso_y_ejecucion(self):
        state = st.compile_state_from_md(VALID_MD)
        self.assertEqual([p["id"] for p in state["process_phases"]], ["M0"])
        self.assertEqual([p["id"] for p in state["execution_phases"]], ["F0", "F1"])
        self.assertEqual(state["schema"], st.SCHEMA_NAME)

    def test_dependencias_separan_ids_y_notas(self):
        md = VALID_MD.replace("| F0 | Repo | Funcionando | — |",
                              "| F0 | Repo | Funcionando | SPEC aprobado |")
        entry = st.compile_state_from_md(md)["execution_phases"][0]
        self.assertEqual(entry["depends_on"], [])
        self.assertEqual(entry["depends_on_notes"], "SPEC aprobado")

    def test_fingerprint_ignora_volatiles(self):
        a = st.compile_state_from_md(VALID_MD, updated="2026-01-01")
        b = st.compile_state_from_md(VALID_MD, updated="2026-12-31")
        b["sealed_docs"] = {"X": "y"}
        b["spec_hashes"] = [{"sha256": "z"}]
        self.assertEqual(st.state_fingerprint(a), st.state_fingerprint(b))


class ValidateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "PROGRESS.md", VALID_MD)

    def _state(self, md=None):
        return st.compile_state_from_md(md or VALID_MD)

    def test_estado_valido(self):
        self.assertEqual(st.validate_state(self._state(), self.dir), [])

    def test_fase_cerrada_sin_checkpoint(self):
        md = VALID_MD.replace("| F0 | Repo | Funcionando | — | [ ] Pendiente |",
                              "| F0 | Repo | Funcionando | — | [x] Listo |")
        errors = st.validate_state(self._state(md), self.dir)
        self.assertTrue(any("checkpoint" in e for e in errors), errors)

    def test_dependencia_inexistente(self):
        md = VALID_MD.replace("| F0 | Repo | Funcionando | — |",
                              "| F0 | Repo | Funcionando | F9 |")
        errors = st.validate_state(self._state(md), self.dir)
        self.assertTrue(any("F9" in e for e in errors), errors)

    def test_estado_fuera_del_enum(self):
        state = self._state()
        state["execution_phases"][0]["status"] = "acabada"
        self.assertTrue(any("no válido" in e for e in st.validate_state(state, self.dir)))

    def test_aprobacion_citada_no_registrada(self):
        _write(self.dir / "TASK-F0.md", "cita APPROVAL-007\n")
        errors = st.validate_state(self._state(), self.dir)
        self.assertTrue(any("APPROVAL-007" in e for e in errors), errors)

    def test_aprobacion_incompleta(self):
        _write(self.dir / "DECISIONS.md", "## Aprobaciones\n\n- **APPROVAL-002** aprobó cosas\n")
        errors = st.validate_state(self._state(), self.dir)
        self.assertTrue(any("incompleta" in e for e in errors), errors)


class SealedAndSpecTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "PROGRESS.md", VALID_MD)

    def test_sello_y_alteracion(self):
        for name in st.REQUIRED_SEALED:
            _write(self.dir / name, f"# {name}\nv1\n")
        state = st.compile_state_from_md(VALID_MD)
        state["sealed_docs"] = st.compute_doc_hashes(self.dir, st.REQUIRED_SEALED)
        self.assertEqual(st.validate_sealed_docs(state, self.dir), [])
        _write(self.dir / "SECURITY.md", "# SECURITY.md\nalterado\n")
        self.assertTrue(st.validate_sealed_docs(state, self.dir))

    def test_doc_presente_sin_sellar(self):
        _write(self.dir / "SECURITY.md", "# SECURITY.md\n")
        state = st.compile_state_from_md(VALID_MD)
        self.assertTrue(any("no sellado" in e for e in st.validate_sealed_docs(state, self.dir)))

    def test_spec_snapshot(self):
        _write(self.dir / "SPEC.md", "# SPEC v1\n")
        state = st.compile_state_from_md(VALID_MD)
        state["spec_hashes"] = [{"sha256": st.sha256_hex((self.dir / "SPEC.md").read_bytes())}]
        self.assertEqual(st.validate_spec_snapshot(state, self.dir), [])
        _write(self.dir / "SPEC.md", "# SPEC v2\n")
        self.assertTrue(st.validate_spec_snapshot(state, self.dir))


class PersistenceTests(unittest.TestCase):
    def test_write_y_load_state(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            st.write_state(d, {"schema": st.SCHEMA_NAME, "a": 1})
            self.assertEqual(st.load_state_json(d)["a"], 1)

    def test_load_state_json_invalido_devuelve_none(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / st.STATE_FILE).write_text("{no json", encoding="utf-8")
            self.assertIsNone(st.load_state_json(d))

    def test_carry_over_conserva_sellos(self):
        state = {"schema": st.SCHEMA_NAME}
        prev = {"sealed_docs": {"X": "y"}, "spec_hashes": [1], "approvers": ["h"]}
        out = st.carry_over_aux_fields(state, prev)
        self.assertEqual(out["sealed_docs"], {"X": "y"})
        self.assertEqual(out["spec_hashes"], [1])
        self.assertEqual(out["approvers"], ["h"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
