# RECEIPT_DESIGN.md — Diseño del recibo de fase (v3.3 · F9 · R1)

> **Estado:** aprobado por el humano (2026-09-18, APPROVAL-003).
> **Alcance:** decisiones de diseño de R1. Sin código.
> **Plan:** `docs/PLAN_RECIBO_ROUTER.md` · **ADRs:** `governance/DECISIONS.md` (ADR-008/009).

---

## 1. Qué es y qué NO es

**Es:** un ancla de auditoría que ata el contenido final de los archivos de una fase
cerrada a un commit/tree concreto y a los checks ejecutados en ese momento. Permite
detectar manipulación **post-cierre** (hoy indetectable: `scope.py` solo mira la
fase en curso).

**NO es:** una prueba de verdad. Los resultados de `checks` son declaraciones de la
ejecución local; la frontera `local`/`trusted` de ADR-005 se mantiene. En CI, el
recibo se regenera desde un checkout limpio (`trusted`). Tampoco sustituye a la
evidencia `EV-NNN`: la **referencia**.

## 2. Manifiesto canónico (lo que se hashea)

```json
{
  "version": "1.0",
  "task_ref": "TASK-F9.md",
  "mode": "FULL",
  "commit_or_tree_ref": "<git rev-parse HEAD>",
  "dirty": false,
  "files": [
    {"path": "fia_harness/core/receipts.py", "content_sha256": "<hex>"}
  ],
  "checks": {
    "golden_rules": "pass",
    "tests": {"passed": 212, "total": 212},
    "lint": "pass",
    "scope": "pass"
  },
  "evidence_refs": ["EV-004"]
}
```

Reglas exactas:

- `files` ordenado alfabéticamente por `path`; rutas **relativas a la raíz del
  repo** (funciona con el estado en subcarpeta, p. ej. `-d governance`).
- Un archivo **borrado** por la fase se representa como
  `{"path": ..., "content_sha256": null, "deleted": true}` y la verificación exige
  su ausencia (en el commit o en el árbol, según `dirty`); los recibos antiguos sin
  `deleted` se tratan como no borrados (compatible).
- `content_sha256` = SHA-256 del contenido final **normalizado**: BOM UTF-8
  eliminado, CRLF → LF, UTF-8. Si el archivo no es texto válido (byte nulo en los
  primeros 8 KB), se hashea el byte crudo sin normalizar.
- Los archivos de gobernanza implícitos (`scope.IMPLICIT_ALLOWED`: `PROGRESS.md`,
  `progress.json`, `DECISIONS.md`, `SPEC.md`, `CONTEXT.md`, `TASK-*.md`,
  `evidence/**`, `reproduce.json`) **no entran** en el manifiesto: su integridad ya
  vive en `progress.json`/huellas, y el recibo no puede depender de un checkpoint
  que se escribe después de emitirlo.
- El manifiesto hasheado **excluye** `generated_at` y `receipt_sha256`.
- `receipt_sha256 = sha256(canonical_json(manifest))` con `sort_keys=True`,
  `separators=(",", ":")`, `ensure_ascii=False`, codificación UTF-8.
  Sin `timestamp` dentro del hash → determinismo: mismo árbol + mismos checks =
  mismo hash.
- `checks`: valores `pass|fail|skip`; `tests` = `{passed:int, total:int}`.
- `mode`: `FULL|LITE` (coherente con QUICKSTART_LITE).
- `dirty: true` si hay cambios **de producto** sin commitear (entra en el hash; la
  gobernanza implícita no cuenta: es bookkeeping del propio estado). `create` falla
  si está sucio salvo `--allow-dirty`; el CI exige `dirty` ausente.
- `commit_or_tree_ref`: `git rev-parse HEAD` (v1 requiere repo git; el kit asume el
  trust boundary Git+CI, ADR-006).

## 3. Archivo del recibo

`evidence/receipts/receipt-<Fase>.json` = manifiesto + metadata **fuera del hash**:

```json
{ "<manifiesto>": "...", "generated_at": "2026-09-18T10:00:00Z", "receipt_sha256": "<hex>" }
```

- `evidence/receipts/` cae bajo `evidence/**`, ya permitido por `scope.py`.
- `generated_at` es informativo y no afecta al hash.

## 4. Estado (`progress.json`)

- El checkpoint de la fase acepta la línea `Recibo: evidence/receipts/receipt-F9.json`
  (parser: misma familia que `Evidencia:`); se compila a `checkpoint["receipt_ref"]`.
- El hash **no se duplica** en `progress.json`: vive en el recibo y `receipt verify`
  lo recalcula. `progress.json` ya está protegido por `state_sha256`.
- **Regla de oro #16:** una fase F `done` sin `receipt_ref` válido → error en
  `--check` y sección `RECEIPTS` de `fia verify`.
- **Grandfathering:** fases con `recorded_at` < `2026-09-18` (constante
  `RECEIPT_GRANDFATHER_BEFORE`, mismo patrón que `quality.GRANDFATHER_BEFORE`)
  exentas. F0–F8 quedan legacy.

## 5. CLI

**`fia receipt create <Fase> [--base REF] [--evidence EV-NNN ...] [--tests P/T] [--lint pass|fail|skip] [--allow-dirty]`**

- Acepta la fase `in_progress` (flujo normal) o `done` (re-emisión tras commitear
  para pasar de `dirty` a limpio, o reparar un recibo ausente); en `done` la
  validación previa de recibos se omite (es la que se va a reparar) y se avisa.
- `files` = archivos cambiados vía `adapters/git.py` (`--base REF`, por defecto el
  working tree sin commitear) **excluyendo la gobernanza implícita** (ver §2). Sin
  archivos de producto → error (una fase sin cambios no es una fase).
- `golden_rules` se calcula con `collect_validation_errors` en el momento de crear:
  si el estado no está limpio, no se emite recibo.
- `evidence_refs`: cada `EV-NNN` debe existir y validar.
- El comando **empaqueta**, no certifica verdad.

**`fia receipt verify <Fase>`** (exit 0/1):

1. Localiza `receipt_ref` (o `evidence/receipts/receipt-<Fase>.json`).
2. Recalcula `receipt_sha256` del manifiesto → debe coincidir.
3. Verifica `files`: contra el commit referenciado (`git show`) o, si el recibo es
   `dirty`, contra el árbol de trabajo actual (estricto; `fia verify` sin
   `--strict-receipts` aplaza esta comparación).
4. Verifica que cada `evidence_refs` existe.
5. PASS/FAIL con razones.

## 6. CI y semántica local/estricta

- `--check`/`sync` aplican la regla #16 en su forma barata: recibo referenciado,
  presente y con hash coherente.
- `fia verify` (local): recibo **limpio** → verificación estricta contra su commit
  (histórica y estable); recibo **`dirty`** → nota «local», verificación estricta
  aplazada (cualquier trabajo posterior invalida la comparación con el árbol; es
  esperado y no bloquea el trabajo local).
- `fia verify --strict-receipts` (CI): los `dirty` se comparan contra el árbol de
  trabajo → un recibo sucio bloquea el merge. El workflow del kit lo usará (F11).
- `fia receipt verify <Fase>`: siempre estricto (pregunta explícita).
- Recibo generado en CI (checkout limpio) = `trusted`; local = `local` (ADR-005).

## 7. Matriz de tests (R6)

| Caso | Esperado |
|---|---|
| Mismo árbol + checks, 2 ejecuciones | Mismo `receipt_sha256` (determinismo) |
| 1 byte alterado en un archivo | Hash distinto · `verify` FAIL |
| CRLF vs LF, con/sin BOM | Mismo hash (normalización) |
| Commit inexistente / repo no git | `verify` FAIL con razón |
| `EV-NNN` inexistente | `create` FAIL |
| Fase `done` sin `Recibo:` | `--check` FAIL |
| Fase legacy (recorded_at antiguo) sin recibo | PASS (grandfathering) |
| `receipt_sha256` manipulado en el archivo | `verify` FAIL |
| Consola Windows cp1252 | Sin errores de codificación |
| Suite y proyectos existentes | Intactos (backward compatible) |

## 8. Límites honestos

- No detecta mentira local en los checks (`tests: passed` es una declaración); la
  detección real es la regeneración en CI (`trusted`).
- No cubre proyectos sin git.
- No sustituye evidencia (`EV-NNN`) ni Definition of Done.
