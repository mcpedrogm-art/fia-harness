# TASK-F11 — Cierre v3.3 (docs, plantillas, CHANGELOG, demo)

## Tipo de tarea
- [x] Construcción de funcionalidad nueva (fase del plan de ejecución)
- [ ] Diagnóstico / corrección de bug
- [ ] Auditoría / refactor
- [ ] Optimización de visibilidad (SEO / AEO / GEO)
- [ ] Diseño UI/UX diferencial
- [ ] Seguridad / hardening (auth, RLS, servidor, secretos)
- [ ] Otro: <especificar>

## Contexto y rol

Actúa como responsable de release del proyecto **FIA Harness**.

Estado actual del trabajo (resumen desde `PROGRESS.md`):
- F0–F10 cerradas (recibo de fase y router operativos); F8 en pausa.
- F11 en curso: cierre v3.3 (documentación, plantillas, CHANGELOG, CI estricto y demo).
- El recorte está amparado por `APPROVAL-003` y los ADR-008/009/010.

Reglas de commit/push/deploy: commit autorizado por el humano en esta sesión;
**push/deploy NO**.

## ALCANCE PERMITIDO (scope)

- fia_harness/**
- tests/**
- docs/**
- governance/**
- templates/**
- .github/**
- README.md
- README.es.md
- CHANGELOG_FIXES.md
- pyproject.toml

---

# OBJETIVO DE LA TAREA

**Objetivo (desde PROGRESS.md):** cierre v3.3: README EN/ES, plantillas (dos copias
sincronizadas), `docs/RECEIPT_ROUTER.md`, CHANGELOG, CI estricto y demo.
**Dependencias:** F10.

---

# FASE A — AUDITORÍA

Revisado: README EN/ES (paridad H2), plantillas raíz y del paquete (test anti-drift
`test_packaging.test_templates_match_repo_root` ya existía), workflow generado
(`scaffold.py`), CI del repo y del demo, CHANGELOG y roadmap.

# FASE E — IMPLEMENTACIÓN

- **Regla nº16** en `INICIO_PROYECTO.md` (+ nota de enforcement), `AGENTS.md`
  (cierre y resumen) y `TASK_TEMPLATE.md` (bloque de recibo); `QUICKSTART_LITE.md`
  documenta `fia route` en el triage. Copias de `templates/` y
  `fia_harness/data/templates/` sincronizadas (test anti-drift en verde).
- **README EN/ES**: recibo, router, comandos, sección «What v3.3 adds», límites
  honestos, dogfood (282 tests, EV-001…EV-009) y descripción de la suite.
- **CI**: `fia verify --strict-receipts` en el workflow generado (`scaffold.py`) y
  en el job de gobernanza del repo (`.github/workflows/tests.yml`).
- **Docs**: `docs/RECEIPT_ROUTER.md` (uso y límites) + addendum v3.3 en
  `docs/ROADMAP_V3_1.md`.
- **CHANGELOG** v3.3.0 + bump de versión (`pyproject.toml`, `__init__.py`).
- **Demo** (`fia-harness-demo`): CI con `--strict-receipts` y nota de recibos
  (fases legacy grandfathered; el caso vivo está en el repo del kit). Commit
  `4e4a8f5`.

# FASE I — TESTS

`python -m unittest discover tests` → 282/282 (incluye paridad README y anti-drift
de plantillas).

# FASE J2 — SEGURIDAD

No aplica: cambios de documentación/CI; sin secretos, credenciales ni permisos.

# FASE K — VALIDACIÓN

```bash
python -m unittest discover tests
python -m fia_harness.cli sync -d governance
python -m fia_harness.cli verify -d governance --strict-receipts
python -m fia_harness.cli receipt verify F11 -d governance
```

---

# FASE L — INFORME FINAL OBLIGATORIO

## TASK-F11 — INFORME FINAL

### 1. Resumen de lo realizado
Cierre v3.3: regla nº16 y recibo documentados en el protocolo y las plantillas,
README EN/ES alineados (recibo + router + límites), CI estricto en kit y demo,
CHANGELOG y versión 3.3.0. **Hotfix v3.3.1:** el job de gobernanza necesitaba
`fetch-depth: 0` (el checkout shallow no tiene los commits históricos de los
recibos); corregido en el workflow generado y en el del repo.

### 2. Diagnóstico o decisiones de diseño tomadas
- La duplicación de plantillas ya tenía guardián (`test_templates_match_repo_root`);
  se mantiene como fuente canónica la raíz `templates/` y se sincroniza la copia del
  paquete en cada edición (verificado por test).
- El CI pasa a `--strict-receipts`: los recibos `dirty` bloquean el merge; los
  proyectos existentes quedan cubiertos por el grandfathering (ADR-009).
- En el demo, las fases F0/F1 son legacy: no se inventan recibos; se documenta la
  limitación y el caso vivo del kit (F9/F10).

### 3. Archivos modificados (lista + explicación concreta)
- Plantillas (2 copias): `INICIO_PROYECTO.md`, `AGENTS.md`, `TASK_TEMPLATE.md`,
  `QUICKSTART_LITE.md`.
- `README.md`, `README.es.md`, `CHANGELOG_FIXES.md`, `pyproject.toml`,
  `fia_harness/__init__.py`, `fia_harness/generators/scaffold.py`,
  `.github/workflows/tests.yml`.
- `docs/RECEIPT_ROUTER.md` (nuevo), `docs/ROADMAP_V3_1.md`, `docs/*` (registro).
- Demo: `.github/workflows/harness.yml`, `README.md` (commit `4e4a8f5`).

### 4. Máquina de estados (si aplica)
No aplica.

### 5. Protección contra duplicados/errores implementada
Paridad README EN/ES (test existente), anti-drift de plantillas (test existente),
version bump coherente en paquete y pyproject.

### 6. Compatibilidad verificada (entornos/plataformas)
Proyectos existentes: grandfathering de recibos y flags legacy intactos; plantillas
nuevas solo aplican a proyectos nuevos (los existentes pueden re-sellar si las
actualizan). CI multiplataforma sin cambios.

### 7. Visibilidad SEO/AEO/GEO — No aplica (kit sin superficie pública).

### 8. Tests
`282/282 passed` (suite completa, Windows / Python 3.11; evidencia EV-011).

### 9. Typecheck
N/A (stdlib-only; sin typecheck configurado).

### 10. Lint
N/A (sin linter configurado en el kit).

### 11. Build
N/A (paquete stdlib-only; sin build propio).

### 12. Seguridad (Fase J2): sin API keys, tokens, credenciales ni datos privados;
sin dependencias nuevas; sin cambios de permisos.

### 13. Archivos NO modificados
`core/receipts.py`, `core/router.py` y el resto del núcleo (F9/F10 cerradas);
materiales de `lanzamiento/` (posts históricos de v3.0, revisados sin cambios).

### 14. Git: `Commit: SÍ` (autorizado) · `Push: NO` · `Deploy: NO`

### 15. Prueba manual recomendada
`fia verify -d governance --strict-receipts` debe quedar PASS con
`2 limpio(s) · 0 local(dirty)` tras re-emitir F11.

### 16. Resultado final:
```text
TAREA COMPLETADA
```

### 17. Próximo paso sugerido
Release v3.3.0 (tag/PyPI) y reanudar la puerta F8 (validación externa).

### 18. Skills/MCP y aprobación humana
No aplica (sin capacidades externas). Recorte amparado por `APPROVAL-003`.

### 19. UI/UX diferencial — No aplica.

### 20. Contexto y prompt injection — No aplica.
