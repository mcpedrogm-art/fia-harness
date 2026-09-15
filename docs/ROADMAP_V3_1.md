# Roadmap v3.0.2 + v3.1 — Gates de calidad y honestidad

> **Estado:** aprobado por el humano (2026-09-15). Visión comprometida hasta v3.1;
> lo posterior es visión, no compromiso. Origen: feedback externo (reviews de
> calidad y de producto) + decisión humana de continuar sin esperar a la puerta F8
> (no hay usuarios externos todavía; F8 queda en pausa).

**Principios (no negociables)**
1. FIA **no juzga calidad** (no hay LLM-juez en el core): solo exige
   presencia, completitud, integridad y **decisión humana** donde hay riesgo.
2. Fail-closed solo para gobernanza (autorización humana); los avisos de calidad
   nunca bloquean por defecto.
3. `heurística → recomendación → decisión`, nunca `palabra clave → autoridad`.
4. Cada gate debe quedar verde en el dogfood del propio repo (o documentar la
   exención).
5. Nada de producto nuevo (dashboards, SaaS, mediadores en runtime, telemetría).

---

## Etapa 0 — Posicionamiento y honestidad · `v3.0.2`

**Objetivo:** que el repo diga exactamente qué garantiza y qué no.

- [ ] Hero EN/ES: `merge checks no agent can skip` →
      **"merge checks the agent cannot silently skip — inside your Git + CI trust boundary"**.
- [ ] Claim: **"A local-first governance harness for AI-assisted software development"**
      / ES: *"Un protocolo de ingeniería para trabajar con agentes sin entregarles el control"*.
- [ ] Tabla en *Limitations*: **Qué garantiza FIA · Qué NO garantiza · Qué debe hacer el humano**
      (freno de mano, no piloto automático).
- [ ] Lanzamiento alineado (`lanzamiento/1_SHOW_HN.md`, `2_DEVHUNT.md`, `3_POSTS_ES.md`)
      + destacar las 3 demostraciones: trampa → detección → **por qué se bloqueó**.
- [ ] Demo README: añadir el caso de **evidencia manipulada** (`evidence/EV-*.txt`
      editado → `PROVENANCE` FAIL), junto a la trampa de fase.
- [ ] `CHANGELOG_FIXES.md` v3.0.2 + bump de versión.

**Criterio de salida:** paridad H2 EN/ES · suite verde · `fia verify -d governance`
verde · CI verde.

---

## Etapa 1 — "Hacer lo existente sólido" · `v3.1.0`

**Objetivo:** cerrar los dos huecos reales detectados por las reviews, sin ampliar
producto.

### 1.1 Gate de riesgo → decisión humana (bloqueante)
- **Hueco:** `policy.py` detecta keywords de riesgo pero solo inyecta checklists;
  la promoción Lite→Full que promete `QUICKSTART_LITE.md` **no es mecánica**.
- **Diseño:** una fase con señales de riesgo (auth, BBDD, migraciones, secretos,
  pagos, PII, infra, servicios externos) debe tener una **decisión humana
  registrada**: `APPROVAL-NNN` citada en su checkpoint/TASK (aprobación o exención
  motivada: "no aplica porque X"). Sin decisión → `--check`/`verify` **FAIL**.
- Proyecto en **Lite** + señal de riesgo → **FAIL con instrucción de promoción**.
- **Dónde:** `core/policy.py` (señales), `core/quality.py` (regla), `core/verify.py`
  (sección `APPROVALS/RISK`), tests, `templates/QUICKSTART_LITE.md`.
- **Dogfood:** registrar `APPROVAL-002` con la autorización humana ya otorgada de
  las fases F0–F7 (y/o exención motivada para F3).

### 1.2 Sección `QUALITY` en `fia verify` (avisos, sin bloquear)
- WARN + razones, exit code intacto:
  - fases sin criterio de aceptación/entregable;
  - `TASK-Fx.md` con informe incompleto (secciones 2 diseño, 8 tests, 10 lint,
    11 build, 12 seguridad);
  - fases pendientes con señales de riesgo (planifica su decisión humana).
- **Grandfathering:** fases ya cerradas = legacy (ADR-004); el aviso aplica a
  cierres nuevos.
- *Desviación documentada:* el aviso de **completitud de SPEC** se mueve a 2.1
  (necesita una lista de secciones **configurable por tipo de proyecto**: un kit,
  una CLI o una librería no tienen "modelo de datos" ni "contratos de API").

### 1.3 Registro
- **ADR-006** — Enforcement dentro del trust boundary Git+CI; "freno de mano, no
  piloto automático"; **se rechaza el mediador en runtime** (execution boundary)
  como dirección de core; la vía es **scope verification post-hoc** (v3.2).
- **ADR-007** — Gates de calidad mecánicos: principio, secuencia y criterios de
  activación.

**Criterio de salida:** tests nuevos verdes · `--check`/`verify` verdes en el
dogfood · CI verde · evidencia (EV) citada en el checkpoint de la fase.

---

## Etapa 2 — v3.2 (solo con fricción real; visión)

| # | Mejora | Diseño clave | Activación |
|---|---|---|---|
| 2.1 | Completitud de SPEC (M2) | lista de secciones **configurable por tipo de proyecto**; WARN primero, `--strict` opcional | fricción F8 |
| 2.2 | Informe TASK completo al cerrar | secciones 2/8/10/11/12 (acepta `N/A (motivo)`); FAIL en `--sync` | fricción F8 |
| 2.3 | ADR obligatorio en fases arquitectónicas | la aprobación de riesgo cita `ADR-NNN` | tras 1.1 |
| 2.4 | Scope enforcement post-hoc | la TASK declara alcance; `verify` compara con el diff (`adapters/git.py`) | fricción F8 |
| 2.5 | Evidence reproducible (opt-in) | `fia verify --reproduce EV-NNN`, comandos allowlisted, comparar exit + hash | fricción F8 |
| 2.6 | Approval levels (intent/execution/release) + hash/firma | amplía el mecanismo existente | tras 2.3 |
| 2.7 | MICRO acotado | alcance máximo, evidencia obligatoria, promoción por riesgo | fricción F8 |
| 2.8 | Benchmark | mide desviaciones (reabiertas, retrabajo, issues). No mide "buena arquitectura" | F8 + instrumento |

**Rechazado explícitamente:** LLM-as-judge en el core · mediador en runtime ·
métricas de código como gates duros · cualquier forma de autonomía.

---

## Verificación (estándar de cada etapa)
Suite completa + tests nuevos · `--check` y `fia verify -d governance` verdes · CI
verde · evidencia registrada con `fia run` (EV) y citada en el checkpoint ·
**parada y autorización humana** antes de la etapa siguiente.

## Reanudación
El detalle operativo y el progreso viven en
`FIA_Harness_v3_PLAN_DE_EJECUCION.md` (sección 10). Si la sesión se corta, seguir
por la primera tarea sin marcar de la etapa en curso.
