"""Tests del router de carril (`fia_harness.core.router`, v3.3, ADR-010)."""

import contextlib
import io
import unittest

from fia_harness import cli
from fia_harness.core import router


class ClassifyTests(unittest.TestCase):
    def test_allowlist_docs_propone_lite(self):
        result = router.classify("actualizar la documentación del README")
        self.assertEqual(result["lane"], "LITE")
        self.assertTrue(result["categories"])

    def test_allowlist_tests_propone_lite(self):
        self.assertEqual(router.classify("añadir tests del parser")["lane"], "LITE")

    def test_allowlist_fix_acotado_propone_lite(self):
        self.assertEqual(router.classify("corregir el bug de paginación")["lane"], "LITE")

    def test_allowlist_refactor_local_propone_lite(self):
        self.assertEqual(router.classify("refactor local de utils")["lane"], "LITE")

    def test_varias_categorias_allowlist_siguen_siendo_lite(self):
        result = router.classify("fix de typo en el README")
        self.assertEqual(result["lane"], "LITE")
        self.assertGreaterEqual(len(result["categories"]), 2)

    def test_login_camuflado_fuerza_full(self):
        result = router.classify("corregir bug en login")
        self.assertEqual(result["lane"], "FULL")
        self.assertIn("login", result["risk_signals"])

    def test_password_fuerza_full(self):
        self.assertEqual(router.classify("actualizar password del usuario")["lane"], "FULL")

    def test_jwt_fuerza_full(self):
        self.assertEqual(router.classify("cambiar el JWT del middleware")["lane"], "FULL")

    def test_pagos_fuerza_full(self):
        self.assertEqual(router.classify("corregir bug de facturación")["lane"], "FULL")

    def test_ambiguo_sin_allowlist_fuerza_full(self):
        result = router.classify("mejorar el sistema de recomendaciones")
        self.assertEqual(result["lane"], "FULL")
        self.assertIn("fail-closed", result["reason"])

    def test_vacio_fuerza_full(self):
        self.assertEqual(router.classify("")["lane"], "FULL")

    def test_determinista(self):
        text = "actualizar la documentación del README"
        self.assertEqual(router.classify(text), router.classify(text))


class CliRouteTests(unittest.TestCase):
    def test_cli_route_lite(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["route", "actualizar docs del README"])
        self.assertEqual(code, 0)
        self.assertIn("Carril: LITE", out.getvalue())

    def test_cli_route_full_por_riesgo(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["route", "corregir bug en login"])
        self.assertEqual(code, 0)
        self.assertIn("Carril: FULL", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
