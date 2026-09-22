# TASK-F15 — Fix del CI generado (v3.6.3)

## Tipo de tarea
- [ ] Construcción de funcionalidad nueva (fase del plan de ejecución)
- [x] Diagnóstico / corrección de bug
- [ ] Auditoría / refactor
- [ ] Optimización de visibilidad (SEO / AEO / GEO)
- [ ] Diseño UI/UX diferencial
- [ ] Seguridad / hardening (auth, RLS, servidor, secretos)
- [ ] Otro: <especificar>

## Contexto y rol

Actúa como responsable del kit **FIA Harness**.

Estado actual del trabajo (resumen desde `PROGRESS.md`):
- F0–F14 cerradas (v3.6.2 publicada; F8 en pausa).
- F15 en curso: el job `calidad` del workflow generado debe detectar el stack
  en cualquier subcarpeta y nunca omitir pasos en silencio.
- Amparada por `APPROVAL-007` y el ADR-014.

Origen del hallazgo: auditoría externa (2026-09-22) de un proyecto real
construido con el kit. En ese proyecto el backend vive en `src/api/` y el job
`calidad` declaraba tests + auditoría, pero **los pasos de Python se saltaban en
silencio** porque `hashFiles(...)` solo mira la raíz; además `npm test
--if-present` no verificaba nada. Resultado: CI verde sin ejecutar la suite.

Reglas de commit/push/deploy: **commit local autorizado por el humano**
(2026-09-22); push no autorizado; deploy no aplica.

## ALCANCE PERMITIDO (scope)

- fia_harness/generators/scaffold.py
- tests/test_generators_bootstrap.py
- CHANGELOG_FIXES.md
- pyproject.toml
- fia_harness/__init__.py
- governance/**

---

# OBJETIVO DE LA TAREA

**Objetivo (desde PROGRESS.md):** fix del CI generado: detección del stack en
subcarpetas y sin omisiones silenciosas (regla 7).
**Dependencias:** F7 (CI / Merge Gate mínimo).

---

# FASE A — AUDITORÍA

Hallazgos sobre `scaffold.GITHUB_WORKFLOW` (plantilla del workflow generado):

1. **Detección solo-raíz:** `hashFiles('requirements.txt')`,
   `hashFiles('pyproject.toml')` y `hashFiles('tests/**/test_*.py')` buscan en la
   raíz del repo. En un monorepo (`src/api/pyproject.toml`, `src/api/tests/`) las
   condiciones son falsas → `setup-python`, instalación, tests y `pip-audit` se
   **saltan sin aviso** (viola la regla de oro nº2: nunca asumir en silencio).
2. **No-op silencioso en Node:** `npm test --if-present` no ejecuta nada si el
   `package.json` no define `scripts.test` (CI verde sin tests).
3. **Fallo enmascarado en Python:** `pytest -q || unittest discover` ejecuta el
   fallback cuando pytest falla, ocultando el fallo real de la suite.
4. **Sin rastro de lo omitido:** las condiciones `if:` no dejan anotación; el job
   aparenta verificar más de lo que hace.

Decisiones humanas (2026-09-22): stack detectado sin tests → **aviso visible no
bloqueante** (`::warning::`, coherente con ADR-007); commit local autorizado.

# FASE E — IMPLEMENTACIÓN

- **Paso de detección** (`id: stack`) en `calidad`, previo a los pasos de stack:
  localiza con `git ls-files` el proyecto Node (`package.json`) y Python
  (`pyproject.toml`/`requirements.txt`) **menos profundo** de todo el repo,
  ignorando `node_modules/`, `.venv/` y `.git/`; publica `node_dir`/`py_dir` en
  `$GITHUB_OUTPUT`. Si no hay ninguno, aviso final `::warning::`.
- **Pasos Node/Python** condicionados a que el directorio detectado exista y
  ejecutados con `working-directory` en ese directorio (monorepo-friendly).
- **Sin script `test`** en `package.json` → `::warning::` visible (regla 7).
- **Sin carpeta `tests/`** en el proyecto Python → `::warning::` visible.
- **Tests Python sin enmascarar:** `if pytest disponible → pytest -q; else
  unittest discover`.
- **Auditoría:** `npm audit --audit-level=high` en el proyecto Node; `pip-audit`
  sobre `requirements.txt` o sobre el entorno instalado (`pip install -e .`).
- La cabecera del workflow documenta la detección y que es personalizable.

# FASE I — TESTS

`tests/test_generators_bootstrap.py`: asserts nuevos sobre el workflow generado
(paso "Detectar stack", salidas `steps.stack.outputs.*`, `::warning`, ausencia de
`--if-present` y de la detección solo-raíz). Suite: 311 → 313.

# FASE J2 — SEGURIDAD

Sin secretos nuevos; la detección usa `git ls-files` sobre el checkout; sin
descargas ni permisos nuevos; las auditorías siguen siendo fail-closed en
vulnerabilidades.

# FASE K — VALIDACIÓN

```bash
python -m unittest discover tests -v
python -m fia_harness.cli verify -d governance --strict-receipts
```

---

# FASE L — INFORME FINAL OBLIGATORIO

## TASK-F15 — INFORME FINAL

### 1. Resumen de lo realizado
El CI que genera `bootstrap.py` ya no se salta pasos en silencio: detecta el
proyecto Node/Python **menos profundo** del repo (monorepos incluidos), ejecuta
tests y auditoría en esa carpeta y avisa con `::warning::` cuando no hay stack,
script `test` o carpeta `tests/`. Se elimina el no-op `npm test --if-present` y
el enmascaramiento `pytest || unittest`. Versión **v3.6.3**.

### 2. Diagnóstico o decisiones de diseño tomadas
- Causa raíz: `hashFiles(...)` solo mira la raíz → skip silencioso en monorepos
  (viola la regla de oro nº2: nunca asumir en silencio).
- Decisión humana (2026-09-22): aviso visible **no bloqueante** si falta stack o
  tests (coherente con ADR-007); commit local autorizado.
- Detección con `git ls-files` (sin dependencias; corre en ubuntu) del proyecto
  menos profundo; ignora `node_modules/`, `.venv/` y `.git/`.
- Alternativa descartada: job en rojo si no hay tests (rompería fases tempranas).

### 3. Archivos modificados (lista + explicación concreta)
- `fia_harness/generators/scaffold.py`: plantilla `GITHUB_WORKFLOW` con el paso
  `Detectar stack` (`$GITHUB_OUTPUT`), pasos Node/Python con `working-directory`,
  `::warning::` de la regla 7 y fallback `if/elif` sin enmascarar.
- `tests/test_generators_bootstrap.py`: 2 tests nuevos (detección/warnings y
  no-enmascaramiento).
- `CHANGELOG_FIXES.md`, `pyproject.toml`, `fia_harness/__init__.py` (v3.6.3),
  `governance/*` (TASK, DECISIONS con ADR-014/APPROVAL-007, PROGRESS).

### 4. Máquina de estados (si aplica)
No aplica.

### 5. Protección contra duplicados/errores implementada
- `bootstrap.py` sigue sin sobrescribir workflows existentes: el fix aplica a
  proyectos nuevos; los ya creados se actualizan a mano (como en la auditoría).
- Detección determinista e idempotente; `working-directory` evita ejecutar en la
  raíz por error.
- Los tests nuevos fijan el contrato (detección, warnings, no enmascarar).

### 6. Compatibilidad verificada (entornos/plataformas)
- Solo cambia la plantilla generada; ningún flujo del kit se altera.
- Suite 313/313 en Windows (EV-027). Bloque bash verificado con Git Bash contra
  un monorepo real (`node_dir=.` · `py_dir=src/api`) y contra el propio kit
  (`node_dir=ninguno` · `py_dir=.`).

### 7. Visibilidad SEO/AEO/GEO — No aplica (kit sin superficie pública).

### 8. Tests
`313/313 passed` (suite completa, Windows / Python 3.14; evidencia EV-027) +
verificación manual del bloque bash en los dos escenarios (monorepo y raíz).

### 9. Typecheck
N/A (stdlib-only; sin typecheck configurado).

### 10. Lint
N/A (sin linter configurado en el kit).

### 11. Build
N/A (cambio de plantilla; el job `wheel` de CI cubre el empaquetado).

### 12. Seguridad (Fase J2): sin secretos; la detección usa `git ls-files` sobre
el checkout; sin descargas ni permisos nuevos; auditorías fail-closed intactas.

### 13. Archivos NO modificados
`core/verify.py`, `core/receipts.py`, `core/router.py`, `core/state.py`,
`core/evidence.py` y el resto del núcleo.

### 14. Git: `Commit: SÍ (local, autorizado)` · `Push: NO` · `Deploy: NO`

### 15. Prueba manual recomendada
En un monorepo con backend en `src/api/`: `fia init` + `bootstrap.py` y comprobar
que el workflow generado detecta `src/api` (o pegar el bloque `Detectar stack` en
un workflow existente y ver los outputs).

### 16. Resultado final:
```text
TAREA COMPLETADA
```

### 17. Próximo paso sugerido
Retomar F8 (validación externa) o publicar v3.6.3 (release).

### 18. Skills/MCP y aprobación humana
No aplica (sin capacidades externas). `APPROVAL-007` y ADR-014 amparan el cambio.

### 19. UI/UX diferencial — No aplica.

### 20. Contexto y prompt injection — No aplica.
