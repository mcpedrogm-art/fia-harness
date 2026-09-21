# PROGRESS.md — Hoja de Ruta e Historial de Fases (repo FIA Harness)

**Fase activa:** F14 (Entorno UI/UX asistido: `fia ui setup` + protocolo) — F8 en pausa

## Fases del Proceso (Harness — dogfood del propio kit)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap del harness en el propio repo | SPEC.md, PROGRESS.md, DECISIONS.md y progress.json activos en la raíz | — | [x] Listo |
| M1 | Descubrimiento técnico: análisis de los planes D1/D2/D3 y decisiones de alcance | Decisiones de distribución, dogfood, F3 y benchmark registradas en DECISIONS.md | M0 | [x] Listo |
| M2 | Especificación v3.0-core aprobada por el humano | SPEC.md congelado con APPROVAL-001 | M1 | [x] Listo |
| M3 | Plan de fases de ejecución derivado de SPEC.md | Tabla F0–F7 en PROGRESS.md | M2 | [x] Listo |

## Fases de Ejecución del Proyecto (v3.0-core → v3.3)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| F0 | Baseline v2.2 y dogfood del repo | docs/V3_BASELINE.md, suite 75/75 registrada, rama v3.0-core, CI con --check | — | [x] Listo |
| F1 | Extracción del Core + superficie `fia` | Módulos core/parser/generators, fachadas generadas, entry point `fia` | F0 | [x] Listo |
| F2 | Parser Engine con niveles de confianza | `extract_field(...) -> ExtractionResult`, config de sinónimos, corpus de PRDs, métrica % | F1 | [x] Listo |
| F3 | State Engine (migración incremental) | schema_version, IDs estables, timestamps, fingerprints, migración con backup | F2 | [x] Listo |
| F4 | Spike: mecanismo de captura de evidencia | docs/EVIDENCE_CAPTURE_DECISION.md + ejemplo end-to-end | F3 | [x] Listo |
| F5 | Evidence Engine | Schema EV-NNN, `fia evidence`, cadena claim→command→execution→artifact→hash | F4 | [x] Listo |
| F6 | Verification Engine | `fia verify` (STATE/DEPS/EVIDENCE/PROVENANCE/SEALS/SPEC) + smoke de tampering | F5 | [x] Listo |
| F7 | CI / Merge Gate mínimo | harness.yml con `fia verify`, local vs CI confiable, demo en rojo/verde | F6 | [x] Listo |
| F8 | Puerta de validación externa (3–5 usuarios) | 3–5 usuarios reales + fricción reportada + `fia verify` en un CI ajeno | F7 | [!] En pausa |
| F9 | Receipt Engine reducido: manifiesto canónico + `fia receipt create/verify` + regla de oro #16 | `core/receipts.py`, `receipt_ref` en checkpoints, sección RECEIPTS en `fia verify`, tests de determinismo y tampering | F7 | [x] Listo |
| F10 | Router fail-closed fino (`fia route`) | `core/router.py`, comando `fia route`, tests negativos (red flags → Full) | F9 | [x] Listo |
| F11 | Cierre v3.3: docs, plantillas, CHANGELOG, dogfood y demo | README EN/ES, plantillas (dos copias sincronizadas), `docs/RECEIPT_ROUTER.md`, CHANGELOG, demo con recibo manipulado | F10 | [x] Listo |
| F12 | UI/UX: cuatro direcciones divergentes + esquema de recetas + `UI_RECIPES.md` | `UI_UX_EXCLUSIVA.md` §8.1–8.2, H3 de `TASK_TEMPLATE.md`, `QUICKSTART_LITE.md`, plantilla `UI_RECIPES.md` (copias sincronizadas) y biblioteca privada local | F11 | [x] Listo |
| F13 | Pack de assets UI: manifiesto + descarga verificada (`fia assets fetch/manifest`, `fia init --assets`) | `core/assets.py` (stdlib, SHA-256, idempotente, fail-closed), plantilla `UI_ASSETS.json`, `docs/UI_ASSETS.md`, tests y E2E | F12 | [x] Listo |
| F14 | Entorno UI/UX asistido: `fia ui setup/status` + pregunta en el protocolo (Full y Lite) | `core/ui.py` (URL oficial por defecto, `--recetas`, override `--url`/env), `ui setup/status` en CLI, Paso 0 en `UI_UX_EXCLUSIVA.md`, H3, `QUICKSTART_LITE.md`, `AGENTS.md`, README EN/ES | F13 | [~] En curso |

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
- **F4 (Spike captura de evidencia):** prototipadas las dos opciones (wrapper y artifacts) sobre un fixture mínimo; decisión híbrida (ADR-005) documentada en `docs/EVIDENCE_CAPTURE_DECISION.md`. Hallazgos clave: los runners escriben en streams distintos (unittest → stderr); sin ancla de CI la fabricación local no es detectable; la distinción local/trusted es la frontera de la garantía. Sin cambios de producto (spike).
  Evidencia: docs/EVIDENCE_CAPTURE_DECISION.md · DECISIONS.md (ADR-005)
  ```text
  Spike F4 (fixture mínimo, Python 3.11.15, stdlib-only):
    (a) wrapper verde:  exit_code=0 · stdout_sha256=e3b0c442… (vacío) · stderr_sha256=a4ca7fdb…
        hallazgo: unittest escribe el informe en stderr → capturar ambos streams
    (a) wrapper rojo:   exit_code=1 · FAILED (failures=1)
    (b) verificación verde: PASS (10/10 checks) — artifact↔manifest, claim↔artifact, resultado↔exit
    (b) verificación roja:  PASS (FAILED es coherente con exit 1)
    (b) tras manipular el artifact (FAILED→OK): FAIL (3 detecciones: hash, binding, coherencia)

  python task_generator.py --check
  ✅ Estado del harness válido: 4 fases de proceso, 8 de ejecución, 9 checkpoints, aprobaciones íntegras.
  ```
- **F5 (Evidence Engine):** registros `EV-NNN` con schema del contrato F4 (comando, exit code, timestamps, hashes de stdout/stderr, artifacts, entorno, `source`), almacén `evidence/`, wrapper opcional `fia run -- <cmd>` (transparente: propaga el exit code) y comandos `fia evidence` (lista/muestra/valida) y `fia evidence --ingest` (digests de CI). La regla de cierre de fase acepta `Evidencia: EV-NNN` y valida procedencia + integridad (hash de cada artifact y digest de CI si existe). Tests: 178 → 197.
  Evidencia: EV-001
  La cadena del registro EV-001 (suite completa ejecutada con `fia run`) se valida en este mismo `--check`: campos, artifacts presentes y hashes coincidentes.
- **F6 (Verification Engine):** `fia verify` compone el reporte STATE / DEPENDENCIES / EVIDENCE / PROVENANCE / SEALS / SPEC SNAPSHOT, no confía en afirmaciones (inspecciona artefactos) y es fail-closed (exit 1 con razones). PROVENANCE distingue `trusted` (digests de CI, ADR-005) de `local` y cuenta la evidencia "solo existencia" (compat v2.2). `validate_state` se refactorizó en secciones (estructura/dependencias) sin cambiar comportamiento. Tests: 197 → 212.
  Evidencia: EV-002
  EV-002 es la ejecución real de `fia verify` sobre este repo (registrada con `fia run`); su cadena se valida en el `--check` de este cierre. Smoke de tampering: copia sana → PASS; artifact manipulado → PROVENANCE FAIL; documento sellado alterado → SEALS FAIL.
- **F7 (CI / Merge Gate):** el workflow generado pasa a ser `fia verify` (instala el paquete; patrón `trusted` documentado con artifacts + digest, ADR-005) y el job `estado-harness` del propio repo también. Demo `fia-harness-demo` migrado a v3 en local: F0/F1 con evidencia real re-ejecutada (EV-001 greet, EV-002 suite), estado 3.0 con backup, `fia verify` PASS (2 con procedencia, 0 solo existencia) y la trampa F2 bloquea el merge (FAIL por deriva; `sync` fail-closed con los errores de checkpoint/TASK). Cambios del demo sin commitear (pendientes de la release v3.0.0 y de autorización de push).
  Evidencia: EV-003
  EV-003 es la ejecución real de `fia verify` sobre este repo (registrada con `fia run`); su cadena se valida en el `--check` de este cierre.
- **F8 (puerta externa):** EN CURSO (2026-09-15). v3.0.0 publicada en PyPI; demo migrado y empujado con CI v3 en verde; materiales de lanzamiento actualizados a v3 (`lanzamiento/1_SHOW_HN.md`, `2_DEVHUNT.md`, `3_POSTS_ES.md`) y puerta de seguimiento en `lanzamiento/6_PUERTA_F8_VALIDACION_EXTERNA.md`. Criterios: 3–5 usuarios externos reales, fricción reportada y `fia verify` estable en un CI ajeno. Time-box: 4–6 semanas.
- **F9 (Recibo de fase):** recibo canónico operativo (`fia receipt create/verify`): manifiesto JSON con hash determinista (metadata fuera del hash), normalización BOM/CRLF, gobernanza implícita excluida del manifiesto y verificación contra commit o árbol (dirty). `receipt_ref` compilado desde la línea `Recibo:` del checkpoint; regla de oro #16 en `--check`/`sync`; sección `RECEIPTS` en `fia verify`. 14 archivos vinculados al commit `d066e5d` (recibo local dirty). Hallazgos del dogfood corregidos: `is_repo`/`changed_files` para estado en subcarpeta y re-emisión en fase `done` (evita el deadlock de reparación). Tests: 248 → 266.
  Evidencia: EV-007
  Recibo: evidence/receipts/receipt-F9.json
- **F10 (Router de carril):** `fia route` determinista y fail-closed: señales de riesgo (`policy.RISK_KEYWORDS`, sin duplicar listas) → Full; allowlist cerrada de 5 categorías (bug acotado, refactor local, solo tests, lint/typos, docs) → propone Lite con razones; sin coincidencia → Full. Sin estado nuevo ni presupuesto autodeclarado (ADR-010); `fia run --` y el resto de la CLI intactos. 14 tests nuevos. Hallazgo de cierre: semántica local/estricta de recibos (`--strict-receipts`; el trabajo posterior no bloquea el verify local pero sí el CI). Tests: 266 → 281.
  Evidencia: EV-009
  Recibo: evidence/receipts/receipt-F10.json
- **F11 (Cierre v3.3):** regla nº16 documentada en `INICIO_PROYECTO.md`, `AGENTS.md` y `TASK_TEMPLATE.md` (plantillas raíz y paquete sincronizadas; anti-drift en verde), `QUICKSTART_LITE.md` con `fia route`; README EN/ES con recibo/router, sección «What v3.3 adds» y límites honestos; CI estricto (`fia verify --strict-receipts`) en el workflow generado y en el job de gobernanza; `docs/RECEIPT_ROUTER.md`; CHANGELOG y bump de versión; demo con CI estricto y nota de recibos (commit `4e4a8f5`). **Hotfix v3.3.1:** el job de gobernanza requiere `fetch-depth: 0` (el checkout shallow no tiene los commits históricos a los que atan los recibos); corregido en el workflow generado y en el del repo. Tests: 282.
  Evidencia: EV-011
  Recibo: evidence/receipts/receipt-F11.json
- **F12 (UI/UX v3.4):** cuatro direcciones divergentes con roles fijos (segura, composición opuesta, interacción/movimiento, arquetipo inesperado) + **esquema de receta de 12 campos** (§8.1) + **matriz de divergencia de 6 ejes** (§8.2: extremo en ≥3, ningún par >2, autochequeo antes de mostrar) para corregir la convergencia observada en pruebas; plantilla `UI_RECIPES.md` (raíz + paquete + `fia init`/`bootstrap` + `NON_PRD_FILES`); H3 y Lite actualizados; README EN/ES; **biblioteca privada local** `UI_LIBRARY.local.md` (gitignored, 12 recetas aportadas por el humano; el kit MIT solo lleva esquema y flujo, nunca prompts/assets de terceros). Release **v3.4.0** reflejada como propiedad del harness. **v3.4.1:** corrección de la numeración de reglas (README EN/ES y nota de enforcement). **v3.4.2:** `init` robusto (mensaje claro ante carpetas no escribibles + `cd` absoluto). **v3.4.3 (reporte externo, verificado y reproducido):** `receipt create` hacía `carry_over_aux_fields` con el estado guardado (fallaba siempre con documentos sellados); los **borrados** se representan en el manifiesto (`deleted: true`) y se verifican por ausencia; `fia run` resuelve el ejecutable con `shutil.which` (PATHEXT: `npm` → `npm.cmd` en Windows) y da error claro si no existe. Batería E2E reproducible (`tests/e2e_manual.py`, EV-019): init/bootstrap/sellos/borrado/tampering/recibo limpio/CI estricto/demo legacy. **v3.4.4 (pruebas adversarias):** rutas git con `-z` (sin comillas: nombres con `ñ`/acentos/espacios ya no se registran como borrados) y `--no-renames` (un renombrado se ancla como baja + alta). Tests: 291. Diferido a v3.5: gate mecánico de UI (ADR-011).
  Evidencia: EV-018
  Recibo: evidence/receipts/receipt-F12.json
- **F13 (Pack de assets UI, v3.5.0 → v3.5.1):** `core/assets.py` (stdlib): manifiesto `UI_ASSETS.json` (`version`, `assets[]` con `path`/`url`/`sha256`), `fia assets fetch [URL|ruta]` (verificación SHA-256 fail-closed, idempotente, escritura atómica `.part`→replace, rutas relativas sin traversal, opt-in), `fia assets manifest --dir-source --base-url` y `fia init --assets <url>`. Plantilla `UI_ASSETS.json` (raíz + paquete + `bootstrap`), `docs/UI_ASSETS.md`, nota en `UI_UX_EXCLUSIVA.md` §8.1 y README EN/ES. El kit no empaqueta media de terceros (mecanismo MIT; contenido en la infraestructura del mantenedor: Supabase self-hosted). Tests: 291 → 299; E2E con manifiesto, fetch y hash incorrecto bloqueando. **v3.5.1:** pack oficial publicado en el Supabase self-hosted (bucket `fia-assets`, 16 objetos: 15 media + `library/UI_LIBRARY.md` con las 12 recetas) y URL documentada en README EN/ES, `docs/UI_ASSETS.md` y la plantilla; verificado end-to-end (`fia init --assets <URL>` → 51.35 MB + recetas; descarga incremental e idempotente).
  Evidencia: EV-022
  Recibo: evidence/receipts/receipt-F13.json
