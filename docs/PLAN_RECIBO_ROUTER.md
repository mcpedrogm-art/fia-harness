# Plan v3.3 — Receipt Engine reducido + `fia route`

> **Estado:** aprobado por el humano (2026-09-17). Pendiente de registrar como
> ADR + `APPROVAL-003` + enmienda de `SPEC.md` al arrancar la Fase R
> (AGENTS.md §4: toda ampliación de alcance se re-aprueba).
> **Base:** FIA Harness v3.2.0.
> **Origen:** recorte de los 3 planes de `NUEVA ADOPCION DE ROLES/`
> (`FIA_ODD_RDD_IMPLEMENTATION_PLAN.md`, `PLAN_INTEGRACION_ODD_RDD_v2.md`,
> `PLAN_MAESTRO_UNIFICADO_FIA_ODD_RDD_ROUTER.md`).
> **Versión objetivo:** v3.3.0.
> **Regla de oro del plan:** si algo no cierra un agujero real o no reduce
> fricción medida, no entra. Nada de producto nuevo.

---

## 0. Diagnóstico en una página

| Dimensión | Realidad |
|---|---|
| **Lo que hay** | v3.2.0: 212+ tests, cero dependencias, cross-platform, `fia verify` (9 secciones), evidencia `EV-NNN` con procedencia `local`/`trusted` (ADR-005), gate de riesgo → decisión humana (v3.1), scope post-hoc + reproducción opt-in (v3.2), dogfood y demo en PyPI. |
| **Hueco real (único)** | Nada ata el contenido de los archivos al cierre de una fase. `scope.py` solo mira la fase en curso; `sealed_docs` sella 3 plantillas; `spec_hashes` sella SPEC al aprobar. Editar un archivo tras cerrar su fase es indetectable hoy. |
| **Límite asumido** | La evidencia local es fabricable (ADR-005). El recibo no la convierte en verdad: es un ancla de auditoría y detección de manipulación, no un oráculo. |
| **Los 3 planes** | ~90% vocabulario y burocracia (Outcomes, Risks, trace, migración, 3 capas). ~10% valor: recibo + política de carril. Con errores factuales sobre el repo: "8 reglas de oro" (hay 15), `fia run --fast` colisiona con el wrapper de evidencia, YAML rompe stdlib-only, `timestamp` dentro del hash rompe el determinismo. |
| **Contexto** | F8 en pausa, cero usuarios externos. El principio del roadmap ("solo con fricción real") descalifica adoptar el plan completo. |
| **Veredicto** | Adoptar el recibo (reducido) + `fia route` fino + actualización de documentación/plantillas. Congelar el resto. |

---

## 1. Alcance aprobado

### Fase R — Receipt Engine reducido (aditivo; el único que cierra un agujero)

**Objetivo:** vincular el contenido final de los archivos tocados por una fase al
cierre de esa fase, de forma determinista y verificable en CI.

- [x] **R1 — Cerrar decisiones de diseño** (documento corto + ADR, sin código) · **completado 2026-09-18**:
  - Formato del manifiesto (JSON, stdlib): `{version, task_ref, mode, commit_or_tree_ref, dirty, files:[{path, content_sha256}], checks:{golden_rules, tests:{passed,total}, lint, scope}, evidence_refs:[EV-NNN]}`.
  - `receipt_sha256 = SHA256(json canónico)` con `sort_keys=True`, `separators=(",",":")`, UTF-8 sin BOM, contenido de archivos normalizado a LF, **`generated_at` y `receipt_sha256` fuera del hash** (metadata).
  - Ubicación: `evidence/receipts/receipt-<Fase>.json` (queda bajo `evidence/**`, ya permitido por `scope.py`).
  - El recibo **referencia** `EV-NNN` existentes; no duplica evidencia.
  - Grandfathering: fases con checkpoint anterior a la fecha de adopción = legacy (patrón ADR-004/007); constante `RECEIPT_GRANDFATHER_BEFORE = 2026-09-18`.
  - Numeración: regla de oro **#16** ("ninguna fase F se cierra sin su recibo verificable"). El router **no** añade regla: la #13 ya cubre Lite + riesgo.
  - Entregables: `docs/RECEIPT_DESIGN.md` · ADR-008/009/010 · APPROVAL-003 · SPEC §7 · fases F9–F11 en `governance/PROGRESS.md`.
- [x] **R2 — Generador** `fia_harness/core/receipts.py` (≤250 líneas): construye manifiesto y hash; sin dependencias.
  - *Hallazgo R1:* `adapters/git.is_repo` solo mira `project_dir/.git`; con el estado en subcarpeta (`-d governance`) hay que detectar el repo con `git rev-parse --show-toplevel` (subprocess en `project_dir`) en el módulo de recibos.
- [x] **R3 — Estado** `receipt_ref` en el checkpoint (compilado por `--sync` desde la línea `Recibo: ...` de `PROGRESS.md`); el hash vive dentro del recibo y se valida al verificar (no se duplica). Validación en `--check` (regla #16) y nueva sección `RECEIPTS` en `fia verify`.
- [x] **R4 — CLI** `fia receipt verify <Fase>`: recalcula desde el árbol/commit referenciado, compara, reporta archivo por archivo y el resultado de los checks.
- [x] **R5 — Compatibilidad**: grandfathering + doble lectura; proyectos v3.x siguen verificando sin cambios.
- [x] **R6 — Tests**: determinismo (mismo árbol → mismo hash), tampering (1 byte → FAIL), CRLF vs LF, cp1252/Linux, `EV` referenciada inexistente → FAIL, fase `done` sin recibo → FAIL, legacy intacto.

**Resultado R2–R6 (2026-09-18):** `fia_harness/core/receipts.py`, `fia receipt create/verify`,
`receipt_ref` compilado desde `Recibo:` en checkpoints, regla #16 en `--check`/`sync`,
sección `RECEIPTS` en `fia verify`, `is_repo`/`toplevel`/`show_file` en `adapters/git.py`.
Suite 248 → **266 tests en verde**; `--check` y `fia verify -d governance` verdes.

**DoD Fase R:** suite completa verde · `--check` y `fia verify -d governance` verdes en el dogfood · demo en verde · ningún flujo actual alterado · `CHANGELOG_FIXES.md` con la entrada.

### Fase X — `fia route` fino (UX de la política que ya existe)

**Objetivo:** que la elección Lite/Full deje de ser manual y silenciosa.

- [x] **X1 — Clasificador** `fia_harness/core/router.py` (≤250 líneas): orden determinista → red flags (`policy.RISK_KEYWORDS`, sin duplicar listas) fuerzan Full; allowlist cerrada (bugs acotados, refactor local, solo tests, lint/typos, docs) propone Lite **con razonamiento explícito**; ambiguo → Full (fail-closed). **Sin archivos de estado nuevos, sin presupuesto autodeclarado.**
- [x] **X2 — CLI** `fia route "<descripción>"` con salida razonada. `fia run --` y el resto de la CLI quedan intactos.
- [x] **X3 — Tests**: keyword camuflada (`jwt`, `password`) → Full; allowlist limpia → propone Lite; ambiguo → Full.

**Resultado X1–X3 (2026-09-18):** `fia_harness/core/router.py` + comando `fia route`;
14 tests nuevos (riesgo camuflado → Full, allowlist → Lite, ambiguo → Full).
Hallazgo de cierre: semántica local/estricta de recibos (`fia verify --strict-receipts`).
Suite 266 → **281 tests en verde**. La documentación de plantillas (`QUICKSTART_LITE.md`)
se hace en F11/D2 por la duplicación de plantillas (D2b).

**DoD Fase X:** comando documentado (CLI help + ADR-010) · tests verdes · `QUICKSTART_LITE.md` explica la ruta (→ F11/D2).

### Fase D — Cierre, documentación y material didáctico

> Obligatoria: sin esto el kit queda incoherente (features nuevas con docs viejas).

- [x] **D1 — README.md + README.es.md**: secciones de recibo y router; límites honestos ("ancla de auditoría, no verdad"; "recomendación, no autoridad"); actualizar lista de comandos y menciones de reglas verificadas en CI.
- [x] **D2 — Plantillas (las DOS copias: `templates/` y `fia_harness/data/templates/`)**:
  - `INICIO_PROYECTO.md` §8: regla #16 + nota de enforcement.
  - `QUICKSTART_LITE.md`: `fia route` y promoción.
  - `TASK_TEMPLATE.md` / `TASK_LITE_TEMPLATE.md`: línea `Recibo:` en el cierre.
  - `AGENTS.md`: cierre de fase con recibo.
- [x] **D2b — Resolver la duplicación de plantillas**: decidir fuente canónica y añadir test/CI de sincronía (o retirar la copia que no se use). Hoy son idénticas salvo `RAG_VECTOR_EXTENSION.md` (solo en raíz): divergirán en la primera edición.
- [x] **D3 — `docs/`**: nuevo `docs/RECEIPT_ROUTER.md` (concepto, límites, ejemplos reales) + actualizar `docs/ROADMAP_V3_1.md` con el estado v3.3.
- [x] **D4 — `CHANGELOG_FIXES.md`** + bump a `3.3.0` (`pyproject.toml`, `__init__.py`).
- [x] **D5 — Dogfood**: fases nuevas en `governance/PROGRESS.md` con `APPROVAL-003` + ADRs (`ADR-008` recorte, `ADR-009` diseño del recibo, `ADR-010` router) + recibo real de las propias fases R/X/D.
- [x] **D6 — Demo (`fia-harness-demo`)**: caso nuevo "editar archivo tras cierre → `fia receipt verify` FAIL" en README + workflow. *Repo externo: el push requiere autorización aparte.*
- [x] **D7 — `lanzamiento/*`**: revisar claims si mencionan el flujo de cierre (opcional, solo si queda desalineado).

**DoD Fase D:** paridad EN/ES · docs alineadas con la realidad · CI del kit y del demo verdes · evidencia citada en cada checkpoint.

**Resultado D1–D7 (2026-09-18):** README EN/ES (recibo, router, «What v3.3 adds», límites, 282 tests), plantillas sincronizadas con la regla nº16 (anti-drift en verde), CI estricto en el workflow generado y en el del repo, `docs/RECEIPT_ROUTER.md` + roadmap, CHANGELOG v3.3.0 y bump a `3.3.0`, demo commiteado (`4e4a8f5`). *Desviación:* `TASK_LITE_TEMPLATE.md` no se toca (las tareas Lite no tienen fase/recibo; el recibo llega con la promoción a Completo). *D7 revisado:* los posts de `lanzamiento/` son históricos de v3.0; sin cambios.

---

## 2. Guardarraíles (no negociables)

- Cero dependencias, stdlib-only, Python 3.8+, consolas Windows (cp1252).
- Sin YAML (JSON para máquina, Markdown para humanos), sin shell scripts.
- Ningún módulo nuevo >250 líneas (SPEC §3.5); dependencias unidireccionales.
- Backward compatible: `fia run --` intacto; grandfathering para proyectos y fases existentes.
- Un solo sistema de verdad: `progress.json` + `DECISIONS.md`; nada de estado paralelo.
- Sin LLM-juez, sin mediador en runtime, sin métricas de código como gates, sin telemetría.
- FIA no juzga calidad: presencia, completitud, integridad y decisión humana.

## 3. Congelado explícito (hasta que F8 produzca fricción real)

Outcomes `OUT-NNN` · Risks `RISK-NNN` · `fia outcome/risk` · `fia outcome verify` ·
`fia trace`/`REQ-XXX` · migración asistida · YAML · carpeta `.fia/` · renombrado
ODD/RDD · cobertura como gate · presupuesto anti-gaming autodeclarado.

## 4. Criterio de reapertura

Si 3–5 usuarios externos de F8 piden trazabilidad de negocio o registro formal de
riesgos, se retoma el Plan Maestro **con esa evidencia**, no antes.

## 5. Estimación y orden

| Fase | Esfuerzo | Riesgo |
|---|---|---|
| R — Recibo | ~1 semana seria | Bajo (aditivo) |
| X — Router | 1–2 días | Muy bajo |
| D — Cierre/docs | 2–3 días | Bajo |

Orden estricto: **R → X → D**. Cada fase termina con parada y autorización humana
antes de la siguiente.

## 6. Reanudación (si la sesión se corta)

1. Leer este documento; la primera casilla sin marcar indica dónde retomar.
2. Al arrancar la Fase R: registrar `ADR-008/009/010`, `APPROVAL-003`, enmendar
   `SPEC.md` y añadir las fases a `governance/PROGRESS.md`; `--sync`; CI verde.
3. Antes de cada fase: `fia verify -d governance` verde como punto de partida.

## 7. Estado de ejecución

- [x] Fase R · **R1** — diseño + registro (2026-09-18): `docs/RECEIPT_DESIGN.md`, ADR-008/009/010, APPROVAL-003, SPEC §7, F9–F11 en `governance/PROGRESS.md`; `--check`, suite (248/248) y `fia verify -d governance` en verde.
- [x] Fase R · **R2–R6** — implementación + tests (2026-09-18): recibo operativo (create/verify), regla #16, sección RECEIPTS; suite 266/266 verde.
- [x] Fase R · cierre dogfood de F9 (2026-09-18): `TASK-F9.md`, EV-007, `Recibo:` en checkpoint, fase done y reapertura auditada por dos hallazgos (re-emisión en `done` para evitar deadlock; `changed_files` en estado-subcarpeta). `fia verify -d governance` PASS · `receipt verify F9` PASS.
  - *Pendiente operativo:* los recibos de F9/F10 son `dirty` (locales). Tras el commit autorizado, re-emitirlos limpios (`fia receipt create F9 --base <ref>` / `F10`); el CI debe verlos `dirty: false` (`fia verify --strict-receipts`).
- [x] Fase X (X1–X3) — `fia route` operativo + `--strict-receipts`; suite 281/281 verde (2026-09-18).
- [x] Fase D (D1–D7) — cierre v3.3 completo (2026-09-18).
- [ ] Release v3.3.0 — **pendiente de decisión humana**: tag + publicación en PyPI + push (el push no está autorizado en esta sesión; los commits locales sí).
- [x] Dogfood final: 3 recibos limpios (F9, F10, F11) verificados con `fia verify -d governance --strict-receipts`.
