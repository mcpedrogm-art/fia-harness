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
    Detalle: `docs/V3_BASELINE.md`.
*   **ADR-002 (2026-09-15):** F3 State Engine con migración incremental: se conservan
    los campos de `harness-state/1` (`process_phases`, `execution_phases`,
    `checkpoints`, `sealed_docs`, `spec_hashes`, `approvers`) y se añaden
    `schema_version`, IDs estables, timestamps y fingerprints, con doble lectura y
    backup `.bak`. Alternativa rechazada por ahora: rediseño completo con arrays
    separados.
*   **ADR-003 (2026-09-15):** Benchmark oficial diferido a v3.1+; en F6/F7 se incluye
    un smoke de gobernanza (tampering / evidencia fabricada → FAIL) como test de
    regresión, no como benchmark.

## Reaperturas

## Aprobaciones
- **APPROVAL-001** · (2026-09-15) · Fase: M2 · Acción: Plan v3.0-core aprobado: SPEC.md congelado (fases F0-F8) · Aprobado por: Humano · Ref: sesion 2026-09-15 (usuario aprueba plan y ejecucion de F0)
