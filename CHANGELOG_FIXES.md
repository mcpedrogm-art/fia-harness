# CHANGELOG_FIXES.md — Correcciones aplicadas al harness

Registro de qué se cambió, por qué, y cómo se verificó. Formato ADR-lite, coherente
con `DECISIONS.md` del propio sistema.

---

## v3.4.2 — `init` robusto ante carpetas no escribibles

1. **`fia init`** captura los `OSError` al preparar la carpeta destino y muestra un
   mensaje claro (ruta absoluta local, OneDrive, Carpetas controladas) en lugar de
   un traceback; devuelve exit code 1.
2. Los pasos finales muestran `cd <ruta absoluta>` (antes `cd .`).
3. Caso real reportado: en un equipo con `Documents` redirigido/protegido,
   `os.mkdir('src')` fallaba con `[WinError 2]` y el traceback no explicaba nada.
4. Tests: 282 → 284 (ruta inválida → error claro; `cd` absoluto).

---

## v3.4.1 — Corrección de documentación: numeración de reglas

1. **README EN/ES:** la nota de enforcement citaba la regla **nº16** (numeración del
   protocolo de 16 reglas) sin que existiera en el resumen de 8 del README. Se añade
   la regla **9 (recibo de fase)** y la nota pasa a "4, 5, 7, 8 y 9", precisando
   cómo se aplica cada una (la 5 como decisión humana registrada en riesgo, la 8 con
   gitleaks, la 9 con `fia verify --strict-receipts`).
2. **`INICIO_PROYECTO.md` (2 copias):** la nota afirmaba que la regla 8 (AEO) se
   verificaba mecánicamente y no es cierto. Ahora enumera las verificadas (4, 5, 7
   y 16), las reforzadas por gate (9 y 13) y las que aún no tienen gate mecánico
   (8 y 12, esta diferida a v3.5 por ADR-011).
3. Tests: 282 (sin cambios; corrección documental).

---

## v3.4.0 — UI/UX: cuatro direcciones divergentes y recetas de sección

1. **Cuatro direcciones divergentes (H3):** el prompt maestro entrega **4**
   direcciones con roles fijos (segura/control, composición opuesta,
   interacción/movimiento, arquetipo inesperado) en lugar de "tres direcciones"
   abstractas. Problema real observado en pruebas: la selección convergía en dos
   variantes cosméticas.
2. **Esquema de receta de sección (12 campos)** y **matriz de divergencia (6 ejes)**
   en `UI_UX_EXCLUSIVA.md` §8.1–8.2: cada dirección extrema en ≥3 ejes, ningún par
   coincidiendo en más de 2, y **autochequeo obligatorio antes de mostrarlas**.
   Nueva plantilla de proyecto `UI_RECIPES.md` (raíz + paquete + `fia init`/
   `bootstrap` + `NON_PRD_FILES`).
3. **Modo Lite:** dos direcciones divergentes (antes: una dirección y una
   alternativa).
4. **Biblioteca privada local** (`UI_LIBRARY.local.md`, gitignored): el kit público
   (MIT) solo lleva el esquema y el flujo, **nunca prompts ni assets de terceros**;
   los assets se autohospedan antes de publicar.
5. **Diferido a v3.5:** gate mecánico de UI (decisión humana registrada para fases
   de UI, mismo patrón que el gate de riesgo v3.1) — ADR-011.
6. Tests: 282 (anti-drift e `init` e2e incluyen la plantilla nueva). Prueba de flujo
   sobre brief neutro: 4 direcciones + matriz sin convergencia (pairwise ≤1).

---

## v3.3.1 — Hotfix de CI: historial completo para verificar recibos

1. **`fetch-depth: 0`** en el job de gobernanza del workflow generado
   (`generators/scaffold.py`) y del CI del propio repo
   (`.github/workflows/tests.yml`): el checkout por defecto de GitHub Actions es
   *shallow* (1 commit) y `fia receipt verify` necesita los commits históricos a
   los que están atados los recibos (`git show <commit>:<archivo>`). Detectado en
   la release v3.3.0: el job de gobernanza fallaba con
   `F9: no verificable en 3628c0b…`.
2. Demo (`fia-harness-demo`) actualizado con el mismo ajuste.
3. Tests: 282 (sin cambios; fix de configuración de CI).

---

## v3.3.0 — Recibo de fase y router de carril (regla nº16)

1. **Recibo de fase** (`core/receipts.py`, regla de oro nº16): manifiesto canónico
   JSON (`version`, `task_ref`, `mode`, commit, `dirty`, `files` con SHA-256 del
   contenido normalizado —BOM/CRLF—, `checks` y evidencia referenciada) y hash
   determinista (`generated_at`/`receipt_sha256` fuera del hash). `fia receipt
   create/verify`; `receipt_ref` compilado desde la línea `Recibo:` del checkpoint;
   `--check`/CI rechazan una fase F cerrada sin recibo. Verificación contra el commit
   (limpio) o contra el árbol (dirty); `fia verify --strict-receipts` exige recibos
   limpios en CI. Grandfathering: cierres anteriores al 2026-09-18 = legacy (ADR-009).
2. **Sección `RECEIPTS` en `fia verify`** y regla nº16 en `INICIO_PROYECTO.md`,
   `AGENTS.md` y `TASK_TEMPLATE.md` (las dos copias de plantillas sincronizadas).
3. **Router de carril** (`core/router.py`, ADR-010): `fia route "<descripción>"`
   propone Lite/Full con razones; señales de riesgo (`policy.RISK_KEYWORDS`) o
   ausencia de allowlist → Full (fail-closed). Sin estado ni presupuesto
   autodeclarado; `fia run --` y el resto de la CLI intactos.
4. **Hallazgos del dogfood**: `is_repo`/`changed_files` operan sobre la raíz del repo
   (estado en subcarpeta), re-emisión de recibos en fases `done` (evita el deadlock
   de reparación) y la gobernanza implícita no marca `dirty`.
5. Tests: 248 → 282. Docs: README EN/ES, `docs/RECEIPT_DESIGN.md`,
   `docs/PLAN_RECIBO_ROUTER.md`, `docs/RECEIPT_ROUTER.md` y roadmap actualizado.

---

## v3.2.0 — "Más difícil de engañar": scope post-hoc y evidencia reproducible

1. **Scope post-hoc** (`core/scope.py` + `adapters/git.py`): la TASK puede declarar
   su **alcance permitido** (sección con globs en `TASK_TEMPLATE.md`, v3.2). Mientras
   la fase está en curso, `fia verify` compara el diff (working tree, o
   `--scope-base origin/main` en CI) con ese alcance y **bloquea cambios fuera**.
   Sin alcance declarado el gate se omite (compatibilidad); los archivos de
   gobernanza de la fase están siempre permitidos. Requiere que el proyecto sea la
   raíz de un repo git.
2. **Evidencia reproducible (opt-in)** (`core/reproduce.py`):
   `fia verify --reproduce [EV-NNN]` re-ejecuta el comando del registro y compara
   **exit code + salida normalizada** (tiempos, timestamps y rutas se neutralizan)
   contra los artifacts originales. **Nunca por defecto** (efectos secundarios y
   flakiness) y con **allowlist explícita** del proyecto (`reproduce.json` →
   `allow_prefixes`); sin allowlist no se reproduce nada.
3. **Dos secciones nuevas en el reporte**: `SCOPE` y `REPRODUCTION` (esta última
   solo se evalúa con `--reproduce`; sin el flag se muestra como omitida).
4. **Plantilla TASK** con la sección `## Alcance permitido (scope)` (placeholder;
   vacía = gate omitido). Sincronizada con la copia del paquete (anti-drift).
5. Tests: 227 → 248. Docs: README EN/ES y `docs/ROADMAP_V3_1.md` actualizados.

---

## v3.1.0 — Gates de calidad: riesgo → decisión humana y avisos (Etapa 1)

1. **Gate de riesgo → decisión humana** (`core/quality.py`, fail-closed): una fase
   con señales de riesgo (auth, BBDD/migraciones/schema, secretos, pagos, PII,
   infra, servicios externos) no puede cerrarse sin una **decisión humana
   registrada** (`APPROVAL-NNN` citada en su TASK o checkpoint: aprobación o
   exención motivada). Es `heurística → recomendación → decisión`: no bloquea por la
   palabra clave, bloquea por la ausencia de decisión. En **Modo Lite**, una fase de
   riesgo exige **promoción a Modo Completo** — lo que `QUICKSTART_LITE.md` ya
   prometía, ahora mecánico.
2. **Sección `RISK` en `fia verify`** y gate equivalente en `--check` (misma fuente).
3. **Sección `QUALITY` (avisos, nunca bloquean)**: informe TASK incompleto
   (secciones 2/8/10/11/12 vacías) y fases pendientes con señales de riesgo.
   **Grandfathering**: cierres anteriores al 2026-09-16 = legacy (ADR-007).
4. **`detect_lite_mode` movido a `core/policy.py`** (señales y modo en un solo
   sitio; `generators.task` lo re-exporta, API intacta).
5. **ADR-006** (enforcement dentro del trust boundary Git+CI; se rechaza el mediador
   en runtime) y **ADR-007** (gates de calidad y grandfathering). Dogfood:
   `APPROVAL-002` (autorización humana de F0–F7) citada en `TASK-F3.md` por su
   señal de riesgo (migración/schema).
6. *Desviación documentada*: el aviso de completitud de SPEC se mueve a v3.2
   (necesita una lista de secciones configurable por tipo de proyecto).
7. Tests: 213 → 227.

---

## v3.0.2 — Posicionamiento honesto: freno de mano, no piloto automático (Etapa 0)

1. **Hero suavizado** (README EN/ES): de *"merge checks no agent can skip"* a
   *"merge checks the agent cannot silently skip — inside your Git + CI trust
   boundary"*. Precisión > marketing: el enforcement vive dentro del trust boundary
   de Git + CI, no es un sandbox.
2. **Claim explícito**: *"a local-first governance harness for AI-assisted software
   development"* / *"un protocolo de ingeniería para trabajar con agentes sin
   entregarles el control"* — con la frase que fija la frontera: **un freno de mano,
   no un piloto automático de calidad**.
3. **Tabla de frontera** en *Limitations* (EN/ES): qué garantiza FIA · qué NO
   garantiza · qué debe hacer el humano. Incluye la evidencia (integridad y
   procedencia sí; reproducción independiente, opt-in v3.2) y el sandbox (no).
4. **Demo con segunda trampa**: el README de `fia-harness-demo` añade el caso de
   **evidencia manipulada** (`echo ... >> evidence/EV-001.stderr.txt` →
   `PROVENANCE` FAIL con la razón exacta, salida real).
5. **Materiales de lanzamiento alineados** (Show HN, DevHunt, posts ES) con el
   mensaje honesto y las tres demostraciones: trampa → detección → por qué se bloqueó.
6. **Reorganización del repositorio** (incluida en esta release): las 11 plantillas
   + RAG a `templates/` (fuente de verdad; el test anti-drift las compara con el
   paquete) y la gobernanza dogfood a `governance/` (se opera con `-d governance`;
   el CI ejecuta `fia verify -d governance`). Eliminado `INSTRUCCIONES DE
   APLICACION.txt` (manual v2). Los proyectos de usuario no cambian.
7. Roadmap comprometido: `docs/ROADMAP_V3_1.md` (Etapa 0 → v3.0.2; Etapa 1 →
   v3.1.0; Etapa 2 → v3.2, solo con fricción real).

---

## v3.0.1 — Los artifacts de evidencia viajan como binarios (fix de portabilidad)

**Bug cazado por el propio CI (dogfood de F7):** git normalizaba los finales de
línea de `evidence/EV-*.stdout.txt`/`.stderr.txt` (CRLF→LF) al commitear, así que
en el checkout de Linux los hashes no coincidían y `fia verify` bloqueaba el merge
(`PROVENANCE FAIL — artifact no coincide con su hash`).

1. El almacén de evidencia crea `evidence/.gitattributes` con `* -text`: los
   artifacts son bytes exactos y su integridad ES el hash.
2. `.gitattributes` raíz con `* text=auto eol=lf` + `evidence/** -text`: protege
   además los sellos SHA-256 de los documentos normativos en clones Windows
   (`core.autocrlf=true`), que hasta ahora podían fallar por CRLF.
3. El mensaje de hash no coincidente ahora menciona la normalización por git.
4. Tests: 212 → 213.

---

## v3.0.0 — Núcleo verificable: estado 3.0, evidencia con procedencia y merge gate

Primera release estable de **v3.0-core** (fases F0–F7 del plan v3.0-core). Resumen:

- **Core extraído al paquete** (ADR-001): `task_generator.py`/`bootstrap.py` en los
  proyectos son fachadas finas; la CLI es `fia` (`init`, `sync`, `check`, `task`,
  `status`, `approve`, `seal`, `reopen`, `run`, `evidence`, `verify`).
- **Parser Engine con confianza** (F2): `extract_field` con niveles alta/media/ninguna,
  config versionada de sinónimos y corpus de regresión (81% de campos resueltos).
- **State Engine 3.0** (F3, ADR-002): IDs estables, timestamps, huellas de deriva e
  integridad, migración con backup y doble lectura `harness-state/1` ↔ 3.0.
- **Evidence Engine** (F5, ADR-005): registros `EV-NNN` con artifacts hasheados,
  `fia run` opcional en local y anclaje de digests de CI (`fia evidence --ingest`).
- **Verification Engine** (F6): `fia verify` (STATE/DEPENDENCIES/EVIDENCE/PROVENANCE/
  SEALS/SPEC SNAPSHOT), fail-closed, con distinción `trusted` vs `local`.
- **CI / Merge Gate** (F7): el workflow generado y el CI del propio repo ejecutan
  `fia verify`; el demo público queda migrado a v3.
- 212 tests, stdlib-only, sin cloud ni telemetría.

> **Cambio de contrato (major):** los scripts de la raíz requieren el paquete
> instalado (`pip install fia-harness`); ya no se copian scripts autocontenidos.
> Detalle por fase en las entradas v3.0.0a1–a6.

---

## v3.0.0a6 — CI / Merge Gate: `fia verify` como gate (F7 de v3.0-core)

1. **Workflow generado** (`bootstrap.py` → `.github/workflows/harness.yml`): el job
   de gobernanza instala `fia-harness` y ejecuta **`fia verify`** como merge gate
   (antes: `task_generator.py --check`). El patrón de procedencia `trusted`
   (ADR-005) queda documentado en el propio workflow: `fia run` + artifacts +
   `fia evidence --ingest` con el digest de la plataforma.
2. **CI del propio repo**: el job `estado-harness` ejecuta
   `python -m fia_harness.cli verify` (dogfood del gate v3).
3. **Demo migrado a v3** (`fia-harness-demo`, ADR-004): F0/F1 respaldadas por
   evidencia real re-ejecutada (`EV-001` greet, `EV-002` suite), estado 3.0 con
   backup, `fia verify` PASS (2 con procedencia, 0 solo existencia) y la trampa F2
   bloquea el merge (FAIL). Cambios pendientes de commit/push hasta la release.
4. **Hallazgo de recuperación (ADR-004)**: con varias fases consecutivas sin
   evidencia, `--reopen` no basta (la validación bloquea la primera reapertura):
   la vía práctica es añadir la evidencia real (como hizo el demo) o reabrir todas
   las afectadas a mano en PROGRESS.md y `--sync`. Candidato a mejorar en v3.1 si
   hay fricción reportada. *(ADR-004 se había perdido por una edición accidental en
   F4 y se restauró aquí, con la nota del hallazgo.)*
5. Tests: 212 (sin cambios); `fia verify` sobre el repo: PASS.

---

## v3.0.0a5 — Verification Engine: `fia verify` (F6 de v3.0-core)

1. **`fia verify`** (`core/verify.py`): reporte STATE / DEPENDENCIES / EVIDENCE /
   PROVENANCE / SEALS / SPEC SNAPSHOT. No confía en afirmaciones: inspecciona
   artefactos. Exit 0 (PASS — merge eligible) / 1 (FAIL — merge blocked) con la
   lista de razones.
2. **PROVENANCE (ADR-005)**: distingue `trusted` (registros EV con digests de CI
   verificados) de `local`, y cuenta la evidencia "solo existencia" (inline/archivo,
   compat v2.2). Un artifact manipulado o un digest de CI que no cuadra → FAIL.
3. **Secciones de estado**: `validate_state` se refactorizó en
   `validate_state_structure` (schema, fases, checkpoints, TASK-Fx) y
   `validate_dependencies` (Regla de Oro nº4/5), sin cambiar el comportamiento de
   `--check`; el reporte usa las secciones por separado.
4. **Smoke de gobernanza e2e**: copia sana → PASS; artifact de EV manipulado →
   PROVENANCE FAIL; documento sellado alterado → SEALS FAIL. `verify` también
   detecta deriva MD↔JSON, artefacto editado a mano (huella) y SPEC cambiada sin
   re-aprobación.
5. **Dogfood**: F6 se cierra citando EV-002 (la propia ejecución de `fia verify`
   registrada con `fia run`). Tests: 197 → 212.

---

## v3.0.0a4 — Evidence Engine: registros EV-NNN y cadena de procedencia (F5 de v3.0-core)

1. **Registros de evidencia `EV-NNN`** (`core/evidence.py`) con el schema decidido en
   F4: comando, cwd, exit code, timestamps UTC, duración, hashes de stdout/stderr,
   artifacts y entorno; `source: local-run | ci-artifact`. Almacén `evidence/`
   (`EV-NNN.json` + `EV-NNN.<stream>.txt`).
2. **Wrapper opcional `fia run -- <comando>`** (`core/runner.py`, ADR-005):
   transparente (propaga el exit code), captura SIEMPRE ambos streams (hallazgo del
   spike: `unittest` escribe en stderr) y registra la evidencia.
3. **`fia evidence`**: lista registros, muestra uno validando su cadena
   (campos → artifacts presentes → hashes → digest de CI si existe) y
   `fia evidence --ingest <manifiesto>` adjunta los digests publicados por la
   plataforma CI.
4. **Regla de cierre de fase ampliada**: `Evidencia: EV-NNN` valida procedencia e
   integridad (ya no solo existencia); el bloque ``` y `Evidencia: <archivo>` siguen
   funcionando. `fia status` muestra la evidencia registrada.
5. **Dogfood**: la suite del propio repo se registró como EV-001 con `fia run` y el
   `--check` del repo valida su cadena. Tests: 178 → 197.

---

## v3.0.0a3 — State Engine incremental: schema 3.0, huellas y migración (F3 de v3.0-core)

1. **Schema `3.0`** (`schema_version`) con migración incremental (ADR-002): se
   conservan los campos de `harness-state/1` y se añaden IDs estables
   (`CP-<fase>` en checkpoints, `SNAP-NNN` en snapshots de SPEC), timestamps
   (`compiled_at`, `recorded_at` por checkpoint) y huellas.
2. **Huellas separadas** (`core/fingerprints.py`): `state_fingerprint` cubre solo la
   autoridad (fases + contenido de checkpoints), por lo que es comparable entre
   schemas y robusta a `evidence=None` de estados antiguos; `state_sha256` cubre el
   artefacto completo y `--check` detecta ediciones manuales de progress.json.
3. **Doble lectura y backup** (ADR-002): `--check` acepta el schema legado con aviso
   y lo valida tal cual; `--sync` migra a 3.0 y guarda `progress.json.bak` antes de
   reescribir; `--stats` muestra el schema del estado.
4. **Extracción por tamaño**: `core/seals.py` (sellado de documentos normativos),
   `parser/discovery.py` (localización del PRD) y `core/reports.py` (`status`).
   Ningún módulo supera 250 líneas.
5. **Verificado**: el estado legacy del propio repo migró en verde (dogfood) con
   backup; tests 161 → 178. Nota (ADR-004): un proyecto anterior a v2.1 (demo, sin
   evidencia cruda en sus checkpoints) falla cerrado al migrar, como debe; el error
   explica la recuperación (`--reopen` en orden inverso + re-cierre con evidencia).
   La actualización del demo con evidencia real se hará en F7.

---

## v3.0.0a2 — Parser Engine con niveles de confianza (F2 de v3.0-core)

1. **`extract_field(content, field) -> ExtractionResult(value, confidence, method)`**
   (`fia_harness/parser/prd.py`): cada campo se resuelve con estrategias en cascada
   — encabezado exacto (`alta`) → encabezado parcial (`media`) → densidad de palabras
   clave (`media`) → sin resolver (`ninguna`). `extract_prd_metadata` mantiene su
   interfaz histórica y añade `confidence` por campo; `unresolved` pasa a ser
   exactamente la lista de campos con confianza `ninguna`.
2. **Config versionada** `fia_harness/data/parser/synonyms.json`: sinónimos por campo
   y palabras clave del fallback. Añadir un sinónimo no toca código (verificado por
   test con config inyectada).
3. **Normalización de encabezados**: sin marcado Markdown, minúsculas y sin acentos
   (`## INTRODUCCION` resuelve el sinónimo "Introducción").
4. **CONTEXT.md y bootstrap reflejan la confianza**: los campos `media` se anotan con
   su método (`heading_partial:…`, `density:N`) y se listan en consola; los `ninguna`
   conservan el aviso "Sin confirmar". Nunca se marca un campo como resuelto sin nivel.
5. **Corpus de regresión** `tests/fixtures/prds/` (20 PRDs: ES/EN, headings no
   estándar, sin headings, negritas, H3, mayúsculas, tablas, prosa) con test de tasa
   mínima. **Métrica medida: 81% de campos resueltos automáticamente (70% con
   confianza alta)** sobre 100 campos. Tests: 144 → 161.

---

## v3.0.0a1 — Núcleo extraído al paquete, CLI `fia` y fachadas (F1 de v3.0-core)

> **Cambio de contrato (major):** los scripts `bootstrap.py` y `task_generator.py` de
> los proyectos pasan a ser **fachadas finas** que importan el paquete instalado
> (`pip install fia-harness`). Decisión: ADR-001 en `DECISIONS.md`; baseline en
> `docs/V3_BASELINE.md`.

1. **Extracción del núcleo a módulos** (`fia_harness/core`, `parser`, `generators`):
   consola, reglas/heurísticas, estado, evidencia, aprobaciones, comandos, parser de
   Markdown y de PRD, generadores de tarea y de proyecto. Ningún módulo supera 250
   líneas; comportamiento equivalente a v2.2 (suite completa en verde).
2. **Fachadas de compatibilidad** (`fia_harness/facades.py`): `init` escribe scripts
   de ~20 líneas que re-exportan la API histórica; si falta el paquete, fallan con un
   mensaje accionable. Se elimina la duplicación `fia_harness/data/scripts/` y sus
   tests de sincronía; nuevo test anti-drift (fachadas del repo == plantilla del
   paquete).
3. **CLI unificada `fia`** (con `fia-harness` como alias): `init`, `sync`, `check`,
   `task`, `status`, `approve`, `seal`, `reopen`. La CLI legacy con flags se mantiene
   intacta vía `fia_harness/legacy.py`.
4. **CI:** el workflow generado instala `fia-harness` antes de `--check`; el job
   dogfood del repo usa `PYTHONPATH`; nuevo job `estado-harness` que valida el estado
   del propio repo. Tests: 75 → 144 (`python -m unittest discover tests -v`).

---

## v2.2.0 — Reapertura auditada y PRD de partida para la ruta de clonado

1. **`--reopen F<N> --reason`** (nuevo). Reabre una fase cerrada (`done` →
   `in_progress`) editando `PROGRESS.md`, registrando la reapertura en `DECISIONS.md`
   (sección `## Reaperturas`) y re-compilando `progress.json`. Fail-closed: exige
   motivo, la fase debe estar `done`, y se bloquea si una fase que depende de ella
   sigue cerrada. *Tests:* `ReopenTests`.

2. **`PRD_TEMPLATE.md`** (nuevo). Plantilla de PRD para la ruta de clonado del repo,
   con encabezados exactos que `extract_prd_metadata` reconoce (`## Problema`,
   `## Usuarios`, `## Funcionalidades`, `## Fuera de alcance`). Se empaqueta e `init`
   la copia a `docs/`; añadida a `NON_PRD_FILES` para no confundirla con un PRD.
   *Tests:* `PrdTemplateTests`.

3. **Fix del stub de `fia-harness init`.** El `PRD.md` generado usaba encabezados con
   sufijos (`Funcionalidades (Must Have)`, `Fuera de alcance (Out of Scope)`) que el
   regex de `extract_prd_metadata` no reconocía, dejando `features`/`out_of_scope`
   como "sin confirmar". Ahora usa los encabezados exactos y el test
   `test_stub_de_init_es_extraible` lo garantiza.

4. **Rediseño del README (EN/ES) + sección LIMITACIONES.** Portada con *hook*,
   modelo mental en 3 pasos, comparativa frente a prompts/SaaS y un bloque honesto
   de límites ("lo que el CI no puede garantizar"). Paridad H2 entre `README.md` y
   `README.es.md` verificada por `ReadmeParityTests`.

5. **Infraestructura de release y CI.** `.github/workflows/release.yml` publica en
   PyPI al etiquetar `v*` mediante Trusted Publishing (OIDC, sin secretos) tras
   correr la suite, y **crea el GitHub Release** con las notas extraídas de este
   changelog (evita que tag, PyPI y Release se desincronicen). `tests.yml` pasa a
   una **matriz multiplataforma** (ubuntu/windows/macos × Python 3.10/3.11/3.12)
   para detectar regresiones de codificación y rutas en cada SO.

6. **`--stats` y `MODELOS.md` (C4).** `task_generator.py --stats` resume el estado
   del proyecto (fases, checkpoints, aprobaciones, sellos, snapshots) desde
   `progress.json`; sin artefacto, lo calcula desde `PROGRESS.md` con aviso.
   `MODELOS.md` (nuevo template) documenta el routing de modelos por fase y el
   snapshot de coste/tokens en el checkpoint. *Tests:* `StatsTests`.

---

## v2.1.0 — Cierres de interlock (fail-closed, sellos, snapshot y evidencia)

Cuatro cierres para que el enforcement no dependa de la buena fe del agente, más
gobernanza nativa del agente (`AGENTS.md`) y paridad de README. Cada cierre va con
sus tests en `tests/test_harness.py`.

1. **`--check` fail-closed sin `progress.json`** (`cmd_check`). Antes, borrar el
   artefacto dejaba el CI verde (solo un aviso por stderr). Ahora falla con exit 1;
   validar solo el MD exige el flag explícito `--state-optional`.
   *Tests:* `MissingStateFileTests`.

2. **Sellado de documentos normativos** (`sealed_docs` + `--seal`). `bootstrap.py`
   sella `INICIO_PROYECTO.md`/`SECURITY.md`/`TASK_TEMPLATE.md` (SHA-256) en M0;
   `--check` detecta si se editaron o des-sellaron en silencio. `state_fingerprint`
   excluye `sealed_docs` y lo valida aparte. *Tests:* `SealDocsTests`.

3. **Snapshot criptográfico de `SPEC.md`** (`spec_hashes`). `--approval` congela el
   hash de `SPEC.md` al aprobar M2 o ampliar alcance; `--check` falla si la spec
   cambió sin nueva aprobación. Lista append-only `[{sha256, ref, date, phase}]`.
   *Tests:* `SpecSnapshotTests`. (La autoría git queda como opción futura.)

4. **Evidencia cruda en el checkpoint**. Una fase F no puede cerrarse con prosa
   sola: su checkpoint debe incluir un bloque de código con la salida de validación
   o `Evidencia: <archivo>`. El parser de checkpoints captura el bloque cercado.
   *Tests:* `EvidenceCheckpointTests`.

5. **`AGENTS.md`** (nuevo): gobernanza nativa del agente (arranque, entrevista 3×3,
   guardarraíl de aprobación, enmienda de PRD), con `INICIO_PROYECTO.md` como fuente
   de verdad. Se empaqueta e `init` lo copia a `docs/`.

6. **Paridad de README** (`ReadmeParityTests`): mismo número de secciones H2 en
   `README.md` y `README.es.md` (se añadieron las secciones que faltaban en ES).

---

## 1. `task_generator.py` no leía la tabla real de `PROGRESS.md`

**Síntoma:** `extract_phase_info()` comparaba `parts[0] == phase` (p. ej. `"F1"`),
pero `bootstrap.py` genera el código de fase en negrita (`**F1**`). La comparación
nunca era verdadera, así que título/objetivo/dependencias quedaban vacíos para
**toda fase**, siempre, en silencio.

**Fix:** `parse_progress_table()` ahora detecta las columnas por su cabecera
("Fase", "Estado", "Entregable/Objetivo", "Dependencias"...) y normaliza cada celda
quitando `**`/`` ` ``/`_` antes de comparar. Ya no importa el orden de columnas ni
si el código de fase está en negrita, cursiva o código.

## 2. Ninguna de las tres inyecciones de checklist ("si aplica") se disparaba

**Síntoma:** el script comparaba cadenas literales copiadas a mano de
`TASK_TEMPLATE.md` (p. ej. `"Aplica el checklist correspondiente de AEO_GEO_SEO.md"`),
pero el original real tiene comillas invertidas (`` `AEO_GEO_SEO.md` ``). La
comparación de texto exacto fallaba por ese único carácter, y lo mismo ocurría con
el bloque de seguridad (backticks) y el de UI/UX (backticks). Las tres ramas
"sí aplica" eran código muerto.

**Fix:** se sustituyó el matching literal por marcadores explícitos en
`TASK_TEMPLATE.md`:
```
<!-- INJECT:VISIBILITY_CHECKLIST -->  ... <!-- /INJECT -->
<!-- INJECT:SECURITY_CHECKLIST -->    ... <!-- /INJECT -->
<!-- INJECT:UIUX_CHECKLIST -->        ... <!-- /INJECT -->
```
Son comentarios HTML, invisibles al leer el `.md` renderizado. El script busca el
marcador, no la prosa; un cambio de redacción futuro en la plantilla ya no puede
romper la inyección en silencio. Si el marcador no aparece, el script **avisa por
stderr** en vez de dejar el placeholder sin tocar.

## 3. Las ramas "No aplica" (regex) tampoco se disparaban

**Síntoma:** el patrón `r"Aplica  \*\*solo si\*\*  esta tarea..."` tenía doble
espacio donde el original tiene uno solo. `re.sub` no encontraba nada.

**Fix:** ya no existen esos regex frágiles: al usar marcadores, la rama "No aplica"
simplemente sustituye el bloque completo por una frase fija
(`NOT_APPLICABLE_TEXT`), sin depender de reconocer la prosa circundante.

## 4. `extract_checklist()` no podía extraer tablas

**Síntoma:** el "Gate de entrada" de `UI_UX_EXCLUSIVA.md` es una tabla Markdown,
no una lista con `[ ]`/`-`/`*`. El filtro de línea la descartaba entera →
`TASK-Fx.md` recibía un bloque "Gate de Entrada UX" vacío, sin aviso.

**Fix:** `extract_section()` captura el contenido íntegro bajo un encabezado
(tablas, notas, listas) hasta el siguiente encabezado de **igual o mayor nivel**
(antes se cortaba en cualquier `#`, incluso un subtítulo dentro de la misma
sección). Verificado: la tabla de 10 filas del Gate de entrada ya sale completa.

## 5. Fallback peligroso: fase por defecto `"F0"` en silencio

**Síntoma:** si la detección de fase pendiente fallaba (como pasaba siempre, por
el bug #1), el script devolvía `"F0"` sin avisar — riesgo real de regenerar o
pisar la tarea de bootstrap ya cerrada.

**Fix:** si no hay ninguna fase pendiente, el script lo dice explícitamente y
termina con código 0 sin generar nada. Si se pide una fase que no existe en
`PROGRESS.md`, termina con código 1 y lista las fases disponibles.

## 6. Heurística de palabras clave con falsos positivos por subcadena

**Síntoma real detectado en pruebas:** la fase "Entrevista de Descubrimiento
Técnico" se marcaba con `UI/UX: SÍ` porque `"vista"` (palabra clave de UI) es
subcadena de `"entre_VISTA_"`. Del mismo modo, `AEO_GEO_SEO.md` como nombre de
archivo activaba `visibilidad` por contener las subcadenas "aeo"/"geo"/"seo".

**Fix:** las palabras clave ahora se buscan con límite de palabra (`\b...\b`), no
como subcadena. Verificado con la fase F1: security/visibility/ui_ux dan los tres
`NO` correctamente.

## 7. `bootstrap.py`: valores por defecto del PRD asignados en silencio

**Síntoma:** si el PRD del cliente no usaba exactamente los encabezados
`Problema`/`Usuarios`/`Features`/`Out of scope`, `CONTEXT.md` se rellenaba con
texto genérico ("No especificado...") sin que nadie se enterase — contradice la
propia Regla de Oro nº2 del sistema ("nunca asumir en silencio").

**Fix:** `extract_prd_metadata()` devuelve ahora la lista de campos no resueltos;
`bootstrap.py` los imprime explícitamente por consola **y** los marca inline en el
propio `CONTEXT.md` generado (`⚠️ Sin confirmar: ...`), para que el aviso no se
pierda si nadie lee la consola.

## 8. `bootstrap.py`: el título extraído del PRD nunca se usaba

**Síntoma:** `extract_prd_metadata()` calculaba `metadata["title"]` pero
`generate_context_file()` no lo insertaba en ningún sitio del `CONTEXT.md`
generado — se perdía.

**Fix:** ahora aparece como `**Proyecto:** <título>` en la cabecera de
`CONTEXT.md`. Si tampoco hay `# Título` en el PRD, se usa el nombre de archivo en
vez de "Nuevo Proyecto" a secas, y se marca como no resuelto.

## 9. Campo "Modo de trabajo" no existía en `CONTEXT.md`, pero sí se buscaba

**Síntoma:** la v1 de `task_generator.py` ya buscaba el texto "Modo de trabajo:
Lite" dentro de `CONTEXT.md` para decidir si generar `TASK-QUICK.md`, pero
`bootstrap.py` nunca creaba ese campo — la detección automática de Lite era
inalcanzable salvo con `--lite` explícito o `QUICK_CONTEXT.md` presente.

**Fix:** se añadió el campo `**Modo de trabajo:**` en la plantilla de
`CONTEXT.md` (sección 4, "Decisiones Confirmadas").

**Efecto colateral corregido en el mismo cambio:** al añadir la frase
`"Completo / Lite — ver QUICKSTART_LITE.md"` como ayuda para el humano, la propia
palabra "Lite" (mencionada como opción) generaba un falso positivo de detección.
Se corrigió exigiendo que "Lite" sea el **valor declarado** justo tras los dos
puntos, no una mención posterior en la misma línea.

## 10. Colisión de espacio de nombres entre fases de proceso y fases de ejecución

**Síntoma:** al unificar el formato de tabla, encontré algo más profundo que una
diferencia de columnas. `bootstrap.py` escribía en `PROGRESS.md` una tabla `F0`-`F8`
que mezclaba fases de *proceso* (`F0`=bootstrap del harness, `F1`=entrevista,
`F2`=SPEC.md, `F3`=plan de fases) con una **adivinanza** de fases de *construcción*
(`F4`=Modelo de Datos, `F5`=Backend+Auth, `F6`=Frontend, `F7`=Deploy, `F8`=QA) —
escrita antes de que `SPEC.md` existiera, es decir, antes de que nadie pudiera saber
si el proyecto real tendría ese plan. Mientras tanto, `INICIO_PROYECTO.md` (Fase 3)
instruye al agente a derivar de `SPEC.md` su **propia** tabla `F0`-`Fn`, cuyo `F0`
de ejemplo es "Bootstrap del repo, tooling..." — un `F0` con significado
completamente distinto al `F0` que ya existía en `PROGRESS.md`. Dos fases con el
mismo código y significados incompatibles, condenadas a convivir en el mismo
documento.

**Fix:** se separan los espacios de nombres:
- `M0`-`M3`: fases del *proceso* (lectura de PRD, entrevista, SPEC.md, plan de
  fases) — genéricas, iguales en todo proyecto, y por eso sí se pre-rellenan en
  `bootstrap.py`.
- `F0`-`Fn`: fases de *ejecución* del proyecto real, derivadas de `SPEC.md` en la
  Fase M3 — específicas de cada proyecto, y por eso `bootstrap.py` ya **no** las
  adivina: deja una tabla vacía con una nota explicando qué pegar ahí y cuándo.

Las dos tablas usan exactamente el mismo esquema de columnas
(`Fase | Objetivo | Entregable | Depende de | Estado`), así que la tabla que el
agente redacta en la Fase 3 de `INICIO_PROYECTO.md` se copia **literalmente**
dentro de `PROGRESS.md`, sin reformatear nada.

`task_generator.py` ahora:
- Parsea varias tablas independientes dentro del mismo `PROGRESS.md` (antes solo
  leía la primera tabla que encontraba en todo el documento).
- Solo autodetecta y genera `TASK-Fx.md` para códigos `F<N>` — las fases `M<N>`
  son pasos de descubrimiento, no tareas de código; pedir `--phase M1` explícitamente
  ahora falla con un mensaje claro en vez de intentar rellenar `TASK_TEMPLATE.md`
  con eso.
- Distingue "todavía no existe la tabla F" (avisa qué fases M faltan) de "ya no
  queda ninguna F pendiente" (proyecto de ejecución completo) — antes ambos casos
  daban el mismo mensaje genérico.
- Si la tabla no tiene columna de título separada (el esquema de la Fase 3 no la
  tiene), usa el objetivo truncado como título en vez de repetir el código de fase
  desnudo (`TASK-F0 — F0` → `TASK-F0 — BOOTSTRAP DEL REPO, TOOLING, LINTING...`).

**Verificación:** ejecutado el ciclo completo — bootstrap con solo `M0`-`M3` (sin
ninguna fila `F`), `task_generator.py` avisando correctamente que faltan fases de
proceso, simulación de `M0`-`M3` cerrados con una tabla `F0`-`F3` añadida a mano
(tal como haría el agente en la Fase M3), y generación correcta de `TASK-F0.md` y
`TASK-F1.md` con título e inyección de checklist de seguridad funcionando.

---

## Archivos afectados por el rediseño M/F (además de los ya listados arriba)

- **`INICIO_PROYECTO.md`** — tabla de ejemplo de la Fase 3 actualizada al esquema
  de 5 columnas con `Estado`, y nota explícita sobre el espacio de nombres `M`/`F`
  y cómo integrar la tabla en `PROGRESS.md`.


Se ejecutó el flujo completo sobre un proyecto de prueba ("Reservas Fácil"):
`bootstrap.py` → `CONTEXT.md`/`PROGRESS.md` generados → `task_generator.py` sobre
F1 (ninguno aplica, correcto), F4 (seguridad SÍ, checklist de `SECURITY.md`
completo e inyectado), F6 (visibilidad + UI/UX SÍ, incluida la tabla del Gate de
entrada, antes vacía). Casos límite probados: fase inexistente (falla con
mensaje claro), proyecto con todas las fases cerradas (termina limpio, sin
regenerar nada), Modo Lite forzado.

---

# Ronda de mejoras post-auditoría (2026-09-05)

## 11. Los TASK generados arrastraban la cabecera meta de la plantilla

**Síntoma:** todo `TASK-Fx.md`/`TASK-QUICK.md` generado empezaba con
`# TASK_TEMPLATE.md — Plantilla maestra` y su bloque "Cómo usar esta plantilla"
(rellenar `<placeholders>`, citar el stack...). Eso es documentación para quien
GENERA la tarea, no para el agente que la ejecuta: ruido de contexto en cada
fase, contradictorio con el principio de ahorro de contexto del propio sistema.

**Fix:** `strip_template_meta_header()` en `task_generator.py` recorta la
plantilla hasta el primer encabezado `# TASK-` (la cabecera meta usa
`TASK_..._TEMPLATE.md`, con guion bajo, así que nunca coincide). Si el marcador
no existiera, avisa por stderr y copia la plantilla íntegra — sin fallo
silencioso.

## 12. Referencia colgante a `SESSION.md`

**Síntoma:** `TASK_TEMPLATE.md` pedía leer "`PROGRESS.md` (y `SESSION.md` si el
proyecto lo usa)", pero `SESSION.md` no está definido en ningún documento del
sistema.

**Fix:** referencia eliminada; el requisito operativo queda en `PROGRESS.md` +
`SKILLS_MCP.md`, que sí existen.

## 13. Búsqueda difusa de PRD con falsos positivos

**Síntoma:** el fallback de `find_prd_file()` tomaba cualquier `.md` de la raíz
como PRD salvo 5 nombres. Un `CHANGELOG.md` o un `NOTES.md` suelto en la raíz de
un proyecto nuevo era tratado como documento de negocio.

**Fix:** constante `NON_PRD_FILES` con todos los archivos de control del harness
y exclusión adicional del prefijo `TASK-*`. Los nombres estándar
(`PRD.md`, `MVP.md`, `brief.md`, `requisitos.md`) siguen teniendo prioridad.

## 14. El módulo RAG estaba huérfano en el flujo

**Síntoma:** `PROYECTOS RAG Y VECTORIALES/RAG_VECTOR_EXTENSION.md` no lo
mencionaba ni `INICIO_PROYECTO.md`, ni `SKILLS_MCP.md`, ni `bootstrap.py`: un
proyecto RAG arrancaba sin activar nunca el módulo.

**Fix (tres piezas):**
- `INICIO_PROYECTO.md`: nuevo punto 12 en la Fase 2 (SPEC), nueva entrada en la
  sección 6 de archivos de control y nueva línea en el checklist de la sección 7.
- `SKILLS_MCP.md`: nueva fila en la matriz de recomendación MCP para
  búsqueda semántica / RAG / vectores.
- `bootstrap.py`: `maybe_activate_rag_module()` detecta keywords RAG en el PRD
  (embeddings, pgvector, búsqueda semántica, LlamaIndex...) y copia el módulo de
  `/docs` a la raíz; si el PRD lo pide pero falta en `/docs`, avisa
  explícitamente (Regla de Oro nº2) para copiarlo del kit maestro.

## 15. Documentación desalineada con el comportamiento real

- `INSTRUCCIONES DE APLICACION.txt`: prometía "resumir en menos de 15 líneas"
  (el script extrae las secciones tal cual, no resume), describía el
  `PROGRESS.md` antiguo (F0/F1) y solo decía `python3` (inexistente en Windows).
  Reescrita: extracción literal + avisos "Sin confirmar", fases M0-M3,
  `python` (Windows) / `python3` (Unix), detección de PRD, módulo RAG y
  referencia a `task_generator.py`.
- `PROTOCOLO DE GESTION Y VISIBILIDAD DE PROYECTOS.txt`: ahora declara en su
  cabecera que es una síntesis ejecutiva y que la fuente de verdad es
  `INICIO_PROYECTO.md` (mitiga el riesgo de divergencia entre los tres
  documentos de arranque; el PDF queda como snapshot estático).
- `guia-automatizacion-tareas.md`: `python` vs `python3` según SO, nuevo
  comportamiento de recorte de plantilla y referencia a los tests.
- `README.md` (nuevo): índice atractivo del sistema con diagramas, mapa de
  archivos, flujo completo y reglas.

## 16. Tests automatizados del kit (`tests/test_harness.py`)

Hasta ahora la única verificación era manual (secciones anteriores de este
changelog). Ahora hay 32 tests sin dependencias externas
(`python -m unittest discover tests -v`), siempre en carpetas temporales:

- Parser de `PROGRESS.md`: tablas múltiples, negritas, columnas combinadas,
  filas inválidas, detección de siguiente fase.
- `extract_section()` contra los documentos reales: la tabla del Gate de entrada
  sale completa; la sección 2.1 corta antes de 2.2.
- Inyectores por marcadores (presente/ausente).
- Heurística de keywords: caso "entre**vista**" (falso positivo clásico) y el
  comportamiento por exceso de "api" en fases frontend.
- Recorte de cabecera meta en ambas plantillas.
- Detección de Modo Lite (valor declarado vs mención, `QUICK_CONTEXT.md`, `--lite`).
- Extracción de metadatos del PRD (completo y sin encabezados).
- `find_prd_file()`: prioridad de nombres estándar, exclusión de archivos de control.
- E2E: `bootstrap.py` → aviso sin fases F → simulación M cerradas + tabla F →
  `TASK-F1.md` generado sin cabecera meta y con checklists inyectados →
  rechazo de fases M y fases inexistentes.

**Verificación de esta ronda:** `python -m unittest discover tests` → 32/32 OK.

---

# Ronda v2 — Enforcement: las reglas se vuelven mecánicas (2026-09-06)

Motivación: el kit obligaba por convención (documentos que dicen lo que no se
hace y agentes que prometen cumplirlo). Esta ronda convierte las Reglas de Oro
4, 5, 7 y 8 en comprobaciones que fallan mecánicamente, sin cambiar la filosofía
del kit (cero dependencias, Markdown como superficie de edición humana).

## 17. `bootstrap.py` emite CI, no solo documentos

**Antes:** el kit generaba documentos; nada verificaba nada a distancia.
**Ahora:** `generate_github_workflow()` emite `.github/workflows/harness.yml`
(nunca sobrescribe si existe) con tres jobs:
- `estado`: `python task_generator.py --check` — valida el estado del harness.
- `secretos`: gitleaks sobre todo el historial (`fetch-depth: 0`).
- `calidad`: tests + auditoría de dependencias condicionados al stack detectado
  (`package.json` → npm ci/test/audit; `requirements.txt`/`pyproject.toml` →
  pytest o unittest + pip-audit).

Además el propio kit obtiene `.github/workflows/tests.yml` (suite de unittest
en cada push/PR). Versión del kit declarada: `HARNESS_VERSION = "2.0.0"`.

## 18. Máquina de estado validada: `progress.json` detrás de `PROGRESS.md`

**Diseño:** `PROGRESS.md` sigue siendo la superficie de edición (humano/agente).
`task_generator.py --sync` lo compila al esquema `harness-state/1` y valida;
`--check` valida sin escribir (es lo que ejecuta el CI); el generador de tareas
auto-recompila si detecta edición manual (el CI, en cambio, es estricto: detecta
drift y falla hasta que alguien haga `--sync`). `--sync` es fail-closed: si el
estado es inválido, no escribe.

**Validaciones aplicadas (cada una es una Regla de Oro hecha mecánica):**
- Estados dentro del enum `pending/in_progress/blocked/done`; IDs únicos `M/F\d+`.
- Toda dependencia declarada existe; ninguna fase cerrada con dependencias
  abiertas (nº4).
- Toda fase cerrada tiene checkpoint de contexto en `PROGRESS.md` (nº5/DoD).
- Toda fase F cerrada tiene su `TASK-F<N>.md` en la raíz (nº7).
- `progress.json` y `PROGRESS.md` sin drift.

**Decisión de arquitectura:** `bootstrap.py` no duplica la lógica de compilación —
importa `task_generator` como módulo vecino y compila con la misma función, así
el JSON nace sincronizado por construcción. Si falta el script, avisa en vez de
inventarse el artefacto. El texto libre en "Depende de" ("SPEC aprobado") se
separa en `depends_on_notes` y no se valida como fase.

## 19. Aprobaciones humanas selladas (`APPROVAL-ID`)

**Antes:** la aprobación era una línea de prosa; el agente podía alegar una
aprobación inexistente y nada lo detectaba.
**Ahora:**
- Formato verificable en `DECISIONS.md > ## Aprobaciones`:
  `**APPROVAL-001** (fecha) · Fase: F2 · Acción: ... · Aprobado por: ... · Ref: ...`
- `task_generator.py --approval "acción" --phase F2 --ref "..."` registra la
  entrada con ID autoincremental y fecha del día.
- `--check` falla si una `TASK-*.md` cita un `APPROVAL-NNN` que no existe en
  `DECISIONS.md`, o si una entrada registrada está incompleta (sin fecha,
  `Acción:` o `Aprobado por:`).
- `TASK_TEMPLATE.md` (Fase L, punto 18) y `TASK_LITE_TEMPLATE.md` piden ahora
  citar el `APPROVAL-ID`; `SKILLS_MCP.md` documenta el formato (sección 5.1).

## 20. Suite ampliada y verificación de la ronda

De 32 a 49 tests: compilación del estado, checkpoint parser (formatos con y sin
negrita), validaciones de dependencias/enum/duplicados, drift y fail-closed,
registro de aprobaciones (autoincremento, formato, menciones sin ID ignoradas)
y e2e ampliado (`--check` en verde tras bootstrap, auto-sanado del generador,
bloqueo tras edición manual sin sync).

**Verificación e2e manual:** proyecto de prueba → `bootstrap.py` (genera
`progress.json` + CI) → `--check` verde → intento de trampa (marcar F0 y F1 como
cerradas sin TASK ni checkpoint): detectado primero por drift y, tras compilar,
`--sync` fail-closed listando las 7 violaciones y sin escribir el JSON → flujo
honesto (TASK + checkpoints) → `--sync` y `--check` en verde.

---

# Entregables de producto y marketing (2026-09-06)

## 21. Estudio de mercado ligero (`ESTUDIO_MERCADO.md`)

Barrido web con fuentes en vivo (septiembre 2026): GitHub Spec Kit, Amazon
Kiro, BMAD Method, Task Master y el estándar AGENTS.md; contexto del ciclo
vibe-coding → spec-driven development. Conclusión: la categoría existe y crece;
el hueco libre es "SDD + enforcement mecánico + gobernanza de capacidades +
español + cero dependencias, local". Posicionamiento recomendado y debilidades
honestas incluidas.

## 22. Web del producto (`web/`) aplicando `UI_UX_EXCLUSIVA.md`

- `web/DESIGN_DIRECTION.md`: Gate de entrada completo, tres direcciones Design
  DNA propuestas («ENCLAVAMIENTO», «ACTA NOTARIAL», «SALA DE CONTROL»), DNA
  elegido con ficha, sistema de movimiento con fallback y auditoría anti-clon.
  Dirección recomendada aplicada por encargo directo; las otras dos quedan
  documentadas para alternar.
- `web/index.html`: página única autocontenida en la dirección
  «ENCLAVAMIENTO» (metáfora del interlocking ferroviario: las reglas no son
  consejos, son checks de merge). Tokens del §9 de UI_UX, componente de señal
  de estado como único portador de estado, divisores de vía, banda "túnel" con
  la salida real del CI (demo del 2026-09-06), tablas de reglas y de paisaje
  competitivo, FAQ AEO con JSON-LD (`SoftwareApplication` + `FAQPage`),
  `prefers-reduced-motion` respetado, landmarks y foco visible.
- `web/llms.txt`: mapa del producto para agentes (GEO, según el formato del
  módulo RAG).

**Verificación:** renderizada en navegador a 1366 px y 390 px; dos defectos
detectados y corregidos (bloque de código sin `white-space: pre`; errata
"Otras/Otros toolkits"). Sin imágenes externas ni JS de terceros; fuentes con
fallback de sistema.

## 23. Retirada de la web del kit (2026-09-06)

Por decisión del responsable, la carpeta `web/` (landing del producto,
`DESIGN_DIRECTION.md` y `llms.txt`) sale del proyecto: no forma parte del
kit funcional. Las entradas 21-22 de este changelog se conservan como
registro histórico de lo que se construyó y cómo se verificó. Las
referencias a `web/` restantes en este archivo son solo históricas.

## 24. Retirada del estudio de mercado del kit (2026-09-06)

Por decisión del responsable, `ESTUDIO_MERCADO.md` (barrido de competidores
y posicionamiento) sale del repositorio: es material de negocio/web, no parte
del kit funcional. Se conserva la entrada 21 como registro histórico; la
investigación vive ahora fuera del repo (web y planificación).

## 25. Empaquetado PyPI: `fia-harness init` (2026-09-07)

- `pyproject.toml` (PEP 621/639): paquete `fia-harness`, stdlib-only,
  Python 3.8+, licencia MIT, sin dependencias.
- Paquete `fia_harness/` con CLI `fia-harness init`: monta un proyecto nuevo
  (plantillas en `/docs`, los dos scripts en la raíz y `PRD.md` de partida)
  sin clonar el kit. Idempotente: nunca sobrescribe lo que ya existe.
- Las copias internas del paquete (scripts y plantillas) están vigiladas por
  tests de sincronización: el CI rompe si divergen de la raíz del repo.
- Fix real de Windows: `bootstrap.py`, `task_generator.py` y el CLI reconfiguren
  stdout/stderr a UTF-8 en consolas `cp1252` (los emojis ✅/🚀/❌ reventaban con
  `UnicodeEncodeError` en Windows sin `PYTHONIOENCODING`). Cubierto con test.
- Suite: de 49 a 56 tests (sincronización del paquete + init e2e + consola cp1252).

**Verificación:** wheel construido e instalado en un venv limpio;
`fia-harness init` ejecutado sobre carpeta temporal; `bootstrap.py` +
`task_generator.py --check` en verde sobre el proyecto generado.

## 26. Dogfooding en CI y README bilingüe (2026-09-07)

- Nuevo job `dogfood` en `.github/workflows/tests.yml`: en cada push, el CI
  ejecuta `fia-harness init` sobre un proyecto temporal, lo arranca con
  `bootstrap.py` y valida su estado con `task_generator.py --check`. El kit se
  gobierna a sí mismo, mecánicamente, no de palabra.
- `README.md` pasa a **inglés** (principal, cara pública de PyPI y GitHub) con
  badges (CI, PyPI, Python, licencia), sección de demo y dogfooding; la versión
  española se conserva como `README.es.md` y enlaza de vuelta.
- `pyproject.toml` sigue apuntando a `README.md` como descripción de PyPI.
