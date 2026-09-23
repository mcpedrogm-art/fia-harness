# TASK-F16 — Módulo condicional TypeSafe/Jev (v3.7.0)

## Tipo de tarea
- [x] Construcción de funcionalidad nueva (fase del plan de ejecución)
- [ ] Diagnóstico / corrección de bug
- [ ] Auditoría / refactor
- [ ] Optimización de visibilidad (SEO / AEO / GEO)
- [ ] Diseño UI/UX diferencial
- [ ] Seguridad / hardening (auth, RLS, servidor, secretos)
- [ ] Otro: <especificar>

## Contexto y rol

Actúa como responsable del kit **FIA Harness**.

Estado actual del trabajo (resumen desde `PROGRESS.md`):
- F0–F15 cerradas (v3.6.3 publicada; F8 en pausa).
- F16 en curso: dotar al kit de un **módulo condicional** para integrar
  **TypeSafe AI (modelo Jev, "System One")** en el producto que el usuario
  construye, con detección automática en el PRD y salvaguardas de gobernanza.
- Amparada por `APPROVAL-008` y el ADR-015.

Origen: petición del humano (2026-09-23): *"si paso un PRD de un sistema de
trading que incluya JEV, al desarrollarlo con FIA Harness quiero tener la
posibilidad de incluirlo en el propio sistema que desarrollemos"*. Se investigó
en profundidad la documentación oficial (<https://docs.typesafe.ai/introduction>)
y se decidió el mismo patrón que el módulo RAG: módulo documental condicional,
detectado y activado por `bootstrap.py`.

Reglas de commit/push/deploy: **commit y push autorizados por el humano**
(2026-09-23, "COMIT AND PUSH" + reflejo como punto de versión).

## ALCANCE PERMITIDO (scope)

- README.md
- README.es.md
- CHANGELOG_FIXES.md
- pyproject.toml
- fia_harness/__init__.py
- fia_harness/cli.py
- fia_harness/generators/bootstrap.py
- fia_harness/parser/prd.py
- fia_harness/parser/discovery.py
- fia_harness/data/templates/*
- templates/*
- tests/*
- governance/*

---

# OBJETIVO DE LA TAREA

**Objetivo (desde PROGRESS.md):** módulo condicional TypeSafe/Jev: detección en
el PRD y activación automática del módulo documental para construir decisiones
estructuradas con IA dentro del producto (v3.7.0).
**Dependencias:** F1 (parser/CLI), F7 (CI), F15 (patrón de módulo/versión).

---

# FASE A — AUDITORÍA

1. **TypeSafe/Jev es un modelo "System One"**, no un LLM de chat ni de código:
   recibe `state` + preguntas tipadas (Choice/Score/Noul) y devuelve respuestas
   estructuradas + probabilidades + `confidence`. La propia documentación advierte
   que **no sustituye al modelo del agente**: se usa *dentro del producto*.
2. **No existía ningún soporte** en el kit (grep de `typesafe|jev|systemone` sin
   coincidencias).
3. **Patrón existente a reutilizar:** `RAG_VECTOR_EXTENSION.md` (módulo condicional
   detectado por `parser.prd.RAG_KEYWORDS` y copiado por
   `bootstrap.maybe_activate_rag_module`). Se replica para no inventar mecanismo.
4. **Riesgo de falsos positivos:** activar por "clasificación" o "confianza"
   genéricos sería ruidoso → palabras clave específicas (marca + términos
   distintivos).

Decisiones humanas (2026-09-23): implementar el **módulo documental** (no CLI de
red); la API key se trata como secreto; la conexión exige aprobación (Regla de Oro
nº6); versión **v3.7.0** (nueva funcionalidad); commit y push autorizados.

# FASE E — IMPLEMENTACIÓN

- **Plantilla `TYPESAFE_EXTENSION.md`** (raíz `templates/` + paquete
  `fia_harness/data/templates/`, copias byte-idénticas): contrato de la API
  (`POST /v1/systemone`), tres primitivas, confianza y umbrales, cuatro patrones,
  integración (HTTP `urllib` / SDK Python / SDK JS), ejemplo de trading, seguridad
  (API key como secreto, `state` que sale del entorno, coste, precisión en
  español), gobernanza y checklist.
- **Detección:** `parser/prd.py` añade `TYPESAFE_KEYWORDS` (regex específica).
- **Activación:** `generators/bootstrap.py` extrae el helper común
  `_maybe_activate_module` (reutilizado por RAG y TypeSafe) y añade
  `maybe_activate_typesafe_module`, invocado en `main()` tras el RAG.
- **Distribución:** `cli.TEMPLATE_NAMES` incluye el módulo (llega a `/docs` con
  `fia init`); `parser/discovery.NON_PRD_FILES` lo excluye como PRD.
- **Gobernanza documental:** fila en `SKILLS_MCP.md`; punto 13 de `SPEC.md` +
  checklist + lista de archivos en `INICIO_PROYECTO.md`; nota en `AGENTS.md`;
  sección 4 en `MODELOS.md`; tabla de módulos condicionales y sección v3.7 en
  README EN/ES.

# FASE I — TESTS

- `tests/test_parser_prd.py`: keywords positivas y sin falsos positivos;
  `TYPESAFE_EXTENSION.md` excluido como PRD.
- `tests/test_generators_bootstrap.py`: nombre del módulo y activación/no
  activación por PRD (TypeSafe y RAG).
- `tests/test_packaging.py`: anti-drift del paquete incluye el módulo. Suite:
  313 → 319.

# FASE J2 — SEGURIDAD

Sin secretos en el repositorio (la API key vive en `TYPESAFE_API_KEY`, tratada como
secreto y cubierta por gitleaks). El módulo **no** ejecuta red: solo documenta y
gobierna la integración. Se advierte de que el `state` enviado abandona el entorno
y de la necesidad de aprobación humana previa (Regla de Oro nº6).

# FASE K — VALIDACIÓN

```bash
python -m unittest discover tests
python -m fia_harness.cli verify -d governance --strict-receipts
```

E2E manual con un PRD de trading: `fia init` + `bootstrap.py` → activa
`TYPESAFE_EXTENSION.md`, **no** activa RAG, `fia check` en verde.

---

# FASE L — INFORME FINAL OBLIGATORIO

## TASK-F16 — INFORME FINAL

### 1. Resumen de lo realizado
Nuevo módulo condicional `TYPESAFE_EXTENSION.md` (espejo del RAG) para integrar
**TypeSafe/Jev** dentro del producto: el PRD lo activa automáticamente y el agente
recibe contrato de API, primitivas, patrones, ejemplo y salvaguardas. Detección,
distribución y gobernanza documental actualizadas. Versión **v3.7.0**.

### 2. Diagnóstico o decisiones de diseño tomadas
- Jev es capa de decisión, **no** modelo de código: el módulo lo declara explícito.
- Se reutiliza el patrón del módulo RAG (helper común) en vez de inventar mecanismo.
- Keywords específicas para evitar activaciones ruidosas.
- API key = secreto; conexión con aprobación humana (Regla de Oro nº6).
- Alternativa descartada: subcomando CLI con red (rompería stdlib-only/local-first
  y no era lo pedido: se quiere construir con Jev *en el producto*).

### 3. Archivos modificados (lista + explicación concreta)
- `templates/TYPESAFE_EXTENSION.md` + `fia_harness/data/templates/…` (módulo).
- `fia_harness/parser/prd.py` (`TYPESAFE_KEYWORDS`).
- `fia_harness/generators/bootstrap.py` (helper + activación).
- `fia_harness/cli.py`, `fia_harness/parser/discovery.py` (distribución/exclusión).
- `templates/` + paquete: `SKILLS_MCP.md`, `INICIO_PROYECTO.md`, `AGENTS.md`,
  `MODELOS.md`; README EN/ES; `CHANGELOG_FIXES.md`, `pyproject.toml`,
  `fia_harness/__init__.py` (v3.7.0).
- `tests/test_parser_prd.py`, `tests/test_generators_bootstrap.py`,
  `tests/test_packaging.py`.
- `governance/*` (TASK, DECISIONS, PROGRESS, evidencia y recibo).

### 4. Máquina de estados (si aplica)
No aplica.

### 5. Protección contra duplicados/errores implementada
- `_maybe_activate_module` es idempotente y no sobrescribe lo existente.
- `TYPESAFE_EXTENSION.md` en `NON_PRD_FILES` (nunca se confunde con el PRD).
- Anti-drift: copias raíz/paquete verificadas por test.
- Aviso explícito si el PRD lo pide pero el módulo no está en `/docs` (regla nº2).

### 6. Compatibilidad verificada (entornos/plataformas)
- Solo añade plantilla y detección; ningún flujo existente del kit se altera.
- Suite 319/319 en Windows (EV-028). E2E con PRD de trading verificado.

### 7. Visibilidad SEO/AEO/GEO — No aplica (kit sin superficie pública).

### 8. Tests
`319/319 passed` (suite completa, Windows / Python 3.14; evidencia EV-028).

### 9. Typecheck
N/A (stdlib-only; sin typecheck configurado).

### 10. Lint
N/A (sin linter configurado en el kit).

### 11. Build
N/A (cambio de plantilla + detección; el job `wheel` de CI cubre el empaquetado).

### 12. Seguridad (Fase J2): sin secretos; módulo documental sin red; API key como
secreto (`TYPESAFE_API_KEY`); conexión con aprobación humana previa.

### 13. Archivos NO modificados
`core/verify.py`, `core/receipts.py`, `core/router.py`, `core/state.py`,
`core/evidence.py` y el resto del núcleo.

### 14. Git: `Commit: SÍ (autorizado)` · `Push: SÍ (autorizado)` · `Deploy: NO`

### 15. Prueba manual recomendada
Poner un `PRD.md` que mencione TypeSafe/Jev en la raíz, ejecutar `python
bootstrap.py` y comprobar que aparece `TYPESAFE_EXTENSION.md` en la raíz (y que el
RAG no se activa si no aplica).

### 16. Resultado final:
```text
TAREA COMPLETADA
```

### 17. Próximo paso sugerido
Retomar F8 (validación externa) o publicar v3.7.0 (release).

### 18. Skills/MCP y aprobación humana
El módulo documenta la conexión con TypeSafe (capacidad externa) y exige
aprobación previa (Regla de Oro nº6). `APPROVAL-008` y ADR-015 amparan el cambio.

### 19. UI/UX diferencial — No aplica.

### 20. Contexto y prompt injection — El módulo advierte de tratar el `state` como
dato no confiable y de no dejar que su contenido cambie reglas ni umbrales.
