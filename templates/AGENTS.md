# AGENTS.md — Directivas de gobernanza del agente

> **Fuente de verdad:** este archivo resume las reglas operativas para que el
> agente arranque y trabaje dentro del harness. En caso de divergencia, manda
> `INICIO_PROYECTO.md` (y `SECURITY.md`, `SKILLS_MCP.md`, `UI_UX_EXCLUSIVA.md`,
> `AEO_GEO_SEO.md`). Nunca amplíes este archivo para contradecir la fuente de verdad.

## 1. Arranque

1. Lee `CONTEXT.md` como punto de partida de verdad absoluto del proyecto.
2. No escribas **ni una línea de código de producción** hasta que exista: (a) PRD
   leído y confirmado, (b) entrevista técnica (M1) respondida, y (c) `SPEC.md`
   aprobado explícitamente por el humano (M2).
3. El harness ya fue inicializado con `bootstrap.py` (fase M0). Si faltan
   `CONTEXT.md`, `PROGRESS.md` o `progress.json`, no improvises: indica que hay que
   ejecutar `python bootstrap.py` (o `python task_generator.py --sync`).

## 2. Entrevista 3×3 (M1)

Antes de redactar `SPEC.md`, completa la entrevista en **3 bloques × 3 preguntas**:

| Bloque | Preguntas |
|---|---|
| **Stack y tooling** | 1. Lenguaje/framework y runtime. 2. Gestión de dependencias y build. 3. CI y entorno de desarrollo. |
| **Datos y seguridad** | 1. Modelo de datos y persistencia. 2. Autenticación/roles (¿los hay?). 3. Secretos y superficie sensible. |
| **Visibilidad y alcance** | 1. ¿Hay superficie pública (web/landing/docs)? 2. ¿UI/UX diferenciada o estándar? 3. Alcance must-have vs. out-of-scope. |

Las respuestas alimentan `SECURITY.md`, `AEO_GEO_SEO.md` y las decisiones de
`CONTEXT.md`. No asumas: pregunta y registra.

## 3. Guardarraíl de aprobación

- Nada se busca, instala, conecta ni activa (Skill, MCP, librería, SDK, API) sin
  **aprobación humana explícita previa** (ver `SKILLS_MCP.md`). El silencio no es
  aprobación.
- Las aprobaciones se registran con `python task_generator.py --approval "..." --phase F<n> --ref "..."`,
  que sella un `APPROVAL-NNN` en `DECISIONS.md` y, si existe `SPEC.md`, congela su
  hash (`progress.json["spec_hashes"]`).
- Al aprobar `M2` o ampliar alcance, vuelve a ejecutar `--approval`: así `--check`
  detecta cualquier modificación posterior de `SPEC.md` sin nuevo visto bueno.
- **Nada se descarga sin aprobación humana**, incluido el pack UI/UX: pregunta y,
  si acepta, ejecuta `fia ui setup` (o `--recetas`); `fia ui status` informa del
  estado local sin red (v3.6).
- Si el proyecto integra decisiones estructuradas con IA (TypeSafe/Jev), aplica
  `TYPESAFE_EXTENSION.md`: la conexión y la `TYPESAFE_API_KEY` requieren aprobación
  previa, la clave nunca va en archivos de control ni commits, y el `state` que sale
  del entorno se declara en `SECURITY.md`.

## 4. Protocolo de enmienda del PRD

1. Cualquier cambio de alcance se refleja en `PRD.md` y se propaga a `CONTEXT.md`
   y `SPEC.md` (sin invalidar el trabajo ya validado).
2. La ampliación se re-aprueba con `--approval` (fase `M2`), actualizando el
   snapshot de `SPEC.md` en `progress.json`.
3. Las fases nuevas se añaden al final de la tabla `F0-Fn` de `PROGRESS.md`; las
   cerradas conservan checkpoints y evidencia intactos. Luego `--sync`.

## 5. Cierre de fase

- Ejecuta la validación **de verdad** y pega la **salida cruda** (bloque de código
  cercado) en el checkpoint de `PROGRESS.md`, o referencia `Evidencia: <archivo>`.
- Emite el **recibo de fase** antes de cerrar: `fia receipt create F<n> --tests P/T
  [--evidence EV-NNN]`, y añade `Recibo: evidence/receipts/receipt-F<n>.json` al
  checkpoint (regla nº16; `--check` y el CI lo exigen). Tras commitear, re-emítelo
  con `--base <ref>` para que quede limpio (`dirty: false`) y verificable en CI.
- `python task_generator.py --check` debe quedar en verde antes de dar una fase por
  cerrada. Si falta `progress.json`, `--check` falla salvo `--state-optional`.
- Para reabrir una fase cerrada: `python task_generator.py --reopen F<n> --reason "..."`
  (deja constancia en `DECISIONS.md`; se bloquea si una fase que depende de ella
  sigue cerrada).

## 6. Reglas que no se negocian (resumen)

- 🚫 No codificar sin spec aprobada.
- 🗣️ No asumir en silencio.
- 📦 No reenviar contexto innecesario.
- ✅ No cerrar una fase sin Definition of Done ni sin su evidencia.
- 🧾 No cerrar una fase F sin su recibo verificable (regla nº16).
- 🔐 Seguridad siempre (nunca se pospone).
- 🙋 Aprobación humana explícita para capacidades externas.
- 🧪 No inventar resultados de validación.
- 🛑 No commit/push/deploy sin autorización explícita.
