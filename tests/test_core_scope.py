"""Tests del gate de scope (`fia_harness.core.scope`, v3.2)."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from fia_harness.core import scope


def _write(path, text):
    path.write_text(text, encoding="utf-8")


def _git(project_dir, *args):
    subprocess.run(["git", *args], cwd=project_dir, check=True,
                   capture_output=True, text=True)


class DeclaredScopeTests(unittest.TestCase):
    def test_lee_globs_de_la_seccion(self):
        text = ("# TASK-F1\n\n## Alcance permitido (scope)\n- src/auth/**\n"
                "- tests/test_auth.py\n\n## Otra\n- no cuenta\n")
        self.assertEqual(scope.declared_scope(text), ["src/auth/**", "tests/test_auth.py"])

    def test_placeholder_no_cuenta(self):
        text = "# TASK-F1\n\n## Alcance permitido (scope)\n- <pendiente de completar>\n"
        self.assertEqual(scope.declared_scope(text), [])

    def test_sin_seccion_vacio(self):
        self.assertEqual(scope.declared_scope("# TASK-F1\n## Contexto\n- x\n"), [])


class ValidateScopeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def _state(self, status="in_progress"):
        return {"schema_version": "3.0", "process_phases": [],
                "execution_phases": [{"id": "F1", "title": "x", "objective": "y",
                                      "depends_on": [], "depends_on_notes": "",
                                      "status": status}],
                "checkpoints": []}

    def _git_repo(self):
        _git(self.dir, "init", "-q")
        _git(self.dir, "config", "user.email", "t@t")
        _git(self.dir, "config", "user.name", "t")

    def _commit_all(self):
        _git(self.dir, "add", ".")
        _git(self.dir, "commit", "-qm", "init")

    def test_sin_git_se_omite(self):
        errors, note = scope.validate_scope(self.dir, self._state())
        self.assertEqual(errors, [])
        self.assertIn("no es un repo git", note)

    def test_sin_fase_en_curso_se_omite(self):
        self._git_repo()
        errors, note = scope.validate_scope(self.dir, self._state(status="pending"))
        self.assertIn("sin fase F en curso", note)

    def test_sin_alcance_declarado_se_omite(self):
        self._git_repo()
        _write(self.dir / "TASK-F1.md",
               "# TASK-F1\n## Alcance permitido (scope)\n- <pendiente>\n")
        errors, note = scope.validate_scope(self.dir, self._state())
        self.assertIn("no declara alcance", note)

    def test_cambio_fuera_de_alcance_falla(self):
        self._git_repo()
        _write(self.dir / "TASK-F1.md",
               "# TASK-F1\n## Alcance permitido (scope)\n- src/auth/**\n")
        self._commit_all()
        _write(self.dir / "otro.txt", "fuera de alcance")
        errors, note = scope.validate_scope(self.dir, self._state())
        self.assertTrue(any("fuera del alcance" in e for e in errors), errors)

    def test_cambio_dentro_de_alcance_pasa(self):
        self._git_repo()
        _write(self.dir / "TASK-F1.md",
               "# TASK-F1\n## Alcance permitido (scope)\n- src/auth/**\n")
        self._commit_all()
        (self.dir / "src" / "auth").mkdir(parents=True)
        _write(self.dir / "src" / "auth" / "login.py", "x")
        errors, note = scope.validate_scope(self.dir, self._state())
        self.assertEqual(errors, [])
        self.assertIn("1 archivo(s)", note)


if __name__ == "__main__":
    unittest.main(verbosity=2)
