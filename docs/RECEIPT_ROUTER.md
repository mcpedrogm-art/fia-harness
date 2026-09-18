# Recibo de fase y router de carril (v3.3)

> Documento de uso. Diseño interno: `docs/RECEIPT_DESIGN.md` · Plan:
> `docs/PLAN_RECIBO_ROUTER.md` · ADR-009/010 en `DECISIONS.md`.

---

## 🧾 Recibo de fase (regla de oro nº16)

**Qué es:** un archivo JSON por fase (`evidence/receipts/receipt-F<N>.json`) con un
manifiesto canónico: los archivos de producto que tocó la fase (hash SHA-256 de su
contenido normalizado), los checks declarados (tests, lint, scope, reglas de oro),
la evidencia `EV-NNN` referenciada, el commit y el modo. Su hash propio
(`receipt_sha256`) se calcula sin `generated_at`, así que es **determinista**.

**Qué NO es:** una prueba de verdad. Ata **contenido** a un commit: detecta
manipulación posterior al cierre, pero no puede probar que los checks declarados
ocurrieron. La frontera `local`/`trusted` de ADR-005 se mantiene.

### Flujo normal

```bash
# 1. Con la fase F<N> en curso (tras implementar y validar):
fia receipt create F<N> --tests 42/42 [--evidence EV-NNN] [--base <ref>]

# 2. En PROGRESS.md, en el checkpoint de la fase:
#    Evidencia: EV-NNN
#    Recibo: evidence/receipts/receipt-F<N>.json

# 3. Cierra la fase y compila:
fia sync && fia verify
```

- `--base <ref>` fija el punto de partida del diff (`ref...HEAD`). Sin él se usan
  los cambios sin commitear.
- `dirty: false` (recomendado para CI): el recibo se ata al commit actual y se
  verifica contra él **para siempre**, aunque fases posteriores toquen los mismos
  archivos. `dirty: true`: ancla local contra el árbol de trabajo.
- Tras commitear, re-emite con `--base` para pasar de `dirty` a limpio (la
  re-emisión también repara un recibo ausente).

### Verificación

| Comando | Qué hace |
|---|---|
| `fia receipt verify F<N>` | Estricto: hash propio + archivos contra commit (o árbol si dirty) + evidencias |
| `fia verify` | Sección `RECEIPTS`: limpios → estricto; `dirty` → nota local (no bloquea el trabajo local) |
| `fia verify --strict-receipts` | CI: los `dirty` se comparan contra el árbol y **bloquean** el merge |

**Grandfathering:** las fases cerradas antes del 2026-09-18 no exigen recibo
(ADR-009), igual que el resto de gates de v3.1.

---

## 🚦 Router de carril (`fia route`)

```bash
$ fia route "actualizar la documentación del README"
[ROUTER] Carril: LITE
[ROUTER] Razón: coincide con la allowlist: actualización de documentación

$ fia route "corregir typo en el mensaje de error de login"
[ROUTER] Carril: FULL
[ROUTER] Razón: señales de riesgo: login
```

- **Determinista y fail-closed:** señales de riesgo (`policy.RISK_KEYWORDS`) →
  Full; allowlist cerrada (bug acotado, refactor local, solo tests, lint/typos,
  docs) → propone Lite con razones; sin coincidencia → Full.
- **No decide ni ejecuta:** solo clasifica. La decisión humana se registra igual y
  el gate v3.1 (regla nº13) sigue siendo el enforcement real: una fase Lite con
  señales de riesgo no compila.
- **Sin estado:** no hay archivos de presupuesto; un contador autodeclarado por el
  agente sería teatro (ADR-010).

---

## ⚠️ Límites honestos

- Un recibo no prueba la verdad de los checks: solo que el contenido y las
  referencias son coherentes y no cambiaron desde el cierre.
- Un recibo `dirty` deja de coincidir en cuanto hay trabajo posterior sin
  commitear; por eso CI exige limpios y `fia receipt verify` es siempre estricto.
- El router es una recomendación: la heurística de palabras clave puede no ver un
  riesgo no listado. Ante duda, Full.
