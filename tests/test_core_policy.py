"""Tests unitarios de las reglas y heurísticas (`fia_harness.core.policy`)."""

import unittest

from fia_harness.core import policy


class AnalyzePhaseRequirementsTests(unittest.TestCase):
    def test_entrevista_no_activa_nada(self):
        reqs = policy.analyze_phase_requirements(
            {"title": "Entrevista", "objective": "Cerrar decisiones"})
        self.assertEqual(reqs, {"security": False, "visibility": False, "ui_ux": False})

    def test_bbdd_activa_seguridad(self):
        reqs = policy.analyze_phase_requirements(
            {"title": "Modelo de datos", "objective": "BBDD versionada"})
        self.assertTrue(reqs["security"])

    def test_frontend_activa_visibilidad_y_ui(self):
        reqs = policy.analyze_phase_requirements(
            {"title": "Landing pública", "objective": "Frontend con UI"})
        self.assertTrue(reqs["visibility"])
        self.assertTrue(reqs["ui_ux"])

    def test_limite_de_palabra_evita_falsos_positivos(self):
        # "vista" dentro de "entrevista" no debe activar UI/UX (\b en el regex)
        reqs = policy.analyze_phase_requirements(
            {"title": "Entrevista", "objective": "sin palabras clave"})
        self.assertFalse(reqs["ui_ux"])


class InjectionConfigTests(unittest.TestCase):
    def test_marcadores_de_inyeccion(self):
        self.assertEqual(policy.INJECT_MARKERS["security"], "SECURITY_CHECKLIST")
        self.assertEqual(policy.INJECT_MARKERS["visibility"], "VISIBILITY_CHECKLIST")
        self.assertEqual(policy.INJECT_MARKERS["ui_ux"], "UIUX_CHECKLIST")

    def test_textos_de_no_aplica(self):
        self.assertIn("No aplica", policy.NOT_APPLICABLE_TEXT["ui_ux"])
        self.assertIn("No aplica", policy.NOT_APPLICABLE_TEXT["security"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
