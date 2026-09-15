"""Tests unitarios del modelo de estado (`fia_harness.core.state`)."""

import json
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
        self.assertEqual(state["schema_version"], st.SCHEMA_VERSION)

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

    def test_evidencia_ausente_sugiere_la_recuperacion(self):
        """ADR-004: el error de evidencia explica cómo salir del atasco (--reopen)."""
        md = VALID_MD.replace("| F0 | Repo | Funcionando | — | [ ] Pendiente |",
                              "| F0 | Repo | Funcionando | — | [x] Listo |")
        md = md.replace("## Checkpoints de Contexto Recientes\n- **M0:** Arranque completado.\n",
                        "## Checkpoints de Contexto Recientes\n- **M0:** Arranque completado.\n"
                        "- **F0:** Repo listo.\n")
        _write(self.dir / "PROGRESS.md", md)
        _write(self.dir / "TASK-F0.md", "# TASK-F0\nInforme.\n")
        errors = st.validate_state(st.compile_state_from_md(md), self.dir)
        self.assertTrue(any("--reopen F0" in e for e in errors), errors)

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


class SchemaAndMigrationTests(unittest.TestCase):
    """F3: schema 3.0, IDs estables, timestamps, huella y migración con backup."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "PROGRESS.md", VALID_MD)

    def test_write_state_asigna_ids_timestamps_y_huella(self):
        st.write_state(self.dir, st.compile_state_from_md(VALID_MD))
        stored = st.load_state_json(self.dir)
        self.assertEqual(stored["schema_version"], st.SCHEMA_VERSION)
        self.assertIn("compiled_at", stored)
        self.assertTrue(stored["state_sha256"])
        self.assertEqual(stored["checkpoints"][0]["id"], "CP-M0")
        self.assertIn("recorded_at", stored["checkpoints"][0])
        self.assertEqual(st.validate_state_integrity(stored), [])

    def test_recorded_at_se_conserva_entre_syncs(self):
        st.write_state(self.dir, st.compile_state_from_md(VALID_MD))
        first = st.load_state_json(self.dir)["checkpoints"][0]["recorded_at"]
        carried = st.carry_over_aux_fields(st.compile_state_from_md(VALID_MD),
                                           st.load_state_json(self.dir))
        st.write_state(self.dir, carried)
        self.assertEqual(st.load_state_json(self.dir)["checkpoints"][0]["recorded_at"], first)

    def test_migracion_legacy_crea_backup_y_reescribe_3_0(self):
        legacy = {"schema": st.LEGACY_SCHEMA, "process_phases": [], "execution_phases": [],
                  "checkpoints": []}
        (self.dir / st.STATE_FILE).write_text(json.dumps(legacy), encoding="utf-8")
        st.write_state(self.dir, st.compile_state_from_md(VALID_MD))
        self.assertTrue((self.dir / (st.STATE_FILE + ".bak")).exists())
        self.assertEqual(st.load_state_json(self.dir)["schema_version"], st.SCHEMA_VERSION)

    def test_validate_acepta_schema_legacy(self):
        legacy = st.compile_state_from_md(VALID_MD)
        legacy.pop("schema_version")
        legacy["schema"] = st.LEGACY_SCHEMA
        self.assertEqual(st.validate_state(legacy, self.dir), [])

    def test_validate_rechaza_schema_desconocido(self):
        state = st.compile_state_from_md(VALID_MD)
        state["schema_version"] = "9.9"
        self.assertTrue(any("schema_version" in e for e in st.validate_state(state, self.dir)))


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
