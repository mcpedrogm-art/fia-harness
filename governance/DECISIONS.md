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

## Reaperturas

## Aprobaciones
- **APPROVAL-001** · (2026-09-15) · Fase: M2 · Acción: Plan v3.0-core aprobado: SPEC.md congelado (fases F0-F8) · Aprobado por: Humano · Ref: sesion 2026-09-15 (usuario aprueba plan y ejecucion de F0)
- **APPROVAL-002** · (2026-09-15) · Fase: F3 · Acción: Autorización humana del plan v3.0-core (fases F0-F7) · Aprobado por: Humano · Ref: sesion 2026-09-15 (usuario autoriza cada fase)
