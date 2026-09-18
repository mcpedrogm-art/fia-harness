# SPEC.md — FIA Harness v3.0-core

**Estado:** Aprobado (APPROVAL-001, fase M2)
**Base:** FIA Harness v2.2.0 (tag `v2.2.0`, commit `c6ea8a2`)
**Plan fuente:** `FIA_Harness_v3_Plan_Maestro_Refaseadogpt.md` (D3) + enmiendas registradas en este repo.

---

## 1. Objetivo

Convertir FIA en un **núcleo verificable**: que el estado del proyecto, la evidencia
de ejecución y su procedencia sean verificables por CI, sin ampliar la superficie de
producto hasta validar el núcleo con usuarios externos reales.

## 2. Alcance de v3.0-core

| Fase | Entrega |
| --- | --- |
| F0 | Baseline v2.2 y dogfood del propio repo |
| F1 | Extracción del Core + superficie `fia` |
| F2 | Parser Engine con niveles de confianza |
| F3 | State Engine (migración incremental) |
| F4 | Spike: mecanismo de captura de evidencia |
| F5 | Evidence Engine |
| F6 | Verification Engine |
| F7 | CI / Merge Gate mínimo |
| F8 | Puerta de validación externa (3–5 usuarios; proceso, no código) |

## 3. Decisiones de diseño

1. **ADR-001 — Distribución:** el paquete `fia_harness` es la única fuente de verdad;
   `task_generator.py`/`bootstrap.py` en proyectos pasan a ser fachadas finas generadas
   que requieren el paquete instalado (`pip install fia-harness`). Se elimina la
   duplicación `fia_harness/data/scripts/` y los tests de sincronía. Alternativa
   diferida a v3.1+: bundle standalone generado (zipapp/inliner), solo con fricción
   real reportada. Detalle en `docs/V3_BASELINE.md`.
2. **ADR-002 — Dogfood:** el propio repo se autogobierna con `PROGRESS.md`,
   `progress.json` y un job de CI que ejecuta `--check` como gate de cada fase.
3. **ADR-003 — F3 incremental:** se conservan `process_phases`, `execution_phases`,
   `checkpoints`, `sealed_docs`, `spec_hashes`, `approvers`; se añaden
   `schema_version`, IDs estables, timestamps y fingerprints. Doble lectura
   `harness-state/1` ↔ 3.0 con migración y backup `.bak`.
4. **Benchmark diferido a v3.1+** (`FIA_Harness_Benchmark_Framework_v1.md` como
   insumo). En F6/F7 se añade un smoke de gobernanza: tampering y evidencia
   fabricada deben producir FAIL.
5. **Criterio de tamaño F1:** ningún módulo nuevo supera 250 líneas salvo excepción
   justificada por escrito en `DECISIONS.md` (el "≤150 líneas + 4-5 módulos" era
   aritméticamente imposible).

## 4. Garantías v2.2 que v3.0-core DEBE preservar

- `--check` fail-closed sin `progress.json` (escape explícito `--state-optional`).
- `sealed_docs`: SHA-256 de `INICIO_PROYECTO.md`, `SECURITY.md` y `TASK_TEMPLATE.md`
  (comando `--seal`).
- `spec_hashes`: snapshot SHA-256 de `SPEC.md` en cada `--approval`.
- Evidencia cruda obligatoria en el checkpoint de toda fase F cerrada.
- `TASK-Fx.md` obligatoria para cerrar una fase F.
- No se cierra una fase con dependencias abiertas.
- Las aprobaciones `APPROVAL-NNN` citadas en TASKs deben existir y estar completas.
- Reapertura auditada (`--reopen` + registro en `DECISIONS.md`).
- `--stats`, `--reopen`, `--seal`, `--approval` siguen existiendo (flags y/o
  subcomandos `fia`).
- stdlib-only, sin cloud, sin telemetría; consolas Windows (cp1252) soportadas.

## 5. No-alcance (diferido a v3.1+)

Policy Engine formal · Human Approval con hash/firma (se conserva lo existente, no se
amplía) · CLI como producto pulido · Lite/Full formalizado por riesgo · Agent Protocol
(revisar con escepticismo) · Modules (`fia-security`, `fia-mcp`, `fia-rag`, `fia-ui`,
`fia-seo`, `fia-privacy`) · Benchmark oficial completo · bundle standalone.

## 6. Criterio de éxito de v3.0-core

Un tercero puede instalar el kit, crear un proyecto, ejecutar una tarea, producir
evidencia con procedencia, intentar saltarse una regla, recibir un fallo determinista,
corregirlo y demostrar un `PASS` en CI. Además: 3–5 usuarios externos reales completan
el flujo sin supervisión del creador (F8).

---

## 7. Enmienda v3.3 — Recibo de fase + Router (APPROVAL-003, 2026-09-18)

**Objetivo:** cerrar el único hueco de enforcement real (nada ata el contenido de los
archivos al cierre de una fase) y hacer explícita la elección de carril Lite/Full.
Sin producto nuevo. Recorte aprobado de los planes ODD/RDD (ADR-008).

| Fase | Entrega |
| --- | --- |
| F9 | Receipt Engine reducido: manifiesto canónico, `fia receipt create/verify`, `receipt_ref` en checkpoints, regla de oro #16, sección `RECEIPTS` en `fia verify`. Diseño: `docs/RECEIPT_DESIGN.md`. |
| F10 | `fia route` fino: fail-closed, reutiliza `policy.RISK_KEYWORDS`, sin archivos de estado nuevos, sin tocar `fia run --`. |
| F11 | Cierre v3.3: README EN/ES, plantillas (dos copias sincronizadas), `docs/RECEIPT_ROUTER.md`, CHANGELOG, dogfood y demo con caso de recibo manipulado. |

**Fuera de alcance (congelado hasta fricción real de F8):** Outcomes `OUT-NNN`,
Risks `RISK-NNN`, `fia outcome/risk/verify`, `fia trace`/`REQ-XXX`, migración
asistida, YAML, carpeta `.fia/`, renombrado ODD/RDD, cobertura como gate,
presupuesto anti-gaming autodeclarado.

**Referencias:** `docs/PLAN_RECIBO_ROUTER.md` · ADR-008/009/010.
