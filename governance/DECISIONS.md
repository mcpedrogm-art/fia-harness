# DECISIONS.md — Registro de Decisiones de Arquitectura (ADR)

## Registro

*   **ADR-000:** El desarrollo de v3.0-core se gobierna con el propio FIA Harness
    v2.2.0 (dogfood): PROGRESS.md + progress.json + `--check` en CI (F0).
*   **ADR-001 (2026-09-15):** Distribución del core — el paquete `fia_harness` es la
    única fuente de verdad; `task_generator.py`/`bootstrap.py` en proyectos pasan a
    ser fachadas finas generadas que requieren el paquete instalado
    (`pip install fia-harness`). Se elimina la duplicación `data/scripts/` y los tests
    de sincronía. Alternativa diferida a v3.1+: bundle standalone generado
    (zipapp/inliner), solo si hay fricción real reportada. Razón: instalación y
    desarrollo simples, sin romper local-first/stdlib-only/sin-telemetría.
    Detalle: `../docs/V3_BASELINE.md`.
*   **ADR-002 (2026-09-15):** F3 State Engine con migración incremental: se conservan
    los campos de `harness-state/1` (`process_phases`, `execution_phases`,
    `checkpoints`, `sealed_docs`, `spec_hashes`, `approvers`) y se añaden
    `schema_version`, IDs estables, timestamps y fingerprints, con doble lectura y
    backup `.bak`. Alternativa rechazada por ahora: rediseño completo con arrays
    separados.
*   **ADR-003 (2026-09-15):** Benchmark oficial diferido a v3.1+; en F6/F7 se incluye
    un smoke de gobernanza (tampering / evidencia fabricada → FAIL) como test de
    regresión, no como benchmark.
*   **ADR-004 (2026-09-15):** Política de migración para proyectos anteriores a v2.1
    (fases F cerradas sin evidencia cruda): **fail-closed**. La migración a 3.0 no
    acepta fases cerradas sin evidencia. Recuperación: (a) añadir la evidencia real
    que exista en el proyecto; (b) reabrir con `--reopen` (orden inverso de cierre si
    hay dependientes); (c) si hay varias fases consecutivas sin evidencia, `--reopen`
    no basta (la validación bloquea la primera reapertura): reabrir a mano todas las
    afectadas en PROGRESS.md y `--sync` (hallazgo de F7). No se introduce flag de
    escape en v3.0-core: debilitaría la garantía central del kit. La actualización del
    demo (`fia-harness-demo`, era v2.0) con evidencia real se hizo en F7 vía (a).
    *(Nota: este ADR se perdió por una edición accidental en F4 y se restauró en F7.)*
*   **ADR-005 (2026-09-15):** Captura de evidencia (F4): **híbrido** — `fia run --
    <cmd>` opcional en local (procedencia local) + artifacts de CI como fuente de
    verdad (`trusted`) validados contra el digest de la plataforma. `verify` (F6)
    distinguirá `local` de `trusted`; sin ancla de CI no hay PASS de procedencia.
    Detalle y evidencia del spike: `../docs/EVIDENCE_CAPTURE_DECISION.md`.

*   **ADR-006 (2026-09-15):** Alcance del enforcement y posicionamiento. FIA opera
    **dentro del trust boundary de Git + CI**: hace detectable y caro el estado
    deshonesto, pero no es un sandbox (el agente comparte filesystem y shell). Se
    **rechaza** evolucionar el core hacia un **mediador en runtime** (execution
    boundary que decide si una acción del agente está permitida): añade un proceso
    persistente, es bypassable igual y contradice el posicionamiento del proyecto.
    La vía es **verificación post-hoc** (scope enforcement: comparar el diff con el
    alcance declarado de la TASK) en v3.2, solo con fricción real. Claim público:
    *un freno de mano, no un piloto automático de calidad*.
*   **ADR-007 (2026-09-15):** Gates de calidad mecánicos (v3.1). Principio: FIA no
    juzga calidad; exige **presencia, completitud, integridad y decisión humana**.
    Secuencia: (1) gate de riesgo → decisión humana, fail-closed (una fase con
    señales de riesgo exige `APPROVAL-NNN` citada; en Modo Lite exige promoción);
    (2) sección `QUALITY` en `fia verify`, avisos que nunca bloquean (informe TASK
    incompleto, riesgo futuro); (3) v3.2: completitud de SPEC (configurable por tipo
    de proyecto), informe TASK bloqueante, ADR obligatorio, scope post-hoc,
    evidencia reproducible opt-in y MICRO acotado. **Grandfathering:** las fases
    cuyo checkpoint es anterior al 2026-09-16 son legacy (como ADR-004) y no generan
    avisos. Se rechaza el LLM-juez en el core (no determinista y gameable).
*   **ADR-008 (2026-09-18):** Recorte aprobado de los planes ODD/RDD (carpeta
    `NUEVA ADOPCION DE ROLES/`). Se adopta **solo** lo que cierra un hueco real:
    Receipt Engine reducido (F9) + `fia route` fino (F10) + actualización
    documental (F11). Se **congelan** Outcomes `OUT-NNN`, Risks `RISK-NNN`,
    `fia outcome/risk/verify`, `fia trace`/`REQ-XXX`, migración asistida, YAML,
    `.fia/`, renombrado ODD/RDD y cobertura como gate: los planes eran ~90%
    vocabulario sin enforcement nuevo y contradecían garantías vigentes
    (stdlib-only, `fia run --`, determinismo del hash) además del principio "solo
    con fricción real" (F8 sin usuarios todavía). Criterio de reapertura: 3–5
    usuarios externos piden trazabilidad de negocio o registro de riesgos.
    Ref: `docs/PLAN_RECIBO_ROUTER.md`, APPROVAL-003.
*   **ADR-009 (2026-09-18):** Diseño del recibo de fase (F9). Manifiesto canónico
    JSON (stdlib): `version, task_ref, mode, commit_or_tree_ref, dirty, files[],
    checks, evidence_refs`; hash SHA-256 sobre JSON canónico **sin `generated_at`
    ni `receipt_sha256`** (determinismo: mismo árbol + checks = mismo hash);
    contenido de archivos normalizado (BOM fuera, CRLF→LF); recibo en
    `evidence/receipts/receipt-<Fase>.json`; `receipt_ref` compilado desde la línea
    `Recibo:` del checkpoint (el hash no se duplica: vive en el recibo); regla de
    oro #16; grandfathering `recorded_at < 2026-09-18`; `fia receipt create/verify`;
    v1 requiere repo git. Límite asumido: no prueba verdad local (ADR-005 se
    mantiene); detecta manipulación post-cierre y da ancla de auditoría.
    Ref: `docs/RECEIPT_DESIGN.md`.
*   **ADR-010 (2026-09-18):** `fia route` fino (F10). Clasificador determinista
    fail-closed: reutiliza `policy.RISK_KEYWORDS` (sin duplicar listas), red flags
    o ambigüedad → carril Full; allowlist cerrada → propone Lite con razonamiento
    explícito. **Sin** archivos de estado nuevos ni presupuesto autodeclarado
    (gameable por el agente; si algún día se quiere, se calcula en CI desde el
    diff de git). No toca `fia run --` ni la CLI existente. No añade regla de oro:
    la #13 ya cubre Lite + riesgo y el gate v3.1 la hace mecánica.
*   **ADR-011 (2026-09-18):** UI/UX (v3.4): cuatro direcciones divergentes + recetas
    de sección. Problema real: en pruebas, la fase H3 convergía en dos variantes
    cosméticas. Decisión: **4 direcciones con roles fijos** (segura/control,
    composición opuesta, interacción/movimiento, arquetipo inesperado), **esquema
    de receta de 12 campos** (§8.1 de `UI_UX_EXCLUSIVA.md`) y **matriz de
    divergencia de 6 ejes** (§8.2: extremo en ≥3, ningún par coincidiendo en >2,
    autochequeo antes de mostrar). Plantilla de proyecto `UI_RECIPES.md`.
    **Biblioteca privada local** (`UI_LIBRARY.local.md`, gitignored) para material
    de referencia con licencia propia (Dínamo Sites): el kit público (MIT) solo
    lleva el esquema y el flujo, nunca los prompts/assets de terceros; los assets
    se autohospedan. **Diferido:** gate mecánico de UI (decisión humana registrada
    para fases de UI) → v3.6. Ref: SPEC §8, APPROVAL-004.
*   **ADR-012 (2026-09-18):** Pack de assets UI (v3.5, F13). El kit no empaqueta
    media de terceros (tamaño + licencia): publica el **mecanismo** y el contenido
    vive donde el mantenedor tenga derechos. Diseño: manifiesto `UI_ASSETS.json`
    (`version`, `assets[]` con `path`/`url`/`sha256`) + `fia assets fetch` (stdlib,
    `urllib`+`hashlib`, timeout, verificación SHA-256 fail-closed, idempotente,
    escritura atómica `.part` → `os.replace`, rutas relativas sin traversal),
    `fia assets manifest` para generar el manifiesto al publicar y `fia init
    --assets <url>` para "FIA completo" en un paso. Hosting previsto: Supabase
    self-hosted del mantenedor (bucket con lectura pública/URLs firmadas); el kit
    **nunca** descarga por defecto (opt-in). Sobre la licencia de los assets de
    Dínamo, el mantenedor confirma que son de descarga y uso libres (2026-09-18);
    si cambiara, el pack se retira sin tocar el kit. Ref: SPEC §9, APPROVAL-005.
*   **ADR-013 (2026-09-21):** Entorno UI/UX asistido (v3.6, F14). Decisión: el
    **protocolo pregunta** (Paso 0 en `UI_UX_EXCLUSIVA.md` §8, ítem H3, Lite y
    AGENTS) y la **máquina descarga** con `fia ui setup` (SHA-256, idempotente;
    `--recetas` para solo `library/UI_LIBRARY.md`; `fia ui status` sin red). **URL
    oficial por defecto** en `core/ui.py` con override `--url` > env
    `FIA_UI_PACK_URL` (funciona sin configurar y no ata: mover el pack es cambiar
    una constante). **Sin registro** de la decisión sí/no en `UI_RECIPES.md` (el
    humano lo descartó; la presencia de `media/`/`library/` es el estado). El
    manifiesto usado se guarda en el `UI_ASSETS.json` del proyecto para permitir
    `status` offline y re-descargas. Nada se descarga sin confirmación humana
    (opt-in estricto). Ref: SPEC §10, APPROVAL-006.

## Reaperturas

- **F9** (2026-09-18) · Reapertura · Razón: hallazgo del dogfood post-cierre: re-emision en done (evitar deadlock) y changed_files para estado en subcarpeta
- **F10** (2026-09-18) · Reapertura · Razón: hallazgo al verificar F10: semantica local/estricta de recibos (--strict-receipts) y prueba negativa de trabajo posterior
- **F11** (2026-09-18) · Reapertura · Razón: CI de release: checkout shallow rompe receipt verify (faltan commits historicos); requiere fetch-depth 0 en el workflow generado y en el del repo
- **F12** (2026-09-18) · Reapertura · Razón: release v3.4.0: reflejar el flujo de 4 direcciones como propiedad del harness (CHANGELOG, README EN/ES y bump) antes de publicar
- **F12** (2026-09-18) · Reapertura · Razón: v3.4.1: corregir numeracion de reglas en README EN/ES y nota de enforcement de INICIO_PROYECTO (referencia colgante a la 16 y regla 8 no verificada)
- **F12** (2026-09-18) · Reapertura · Razón: v3.4.2: init con mensaje claro ante OSError (cwd/ruta no escribible: OneDrive, Carpetas controladas) y cd absoluto en los pasos
- **F12** (2026-09-18) · Reapertura · Razón: v3.4.3: fixes del reporte externo (carry_over en receipt create, borrados en el manifiesto, shutil.which en fia run) + bateria de pruebas
- **F12** (2026-09-18) · Reapertura · Razón: v3.4.4: rutas git con -z/quotepath y --no-renames (nombres no-ASCII y renombrados quedaban mal en el manifiesto) + bateria adversaria
- **F13** (2026-09-21) · Reapertura · Razón: v3.5.1: recetas en el pack + URL oficial documentada (README EN/ES, docs/UI_ASSETS.md y plantilla UI/UX)
- **F14** (2026-09-21) · Reapertura · Razón: v3.6.1: fix de empaquetado (UI_ASSETS.json fuera del wheel por glob *.md) + guardarrailes (test package-data, job wheel en CI, humo en release) y mensaje de error afinado
## Aprobaciones
- **APPROVAL-001** · (2026-09-15) · Fase: M2 · Acción: Plan v3.0-core aprobado: SPEC.md congelado (fases F0-F8) · Aprobado por: Humano · Ref: sesion 2026-09-15 (usuario aprueba plan y ejecucion de F0)
- **APPROVAL-002** · (2026-09-15) · Fase: F3 · Acción: Autorización humana del plan v3.0-core (fases F0-F7) · Aprobado por: Humano · Ref: sesion 2026-09-15 (usuario autoriza cada fase)
- **APPROVAL-003** · (2026-09-18) · Fase: M2 · Acción: Recorte v3.3 aprobado: Recibo de fase + router fino (F9-F11); Outcomes/Risks congelados hasta friccion real de F8 · Aprobado por: Humano · Ref: sesion 2026-09-18 (usuario aprueba docs/PLAN_RECIBO_ROUTER.md)
- **APPROVAL-004** · (2026-09-18) · Fase: M2 · Acción: UI/UX v3.4: cuatro direcciones divergentes + esquema de recetas y plantilla UI_RECIPES.md · Aprobado por: Humano · Ref: sesion 2026-09-18 (usuario aprueba el flujo de 4 variantes y la integracion de recetas)
- **APPROVAL-005** · (2026-09-21) · Fase: M2 · Acción: Pack de assets UI v3.5: manifiesto UI_ASSETS.json + fia assets fetch/manifest + fia init --assets (el kit no empaqueta media de terceros) · Aprobado por: Humano · Ref: sesion 2026-09-18 (usuario aprueba el pack de assets y su hosting en Supabase self-hosted)
- **APPROVAL-006** · (2026-09-21) · Fase: M2 · Acción: Entorno UI/UX asistido v3.6: fia ui setup/status con confirmacion en el protocolo (Full y Lite), URL oficial por defecto y override · Aprobado por: Humano · Ref: sesion 2026-09-21 (usuario aprueba el flujo y el nombre fia ui setup)
