# PROGRESS.md — Hoja de Ruta e Historial de Fases (repo FIA Harness)

**Fase activa:** F4

## Fases del Proceso (Harness — dogfood del propio kit)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap del harness en el propio repo | SPEC.md, PROGRESS.md, DECISIONS.md y progress.json activos en la raíz | — | [x] Listo |
| M1 | Descubrimiento técnico: análisis de los planes D1/D2/D3 y decisiones de alcance | Decisiones de distribución, dogfood, F3 y benchmark registradas en DECISIONS.md | M0 | [x] Listo |
| M2 | Especificación v3.0-core aprobada por el humano | SPEC.md congelado con APPROVAL-001 | M1 | [x] Listo |
| M3 | Plan de fases de ejecución derivado de SPEC.md | Tabla F0–F7 en PROGRESS.md | M2 | [x] Listo |

## Fases de Ejecución del Proyecto (v3.0-core)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| F0 | Baseline v2.2 y dogfood del repo | docs/V3_BASELINE.md, suite 75/75 registrada, rama v3.0-core, CI con --check | — | [x] Listo |
| F1 | Extracción del Core + superficie `fia` | Módulos core/parser/generators, fachadas generadas, entry point `fia` | F0 | [x] Listo |
| F2 | Parser Engine con niveles de confianza | `extract_field(...) -> ExtractionResult`, config de sinónimos, corpus de PRDs, métrica % | F1 | [x] Listo |
| F3 | State Engine (migración incremental) | schema_version, IDs estables, timestamps, fingerprints, migración con backup | F2 | [x] Listo |
| F4 | Spike: mecanismo de captura de evidencia | docs/EVIDENCE_CAPTURE_DECISION.md + ejemplo end-to-end | F3 | [ ] Pendiente |
| F5 | Evidence Engine | Schema EV-NNN, `fia evidence`, cadena claim→command→execution→artifact→hash | F4 | [ ] Pendiente |
| F6 | Verification Engine | `fia verify` (STATE/DEPS/EVIDENCE/PROVENANCE/SEALS/SPEC) + smoke de tampering | F5 | [ ] Pendiente |
| F7 | CI / Merge Gate mínimo | harness.yml con `fia verify`, local vs CI confiable, demo en rojo/verde | F6 | [ ] Pendiente |

## Checkpoints de Contexto Recientes

- **M0 (Bootstrap dogfood):** Estructura de gobierno activa en el repo (SPEC.md, PROGRESS.md, DECISIONS.md, progress.json) creada en F0.
- **M1 (Descubrimiento):** Análisis comparativo D1/D2/D3 completado; ADR-001/002/003 registradas.
- **M2 (SPEC aprobado):** SPEC.md v3.0-core aprobado por el humano (APPROVAL-001).
- **M3 (Plan de fases):** Tabla F0–F7 definida y derivada de SPEC.md.
- **F0 (Baseline y dogfood):** Suite v2.2 en verde (75/75), baseline documentado y dogfood activo en el repo (SPEC.md, PROGRESS.md, DECISIONS.md, progress.json, TASK-F0.md, job de CI `--check`).
  Evidencia: docs/V3_BASELINE.md
  ```text
  python -m unittest discover tests -v   (Python 3.11.15, Windows)
  Ran 75 tests in 2.210s
  OK

  python task_generator.py --check
  ✅ Estado del harness válido: 4 fases de proceso, 8 de ejecución, 5 checkpoints, aprobaciones íntegras.
  ```
- **F1 (Core + CLI `fia`):** Núcleo extraído a `fia_harness/core|parser|generators` (17 módulos, ninguno >250 líneas), fachadas finas generadas (ADR-001, sin duplicación) y CLI `fia` con 8 subcomandos. Suite 75 → 144 tests, todos en verde; comportamiento equivalente a v2.2 (tests originales intactos).
  Evidencia: CHANGELOG_FIXES.md (v3.0.0a1) · docs/V3_BASELINE.md (referencia de equivalencia)
  ```text
  python -m unittest discover tests -v   (Python 3.11.15, Windows)
  Ran 144 tests in 2.127s
  OK

  python task_generator.py --check
  ✅ Estado del harness válido: 4 fases de proceso, 8 de ejecución, 6 checkpoints, aprobaciones íntegras.
  ```
- **F2 (Parser Engine con confianza):** `extract_field` con estrategias en cascada (heading exacto → parcial → densidad → ninguna), config versionada de sinónimos (añadir sinónimo no toca código), normalización de acentos/mayúsculas, confianza reflejada en CONTEXT.md y consola, corpus de 20 PRDs con test de regresión. Tests: 144 → 161.
  Evidencia: CHANGELOG_FIXES.md (v3.0.0a2) · tests/fixtures/prds/ · tests/test_prd_corpus.py
  ```text
  python -m unittest discover tests -v   (Python 3.11.15, Windows)
  Ran 161 tests in 2.482s
  OK

  Métrica del corpus (20 PRDs, 100 campos):
    resueltos (alta+media): 81/100 = 81.0%
    confianza alta:         70/100 = 70.0%

  python task_generator.py --check
  ✅ Estado del harness válido: 4 fases de proceso, 8 de ejecución, 7 checkpoints, aprobaciones íntegras.
  ```
- **F3 (State Engine incremental):** schema 3.0 con IDs estables (`CP-*`, `SNAP-*`), timestamps (`compiled_at`, `recorded_at`), huellas separadas (autoridad vs artefacto) y migración con doble lectura + backup. Extracciones por tamaño: `core/seals.py`, `parser/discovery.py`, `core/reports.py`. Hallazgo pre-v2.1 resuelto con ADR-004 (fail-closed + mensaje guiado de recuperación). Tests: 161 → 178.
  Evidencia: CHANGELOG_FIXES.md (v3.0.0a3) · tests/test_core_fingerprints.py · tests/test_core_state.py
  ```text
  python -m unittest discover tests -v   (Python 3.11.15, Windows)
  Ran 178 tests in 2.397s
  OK

  Migración dogfood del propio repo (harness-state/1 → 3.0):
    --check (legacy): ✅ válido con aviso "schema legado" (doble lectura)
    --sync:           ✅ migrado · backup progress.json.bak creado
    --stats:          Schema del estado: 3.0

  python task_generator.py --check
  ✅ Estado del harness válido: 4 fases de proceso, 8 de ejecución, 8 checkpoints, aprobaciones íntegras.
  ```
