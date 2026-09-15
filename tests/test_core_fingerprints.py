"""Tests unitarios de las huellas del estado (`fia_harness.core.fingerprints`)."""

import unittest

from fia_harness.core import fingerprints as fp


def _state(**overrides):
    state = {
        "schema_version": "3.0",
        "process_phases": [{"id": "M0", "title": "", "objective": "x", "depends_on": [],
                            "depends_on_notes": "", "status": "done"}],
        "execution_phases": [{"id": "F0", "title": "", "objective": "y", "depends_on": [],
                              "depends_on_notes": "", "status": "pending"}],
        "checkpoints": [{"id": "CP-M0", "phase": "M0", "summary": "ok", "evidence": "",
                         "evidence_file": None, "recorded_at": "2026-01-01T00:00:00"}],
        "compiled_at": "2026-01-01T00:00:00",
        "updated": "2026-01-01",
        "sealed_docs": {},
        "spec_hashes": [],
    }
    state.update(overrides)
    return state


class AuthorityProjectionTests(unittest.TestCase):
    def test_fingerprint_ignora_schema_ids_timestamps_y_sellos(self):
        a = _state()
        b = _state(schema_version="harness-state/1", compiled_at="2026-12-31T23:59:59",
                   updated="2026-12-31", sealed_docs={"X": "y"})
        b["checkpoints"] = [dict(b["checkpoints"][0], id="CP-OTRO",
                                 recorded_at="2027-01-01T00:00:00")]
        self.assertEqual(fp.state_fingerprint(a), fp.state_fingerprint(b))

    def test_fingerprint_detecta_cambio_de_autoridad(self):
        a = _state()
        b = _state()
        b["execution_phases"][0]["status"] = "done"
        self.assertNotEqual(fp.state_fingerprint(a), fp.state_fingerprint(b))

    def test_fingerprint_comparable_entre_schemas(self):
        legacy = {"schema": "harness-state/1", "process_phases": [], "execution_phases": [],
                  "checkpoints": []}
        actual = {"schema_version": "3.0", "process_phases": [], "execution_phases": [],
                  "checkpoints": []}
        self.assertEqual(fp.state_fingerprint(legacy), fp.state_fingerprint(actual))

    def test_evidencia_none_y_vacio_son_equivalentes(self):
        # Los estados antiguos guardaban evidence=None; el parser actual usa "".
        a = _state()
        b = _state()
        b["checkpoints"] = [dict(b["checkpoints"][0], evidence=None, evidence_file="")]
        self.assertEqual(fp.state_fingerprint(a), fp.state_fingerprint(b))


class IntegrityTests(unittest.TestCase):
    def test_huella_valida(self):
        state = _state()
        state["state_sha256"] = fp.state_sha256(state)
        self.assertEqual(fp.validate_state_integrity(state), [])

    def test_edicion_manual_detectada(self):
        state = _state()
        state["state_sha256"] = fp.state_sha256(state)
        state["compiled_at"] = "2020-01-01T00:00:00"
        self.assertTrue(fp.validate_state_integrity(state))

    def test_estado_sin_huella_no_aplica(self):
        self.assertEqual(fp.validate_state_integrity(_state()), [])

    def test_sha256_hex_conocido(self):
        self.assertEqual(fp.sha256_hex(b"abc"),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


if __name__ == "__main__":
    unittest.main(verbosity=2)
