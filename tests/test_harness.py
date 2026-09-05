"""Tests del kit FIA Harness: parsers y ciclo completo de los dos scripts.

Ejecutar desde la raíz del kit:
    python -m unittest discover tests -v

Sin dependencias externas. El test e2e se ejecuta siempre en una carpeta
temporal (TemporaryDirectory): nunca modifica el repositorio del kit.
"""

import contextlib
import datetime
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEMPLATE_FILES = [
    "INICIO_PROYECTO.md", "SECURITY.md", "AEO_GEO_SEO.md", "UI_UX_EXCLUSIVA.md",
    "SKILLS_MCP.md", "TASK_TEMPLATE.md", "TASK_LITE_TEMPLATE.md", "QUICKSTART_LITE.md",
]


def _load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bootstrap = _load_module("bootstrap")
task_generator = _load_module("task_generator")

PROGRESS_SAMPLE = """# PROGRESS.md

**Fase activa:** F1

## Fases del Proceso

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| **M0** | Bootstrap del harness | Plantillas activas | — | [x] Listo |
| **M1** | Entrevista técnica | Seguridad completada | M0 | [ ] Pendiente |

## Fases de Ejecución

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| F0 | Bootstrap del repo | Repo funcionando | SPEC aprobado | [x] Listo |
| F1 | Modelo de datos + migraciones | BBDD creada | F0 | [ ] Pendiente |
| F2 | Backend core | API mínima | F1 | [ ] Pendiente |
"""


class ParseProgressTableTests(unittest.TestCase):
    def test_lee_varias_tablas_y_quita_negritas(self):
        rows = task_generator.parse_progress_table(PROGRESS_SAMPLE)
        self.assertEqual([r["phase"] for r in rows], ["M0", "M1", "F0", "F1", "F2"])

    def test_detecta_siguiente_fase_ejecucion(self):
        rows = task_generator.parse_progress_table(PROGRESS_SAMPLE)
        self.assertEqual(task_generator.detect_next_phase(rows), "F1")

    def test_extrae_objetivo_y_dependencias(self):
        rows = task_generator.parse_progress_table(PROGRESS_SAMPLE)
        f1 = task_generator.get_phase_row(rows, "F1")
        self.assertEqual(f1["objective"], "Modelo de datos + migraciones / BBDD creada")
        self.assertEqual(f1["dependencies"], "F0")

    def test_columna_combinada_no_se_duplica(self):
        tabla = (
            "| Fase | Entregable / Objetivo | Estado |\n"
            "| --- | --- | --- |\n"
            "| F0 | Repo funcionando | [ ] Pendiente |\n"
        )
        rows = task_generator.parse_progress_table(tabla)
        self.assertEqual(rows[0]["objective"], "Repo funcionando")

    def test_filas_sin_codigo_de_fase_se_ignoran(self):
        tabla = (
            "| Fase | Objetivo | Estado |\n"
            "| --- | --- | --- |\n"
            "| — | nota suelta | [ ] Pendiente |\n"
            "| F1 | Real | [ ] Pendiente |\n"
        )
        rows = task_generator.parse_progress_table(tabla)
        self.assertEqual([r["phase"] for r in rows], ["F1"])

    def test_sin_fases_pendientes_devuelve_none(self):
        contenido = PROGRESS_SAMPLE.replace("[ ] Pendiente", "[x] Listo")
        rows = task_generator.parse_progress_table(contenido)
        self.assertIsNone(task_generator.detect_next_phase(rows))


class ExtractSectionTests(unittest.TestCase):
    """Contra los documentos reales del kit: extract_section debe capturar tablas."""

    @classmethod
    def setUpClass(cls):
        cls.ui_ux = (ROOT / "UI_UX_EXCLUSIVA.md").read_text(encoding="utf-8")
        cls.security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

    def test_captura_tabla_del_gate_de_entrada_completa(self):
        gate = task_generator.extract_section(self.ui_ux, "Gate de entrada")
        self.assertIn("| Producto |", gate)
        self.assertIn("Restricciones", gate)
        self.assertNotIn("Design DNA es la decisión", gate)  # no se pasa de sección

    def test_captura_seccion_auth_y_corta_en_la_siguiente(self):
        auth = task_generator.extract_section(self.security, "Autenticación")
        self.assertIn("bcrypt", auth)
        self.assertIn("2FA/MFA", auth)
        self.assertNotIn("RLS (Row Level Security) activado", auth)  # eso es 2.2

    def test_captura_seccion_infraestructura(self):
        infra = task_generator.extract_section(self.security, "Infraestructura")
        self.assertIn("Fail2ban", infra)


class InjectMarkerTests(unittest.TestCase):
    SNIPPET = (
        "antes\n"
        "<!-- INJECT:SECURITY_CHECKLIST -->\ncontenido antiguo\n<!-- /INJECT -->\n"
        "después\n"
    )

    def test_sustituye_bloque_completo_con_marcadores(self):
        resultado, encontrado = task_generator.inject(self.SNIPPET, "security", "NUEVO")
        self.assertTrue(encontrado)
        self.assertIn("NUEVO", resultado)
        self.assertNotIn("contenido antiguo", resultado)
        self.assertNotIn("<!-- INJECT", resultado)

    def test_marcador_ausente_devuelve_found_false(self):
        resultado, encontrado = task_generator.inject("sin marcadores", "security", "X")
        self.assertFalse(encontrado)
        self.assertEqual(resultado, "sin marcadores")


class KeywordHeuristicTests(unittest.TestCase):
    def test_entrevista_no_activa_nada(self):
        row = {"title": "Entrevista de Descubrimiento Técnico",
               "objective": "Cerrar decisiones con el humano"}
        reqs = task_generator.analyze_phase_requirements(row)
        self.assertEqual(reqs, {"security": False, "visibility": False, "ui_ux": False})

    def test_f1_modelo_de_datos_activa_solo_seguridad(self):
        row = {"title": "Modelo de datos + migraciones",
               "objective": "BBDD creada y versionada"}
        reqs = task_generator.analyze_phase_requirements(row)
        self.assertTrue(reqs["security"])
        self.assertFalse(reqs["visibility"])
        self.assertFalse(reqs["ui_ux"])

    def test_frontend_con_api_activa_seguridad_por_exceso(self):
        # Comportamiento actual (documentado): "api" es palabra clave de seguridad.
        # Peca por exceso de checklist, nunca por defecto.
        row = {"title": "Frontend core", "objective": "UI navegable conectada a API"}
        reqs = task_generator.analyze_phase_requirements(row)
        self.assertTrue(reqs["security"])
        self.assertTrue(reqs["ui_ux"])


class StripTemplateHeaderTests(unittest.TestCase):
    def test_plantilla_completa_empieza_en_el_encabezado_de_tarea(self):
        plantilla = (ROOT / "TASK_TEMPLATE.md").read_text(encoding="utf-8")
        recortada = task_generator.strip_template_meta_header(plantilla, "TASK_TEMPLATE.md")
        self.assertTrue(recortada.startswith("# TASK-<N>"))
        self.assertNotIn("Cómo usar esta plantilla", recortada)
        self.assertIn("FASE J2", recortada)  # el cuerpo llega íntegro

    def test_plantilla_lite_empieza_en_task_quick(self):
        plantilla = (ROOT / "TASK_LITE_TEMPLATE.md").read_text(encoding="utf-8")
        recortada = task_generator.strip_template_meta_header(plantilla, "TASK_LITE_TEMPLATE.md")
        self.assertTrue(recortada.startswith("# TASK-QUICK"))

    def test_plantilla_sin_encabezado_de_tarea_se_devuelve_integra(self):
        self.assertEqual(
            task_generator.strip_template_meta_header("hola\nmundo", "x.md"),
            "hola\nmundo",
        )


class DetectLiteModeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_valor_declarado_lite_activa(self):
        self.assertTrue(task_generator.detect_lite_mode("Modo de trabajo: Lite", self.dir, False))

    def test_mencion_de_lite_como_opcion_no_activa(self):
        contexto = ("**Modo de trabajo:** Pendiente de entrevista técnica "
                    "(Completo / Lite — ver `QUICKSTART_LITE.md`)")
        self.assertFalse(task_generator.detect_lite_mode(contexto, self.dir, False))

    def test_quick_context_presente_activa(self):
        (self.dir / "QUICK_CONTEXT.md").write_text("brief", encoding="utf-8")
        self.assertTrue(task_generator.detect_lite_mode("", self.dir, False))

    def test_flag_forzado_gana_siempre(self):
        self.assertTrue(task_generator.detect_lite_mode("Modo de trabajo: Completo", self.dir, True))


class ExtractPrdMetadataTests(unittest.TestCase):
    def _prd(self, tmp, contenido):
        path = tmp / "PRD.md"
        path.write_text(contenido, encoding="utf-8")
        return bootstrap.extract_prd_metadata(path)

    def test_extrae_todas_las_secciones(self):
        with tempfile.TemporaryDirectory() as d:
            meta = self._prd(Path(d), (
                "# Reservas Fácil\n\n## Problema\nPerder reservas por WhatsApp.\n\n"
                "## Usuarios\nRestaurantes pequeños.\n\n## Funcionalidades\n"
                "* Calendario de reservas\n* Notificaciones\n\n"
                "## Fuera de alcance\n* Pagos en línea\n"
            ))
        self.assertEqual(meta["title"], "Reservas Fácil")
        self.assertIn("WhatsApp", meta["problem"])
        self.assertIn("Calendario de reservas", meta["features"])
        self.assertIn("Pagos en línea", meta["out_of_scope"])
        self.assertEqual(meta["unresolved"], [])

    def test_prd_sin_encabezados_marca_unresolved(self):
        with tempfile.TemporaryDirectory() as d:
            meta = self._prd(Path(d), "# Mi Proyecto\nTexto sin secciones reconocibles.\n")
        self.assertEqual(meta["title"], "Mi Proyecto")
        for campo in ("problem", "users", "features", "out_of_scope"):
            self.assertIn(campo, meta["unresolved"])


class FindPrdFileTests(unittest.TestCase):
    def _tmp_dir(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_archivos_de_control_no_son_prd(self):
        d = self._tmp_dir()
        for nombre in ("README.md", "CHANGELOG.md", "NOTES.md", "QUICK_CONTEXT.md"):
            (d / nombre).write_text("x", encoding="utf-8")
        self.assertIsNone(bootstrap.find_prd_file(d))

    def test_las_tareas_y_plantillas_no_son_prd(self):
        d = self._tmp_dir()
        (d / "TASK-F1.md").write_text("x", encoding="utf-8")
        (d / "CHANGELOG_FIXES.md").write_text("x", encoding="utf-8")
        self.assertIsNone(bootstrap.find_prd_file(d))

    def test_md_suelto_si_sirve_como_pista(self):
        d = self._tmp_dir()
        (d / "README.md").write_text("x", encoding="utf-8")
        (d / "Notas de reunion.md").write_text("x", encoding="utf-8")
        prd = bootstrap.find_prd_file(d)
        self.assertIsNotNone(prd)
        self.assertEqual(prd.name, "Notas de reunion.md")

    def test_nombre_estandar_tiene_prioridad(self):
        d = self._tmp_dir()
        (d / "Notas de reunion.md").write_text("x", encoding="utf-8")
        (d / "PRD.md").write_text("x", encoding="utf-8")
        self.assertEqual(bootstrap.find_prd_file(d).name, "PRD.md")


def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# Estado de referencia SANO para los tests de estado/sync: todas las fases
# pendientes salvo M0 (cerrada y con su checkpoint). Cerrar una F requeriría
# además su TASK-Fx.md (Regla de Oro nº7), así que ese caso se construye a mano
# en cada test que lo necesita.
VALID_STATE_MD = (PROGRESS_SAMPLE.replace(
    "| F0 | Bootstrap del repo | Repo funcionando | SPEC aprobado | [x] Listo |",
    "| F0 | Bootstrap del repo | Repo funcionando | SPEC aprobado | [ ] Pendiente |")
    + "\n## Checkpoints de Contexto Recientes\n- **M0:** Arranque completado.\n"
)


class StateCompileTests(unittest.TestCase):
    def test_compila_fases_y_checkpoints(self):
        state = task_generator.compile_state_from_md(VALID_STATE_MD)
        self.assertEqual([p["id"] for p in state["process_phases"]], ["M0", "M1"])
        self.assertEqual([p["id"] for p in state["execution_phases"]], ["F0", "F1", "F2"])
        self.assertEqual(state["execution_phases"][1]["status"], "pending")
        self.assertEqual(state["checkpoints"],
                         [{"phase": "M0", "summary": "Arranque completado."}])

    def test_texto_libre_en_dependencias_no_se_valida_como_fase(self):
        tabla = ("| Fase | Objetivo | Entregable | Depende de | Estado |\n"
                 "| --- | --- | --- | --- | --- |\n"
                 "| F0 | Bootstrap | Repo | SPEC aprobado | [ ] Pendiente |\n")
        entry = task_generator.compile_state_from_md(tabla)["execution_phases"][0]
        self.assertEqual(entry["depends_on"], [])
        self.assertEqual(entry["depends_on_notes"], "SPEC aprobado")

    def test_fingerprint_ignora_updated(self):
        a = task_generator.compile_state_from_md(VALID_STATE_MD, updated="2026-01-01")
        b = task_generator.compile_state_from_md(VALID_STATE_MD, updated="2026-12-31")
        self.assertEqual(task_generator.state_fingerprint(a), task_generator.state_fingerprint(b))


class StateValidateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "PROGRESS.md", VALID_STATE_MD)

    def _state(self, md=None):
        return task_generator.compile_state_from_md(md or VALID_STATE_MD)

    def test_estado_valido_no_produce_errores(self):
        self.assertEqual(task_generator.validate_state(self._state(), self.dir), [])

    def test_fase_cerrada_con_dependencia_pendiente(self):
        md = VALID_STATE_MD.replace(
            "| F1 | Modelo de datos + migraciones | BBDD creada | F0 | [ ] Pendiente |",
            "| F1 | Modelo de datos + migraciones | BBDD creada | F0 | [x] Listo |")
        errors = task_generator.validate_state(self._state(md), self.dir)
        # F0 sigue pendiente, así que cerrar F1 viola tres reglas a la vez:
        # dependencia abierta, TASK-F1.md inexistente y checkpoint ausente
        self.assertTrue(any("dependencia F0 no" in e for e in errors), errors)
        self.assertTrue(any("TASK-F1.md" in e for e in errors), errors)
        self.assertTrue(any("checkpoint" in e for e in errors), errors)

    def test_dependencia_inexistente(self):
        md = VALID_STATE_MD.replace(
            "| F0 | Bootstrap del repo | Repo funcionando | SPEC aprobado | [ ] Pendiente |",
            "| F0 | Bootstrap del repo | Repo funcionando | F9 | [ ] Pendiente |")
        errors = task_generator.validate_state(self._state(md), self.dir)
        self.assertTrue(any("F9" in e for e in errors), errors)

    def test_estado_fuera_del_enum(self):
        state = self._state()
        state["process_phases"][1]["status"] = "acabada"
        errors = task_generator.validate_state(state, self.dir)
        self.assertTrue(any("no válido" in e for e in errors), errors)

    def test_fase_duplicada(self):
        state = self._state()
        state["execution_phases"].append(dict(state["execution_phases"][0]))
        errors = task_generator.validate_state(state, self.dir)
        self.assertTrue(any("duplicada" in e for e in errors), errors)

    def test_aprobacion_citada_no_registrada(self):
        _write(self.dir / "DECISIONS.md",
               "# DECISIONS.md\n\n## Aprobaciones\n\n- **APPROVAL-001** (2026-09-05) · "
               "Fase: F2 · Acción: instalar Skill X · Aprobado por: Humano\n")
        _write(self.dir / "TASK-F1.md", "Informe. Aprobación citada: APPROVAL-009.\n")
        errors = task_generator.validate_state(self._state(), self.dir)
        self.assertTrue(any("APPROVAL-009" in e for e in errors), errors)
        _write(self.dir / "TASK-F1.md", "Informe. Aprobación citada: APPROVAL-001.\n")
        errors = task_generator.validate_state(self._state(), self.dir)
        self.assertFalse(any("APPROVAL" in e for e in errors), errors)

    def test_entrada_aprobacion_incompleta(self):
        _write(self.dir / "DECISIONS.md",
               "## Aprobaciones\n\n- **APPROVAL-002** aprobó cosas sin más\n")
        errors = task_generator.validate_state(self._state(), self.dir)
        self.assertTrue(any("incompleta" in e for e in errors), errors)

    def test_mencion_aprobacion_sin_id_no_es_entrada(self):
        _write(self.dir / "DECISIONS.md",
               "## Aprobaciones\n\n*Formato: APPROVAL-NNN (fecha) · Acción · Aprobado por*\n")
        self.assertEqual(task_generator.validate_state(self._state(), self.dir), [])


class SyncCheckApprovalTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        _write(self.dir / "PROGRESS.md", VALID_STATE_MD)

    def _expect_system_exit(self, fn):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                fn()
        self.assertEqual(ctx.exception.code, 1)
        return stderr.getvalue()

    def test_sync_genera_y_check_pasa(self):
        task_generator.cmd_sync(self.dir)
        self.assertTrue((self.dir / "progress.json").exists())
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            task_generator.cmd_check(self.dir)
        self.assertIn("Estado del harness válido", stdout.getvalue())

    def test_check_detecta_drift_tras_edicion_manual(self):
        task_generator.cmd_sync(self.dir)
        _write(self.dir / "PROGRESS.md", VALID_STATE_MD.replace(
            "| F2 | Backend core | API mínima | F1 | [ ] Pendiente |",
            "| F2 | Backend core | API mínima | F1 | [x] Listo |"))
        stderr = self._expect_system_exit(lambda: task_generator.cmd_check(self.dir))
        self.assertIn("desincronizados", stderr)
        # --sync es fail-closed: el estado editado es inválido y NO se escribe
        stderr = self._expect_system_exit(lambda: task_generator.cmd_sync(self.dir))
        self.assertIn("NO se ha escrito", stderr)
        self.assertTrue((self.dir / "progress.json").exists())  # el anterior se conserva

    def test_approval_registra_y_autoincrementa(self):
        _write(self.dir / "DECISIONS.md", "# DECISIONS.md\n\n## Registro\n* ADR-000\n")
        task_generator.cmd_approval(self.dir, "instalar Skill X v1.2", "F2", "chat 5-sep", "Humano")
        texto = (self.dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("**APPROVAL-001**", texto)
        self.assertIn(datetime.date.today().isoformat(), texto)
        self.assertIn("Acción: instalar Skill X v1.2", texto)
        self.assertIn("Aprobado por: Humano", texto)
        self.assertIn("Ref: chat 5-sep", texto)
        task_generator.cmd_approval(self.dir, "conectar MCP supabase", None, "", "María")
        texto = (self.dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("**APPROVAL-002**", texto)
        self.assertIn("Aprobado por: María", texto)
        state = task_generator.compile_state_from_md(VALID_STATE_MD)
        self.assertEqual(task_generator.validate_state(state, self.dir), [])


class EndToEndTests(unittest.TestCase):
    """Ciclo completo bootstrap -> task_generator en carpeta temporal."""

    PRD = (
        "# Reservas VectorIA\n\n## Problema\nLos restaurantes pierden reservas.\n\n"
        "## Usuarios\nRestaurantes de 10-30 mesas.\n\n## Funcionalidades\n"
        "* Buscador semántico con embeddings\n* Panel de administración\n\n"
        "## Fuera de alcance\n* App móvil nativa\n"
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        docs = self.dir / "docs"
        docs.mkdir()
        for nombre in TEMPLATE_FILES:
            shutil.copy2(ROOT / nombre, docs / nombre)
        shutil.copy2(ROOT / "PROYECTOS RAG Y VECTORIALES" / bootstrap.RAG_MODULE_NAME,
                     docs / bootstrap.RAG_MODULE_NAME)
        (self.dir / "PRD.md").write_text(self.PRD, encoding="utf-8")

    def _run(self, *args):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        return subprocess.run(
            [sys.executable, str(ROOT / args[0]), *args[1:]],
            cwd=self.dir, capture_output=True, text=True, encoding="utf-8", env=env,
        )

    def test_bootstrap_genera_archivos_y_activa_rag(self):
        result = self._run("bootstrap.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        for nombre in ("CONTEXT.md", "PROGRESS.md", "DECISIONS.md",
                       bootstrap.RAG_MODULE_NAME, "SECURITY.md",
                       "progress.json", ".github/workflows/harness.yml"):
            self.assertTrue((self.dir / nombre).exists(), f"falta {nombre}")
        contexto = (self.dir / "CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("Reservas VectorIA", contexto)
        self.assertIn("Buscador semántico con embeddings", contexto)
        progreso = (self.dir / "PROGRESS.md").read_text(encoding="utf-8")
        self.assertIn("| M0 |", progreso)
        self.assertIn("[x] Listo |", progreso)
        # Las fases F no se adivinan: fuera del comentario de ejemplo no hay filas F
        sin_comentarios = re.sub(r"<!--.*?-->", "", progreso, flags=re.DOTALL)
        self.assertNotIn("| F0 |", sin_comentarios)
        decisiones = (self.dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("## Aprobaciones", decisiones)

    def test_check_pasa_en_estado_recien_bootstrapeado(self):
        """El estado inicial que emite bootstrap.py debe ser verde para el CI."""
        self._run("bootstrap.py")
        result = self._run("task_generator.py", "--check")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Estado del harness válido", result.stdout)

    def test_generador_auto_sana_el_estado_tras_edicion_manual(self):
        self._run("bootstrap.py")
        progreso = (self.dir / "PROGRESS.md").read_text(encoding="utf-8")
        editado = progreso.replace(
            "`SPEC.md` redactado y aprobado explícitamente por el humano",
            "`SPEC.md` redactado y aprobado explícitamente por el humano (revisado v2)")
        (self.dir / "PROGRESS.md").write_text(editado, encoding="utf-8")
        result = self._run("task_generator.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("recompilado", result.stdout + result.stderr)
        estado = (self.dir / "progress.json").read_text(encoding="utf-8")
        self.assertIn("(revisado v2)", estado)

    def test_check_falla_tras_edicion_manual_sin_sync(self):
        self._run("bootstrap.py")
        progreso = (self.dir / "PROGRESS.md").read_text(encoding="utf-8")
        editado = progreso.replace(
            "`SPEC.md` redactado y aprobado explícitamente por el humano",
            "`SPEC.md` redactado y aprobado explícitamente por el humano (revisado v2)")
        (self.dir / "PROGRESS.md").write_text(editado, encoding="utf-8")
        result = self._run("task_generator.py", "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("desincronizados", result.stderr)

    def test_task_generator_avisa_mientras_no_haya_fases_f(self):
        self._run("bootstrap.py")
        result = self._run("task_generator.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fases de proceso pendientes", result.stdout)

    def test_ciclo_completo_genera_task_sin_cabecera_meta(self):
        self._run("bootstrap.py")
        progreso = (self.dir / "PROGRESS.md").read_text(encoding="utf-8")
        progreso = progreso.replace("**Fase activa:** M1", "**Fase activa:** F1")
        progreso = re.sub(r"(\| M\d \|.*?)\[ \] Pendiente \|", r"\1[x] Listo |", progreso)
        progreso = progreso.replace(
            "| Fase | Objetivo | Entregable | Depende de | Estado |\n"
            "| --- | --- | --- | --- | --- |\n\n## Checkpoints",
            "| Fase | Objetivo | Entregable | Depende de | Estado |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| F0 | Bootstrap del repo, tooling | Repo funcionando | SPEC aprobado | [x] Listo |\n"
            "| F1 | Modelo de datos + migraciones | BBDD creada | F0 | [ ] Pendiente |\n"
            "| F2 | Frontend core | UI navegable | F1 | [ ] Pendiente |\n\n"
            "## Checkpoints",
        )
        (self.dir / "PROGRESS.md").write_text(progreso, encoding="utf-8")
        # F0 va cerrada en la tabla simulada y M1-M3 se cierran en el mismo bloque:
        # el estado validado exige TASK para F0 y checkpoint para cada fase cerrada
        # (Reglas de Oro 4 y 7), así que el escenario los incluye
        _write(self.dir / "TASK-F0.md", "# TASK-F0 — BOOTSTRAP DEL REPO\n\nInforme: repo funcionando.\n")
        progreso = (self.dir / "PROGRESS.md").read_text(encoding="utf-8")
        progreso = progreso.replace(
            "## Checkpoints de Contexto Recientes\n",
            "## Checkpoints de Contexto Recientes\n"
            "- **M1:** Entrevista completada; SECURITY.md y AEO_GEO_SEO.md rellenados.\n"
            "- **M2:** SPEC.md redactado y aprobado por el humano.\n"
            "- **M3:** Plan de fases F0-F3 derivado de SPEC.md.\n"
            "- **F0:** Repo inicial funcionando y CI básico en verde.\n")
        (self.dir / "PROGRESS.md").write_text(progreso, encoding="utf-8")

        result = self._run("task_generator.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        task = (self.dir / "TASK-F1.md")
        self.assertTrue(task.exists())
        primera = task.read_text(encoding="utf-8").splitlines()[0]
        self.assertTrue(primera.startswith("# TASK-F1"), primera)  # sin cabecera meta
        contenido = task.read_text(encoding="utf-8")
        self.assertIn("Checklist de Seguridad Obligatorio", contenido)
        self.assertIn("No aplica: esta tarea no toca superficie pública", contenido)
        # El artefacto de estado también se auto-sanó con la tabla F pegada a mano
        estado = json.loads((self.dir / "progress.json").read_text(encoding="utf-8"))
        self.assertEqual([p["id"] for p in estado["execution_phases"]],
                         ["F0", "F1", "F2"])
        self.assertEqual(estado["execution_phases"][0]["status"], "done")

    def test_fase_de_proceso_se_rechaza(self):
        self._run("bootstrap.py")
        result = self._run("task_generator.py", "--phase", "M1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("fase de PROCESO", result.stderr)

    def test_fase_inexistente_falla_listando_disponibles(self):
        self._run("bootstrap.py")
        result = self._run("task_generator.py", "--phase", "F99")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no aparece", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
