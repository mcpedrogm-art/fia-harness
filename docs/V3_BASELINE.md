# docs/V3_BASELINE.md — Baseline v2.2.0

**Fase:** F0 (Baseline y dogfood) · **Fecha:** 2026-09-15
**Propósito:** congelar el comportamiento de FIA Harness v2.2.0 antes de cambiar
arquitectura (plan v3.0-core). Este documento es la referencia contra la que se
verifica "comportamiento equivalente" en F1–F7.

---

## 1. Entorno de referencia

| Dato | Valor |
| --- | --- |
| Sistema | Windows (consola cp1252 verificada en tests) |
| Python | 3.11.15 |
| Rama de trabajo v3 | `v3.0-core` (creada desde `main`) |
| Commit base | `c6ea8a2` ("Release: crear el GitHub Release automáticamente al etiquetar") |
| Tag | `v2.2.0` |
| Versión en `pyproject.toml` | `2.2.0` |

## 2. Baseline de tests

```text
Comando:  python -m unittest discover tests -v
Resultado: Ran 75 tests in 2.210s — OK (exit code 0)
Log crudo: docs/evidence/v2.2.0_unittest.log
```

CI del repo antes de v3:

- `.github/workflows/tests.yml`: suite `unittest` en matriz **3 SO × Python 3.10/3.11/3.12**
  + job **dogfood** (`fia_harness.cli init` en `_dogfood` → `bootstrap.py` → `--check`).
- `.github/workflows/release.yml`: al etiquetar `v*` → tests → build → **PyPI (OIDC)**
  → GitHub Release con notas desde `CHANGELOG_FIXES.md`.

## 3. Inventario CLI público (a preservar)

### `fia-harness` (console script, paquete PyPI)

```text
fia-harness init [-d/--dir DIR]
```

Monta un proyecto nuevo: plantillas en `docs/`, los dos scripts en la raíz, `PRD.md`
de partida. Idempotente (nunca sobrescribe).

### `python bootstrap.py` (proyecto de usuario, sin flags)

Crea carpetas (`src`, `tests`, `docs`, `infra`), copia plantillas de `docs/` a la raíz,
extrae metadatos del PRD → `CONTEXT.md` (con avisos "⚠️ Sin confirmar"), genera
`PROGRESS.md`, `progress.json` (con sellos), `.github/workflows/harness.yml`,
`DECISIONS.md`, y activa el módulo RAG si el PRD lo menciona.

### `python task_generator.py` (flags públicos)

```text
(nada)            Genera TASK-Fx.md de la primera fase F pendiente
-p/--phase F<N>   Fase explícita (rechaza fases M)
-l/--lite         Fuerza plantilla Lite
-d/--dir DIR      Directorio raíz del proyecto
--sync            Compila y valida PROGRESS.md → progress.json (fail-closed)
--check           Valida el estado sin modificar nada (lo que ejecuta el CI)
--state-optional  Permite --check sin progress.json (escape explícito)
--seal [DOC...]   Sella documentos normativos (SHA-256) en progress.json
--approval ACCION Registra APPROVAL-NNN en DECISIONS.md (+ snapshot de SPEC.md)
--ref / --approved-by  Metadatos de la aprobación
--reopen F<N> --reason "..."  Reapertura auditada (done → in_progress)
--stats           Resumen del estado (fases, checkpoints, aprobaciones, sellos)
```

## 4. Modelo de estado actual (`harness-state/1`)

```json
{
  "schema": "harness-state/1",
  "process_phases":  [{ "id": "M0", "title", "objective", "depends_on", "depends_on_notes", "status" }],
  "execution_phases":[{ "id": "F0", "title", "objective", "depends_on", "depends_on_notes", "status" }],
  "checkpoints":     [{ "phase", "summary", "evidence", "evidence_file" }],
  "updated": "AAAA-MM-DD",
  "sealed_docs":     { "ARCHIVO.md": "sha256" },
  "spec_hashes":     [{ "sha256", "ref", "date", "phase" }],
  "approvers":       []
}
```

Estados válidos: `pending`, `in_progress`, `blocked`, `done`.

## 5. Garantías v2.2 a preservar (verificadas por la suite)

1. `--check` **fail-closed** sin `progress.json` (solo `--state-optional` lo relaja).
2. `--check` detecta desincronía `PROGRESS.md` ↔ `progress.json` (fingerprint).
3. `sealed_docs` + `--seal`: editar `INICIO_PROYECTO.md` / `SECURITY.md` /
   `TASK_TEMPLATE.md` sin re-sellar rompe el CI.
4. `spec_hashes`: `--approval` congela SHA-256 de `SPEC.md`; cambiarla sin nueva
   aprobación rompe el CI.
5. Evidencia cruda (bloque ``` o `Evidencia: <archivo>`) obligatoria en el checkpoint
   de toda fase F cerrada.
6. `TASK-Fx.md` obligatoria para cerrar una fase F.
7. No se cierra una fase con dependencias abiertas (Regla de Oro nº 4).
8. `APPROVAL-NNN` citada en una TASK debe existir en `DECISIONS.md` y estar completa
   (fecha, Acción, Aprobado por).
9. `--reopen` deja rastro auditable en `DECISIONS.md` y exige motivo.
10. Consolas Windows cp1252: sin `UnicodeEncodeError` en los scripts.

## 6. Layout de empaquetado (a cambiar en F1 — ADR-001)

```text
raíz del repo        → scripts fuente: bootstrap.py (505 líneas), task_generator.py (982)
fia_harness/
    cli.py           → solo `init` (157 líneas)
    data/scripts/    → copias de los scripts (duplicadas)
    data/templates/  → 11 plantillas
    data/rag/        → RAG_VECTOR_EXTENSION.md
tests/
    test_harness.py      → 672 líneas (suite principal)
    test_packaging.py    → guardas anti-drift scripts↔paquete + e2e de `init`
```

## 7. ADR-001 — Decisión de distribución (resumen)

El paquete `fia_harness` pasa a ser la **única fuente de verdad** en v3. Los scripts
de la raíz (del repo y de los proyectos) serán **fachadas finas generadas** que
importan el paquete instalado; los proyectos requerirán `pip install fia-harness`
(documentado como cambio de contrato major). Se eliminan `data/scripts/` y los tests
de sincronía. El bundle standalone generado (zipapp/inliner) queda diferido a v3.1+
solo si hay fricción real reportada. Justificación completa: `DECISIONS.md` (ADR-001).

## 8. Artefactos de referencia

- Suite: `tests/test_harness.py`, `tests/test_packaging.py`.
- Demo externo con trampa reproducible: repo `fia-harness-demo`
  (`PROGRESS.F2_tampered.md` → `--check` en rojo).
- Material de lanzamiento/KPIs para la puerta F8: carpeta `lanzamiento/` (fuera del repo).
- `dist/` contiene artefactos 2.0.0 (obsoletos, no se publican).

## 9. Checklist de salida de F0

- [x] Tag `v2.2.0` verificado y rama `v3.0-core` creada.
- [x] Suite completa ejecutada: 75/75 verde, tiempo registrado, log crudo archivado.
- [x] CLI pública inventariada.
- [x] Garantías a preservar listadas y referenciadas desde `SPEC.md`.
- [x] Dogfood activo: `SPEC.md`, `PROGRESS.md`, `DECISIONS.md`, `progress.json`,
      `TASK-F0.md` y job de CI `--check`.
- [x] Sin cambios de semántica del sistema (solo documentación y gobierno del repo).
