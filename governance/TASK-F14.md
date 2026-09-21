# TASK-F14 — Entorno UI/UX asistido (v3.6.0)

## Tipo de tarea
- [x] Construcción de funcionalidad nueva (fase del plan de ejecución)
- [ ] Diagnóstico / corrección de bug
- [ ] Auditoría / refactor
- [ ] Optimización de visibilidad (SEO / AEO / GEO)
- [x] Diseño UI/UX diferencial
- [ ] Seguridad / hardening (auth, RLS, servidor, secretos)
- [ ] Otro: <especificar>

## Contexto y rol

Actúa como responsable de DX/UI del proyecto **FIA Harness**.

Estado actual del trabajo (resumen desde `PROGRESS.md`):
- F0–F13 cerradas (v3.5.1 publicada; pack oficial vivo en Supabase; F8 en pausa).
- F14 en curso: que el momento UI/UX del protocolo ofrezca instalar el entorno
  avanzado con una confirmación humana y descarga mecánica.
- Amparada por `APPROVAL-006` y el ADR-013.

Reglas de commit/push/deploy: commit y push autorizados por el humano; deploy no
aplica (el pack ya está publicado).

## ALCANCE PERMITIDO (scope)

- fia_harness/**
- tests/**
- docs/**
- templates/**
- governance/**
- README.md
- README.es.md
- CHANGELOG_FIXES.md
- pyproject.toml

---

# OBJETIVO DE LA TAREA

**Objetivo (desde PROGRESS.md):** entorno UI/UX asistido: `fia ui setup/status` +
pregunta en el protocolo (Full y Lite).
**Dependencias:** F13.

---

# FASE A — AUDITORÍA

Revisados: `core/assets.py` (descarga verificada reutilizable), CLI y subparsers,
`UI_UX_EXCLUSIVA.md` §8, H3 de `TASK_TEMPLATE.md`, `QUICKSTART_LITE.md`, `AGENTS.md`
y README EN/ES. Decisiones del humano: dos niveles (completo / `--recetas`), sin
registro de la decisión, también en Lite, `fia ui setup` como nombre.

# FASE E — IMPLEMENTACIÓN

- `core/ui.py`: `UI_PACK_URL` (oficial), `pack_url()` (`--url` > `FIA_UI_PACK_URL` >
  constante), `cmd_ui_setup` (guarda el manifiesto en el `UI_ASSETS.json` del
  proyecto y delega en la descarga verificada) y `cmd_ui_status` (sin red).
- `core/assets.py`: `fetch_manifest(..., only_prefix=)` y `check_manifest(...)`.
- CLI: subcomando `ui` (`setup [--recetas] [--url]`, `status`).
- Protocolo: Paso 0 en `UI_UX_EXCLUSIVA.md` §8, ítem en H3, mención en
  `QUICKSTART_LITE.md` y `AGENTS.md` (copias raíz + paquete sincronizadas).
- README EN/ES («What v3.6 adds», comandos) y `docs/UI_ASSETS.md`.

# FASE I — TESTS

`tests/test_core_ui.py` (8 casos: setup completo con manifiesto guardado,
`--recetas`, status ausente/completo/parcial/modificado, override por env,
constante oficial, CLI) + paso 9 del E2E. Suite: 299 → 307.

# FASE J2 — SEGURIDAD

Sin secretos en el código; descarga opt-in con SHA-256 y rutas seguras (reutiliza
`assets`); `status` sin red. La URL oficial es pública y configurable.

# FASE K — VALIDACIÓN

```bash
python -m unittest discover tests
python tests/e2e_manual.py
python -m fia_harness.cli verify -d governance --strict-receipts
```

---

# FASE L — INFORME FINAL OBLIGATORIO

## TASK-F14 — INFORME FINAL

### 1. Resumen de lo realizado
El momento UI/UX ya ofrece instalar el entorno avanzado: el agente pregunta, el
humano decide y `fia ui setup` descarga y verifica (completo o solo recetas);
`fia ui status` informa sin red. **v3.6.1:** fix de empaquetado detectado por el
humano en uso real (`UI_ASSETS.json` quedaba fuera del wheel por el glob `*.md` y
`fia init` fallaba en instalaciones de PyPI) + guardarraíles (test de cobertura de
`package-data`, job `wheel` en CI y humo en el release) y mensaje de error afinado.

### 2. Diagnóstico o decisiones de diseño tomadas
- La decisión es humana (protocolo) y la ejecución mecánica (CLI): encaja con el
  principio del kit y con el opt-in estricto.
- URL oficial por defecto + override: funciona sin configurar y no ata el kit.
- El manifiesto usado se guarda en el proyecto para `status` offline y re-descargas
  incrementales; sin registro adicional de la decisión (descartado por el humano).

### 3. Archivos modificados (lista + explicación concreta)
- `fia_harness/core/ui.py` (nuevo), `fia_harness/core/assets.py` (filtro y chequeo),
  `fia_harness/cli.py` (subcomando `ui` y docstring).
- Plantillas (2 copias): `UI_UX_EXCLUSIVA.md`, `TASK_TEMPLATE.md`,
  `QUICKSTART_LITE.md`, `AGENTS.md`.
- `tests/test_core_ui.py` (nuevo), `tests/e2e_manual.py` (paso 9).
- `README.md`, `README.es.md`, `docs/UI_ASSETS.md`, `CHANGELOG_FIXES.md`,
  `pyproject.toml`, `fia_harness/__init__.py`, `governance/*`.

### 4. Máquina de estados (si aplica)
No aplica.

### 5. Protección contra duplicados/errores implementada
Idempotencia y SHA-256 heredados de `assets`; `status` detecta ausentes y
modificados; el manifiesto guardado evita ambigüedad sobre lo instalado.

### 6. Compatibilidad verificada (entornos/plataformas)
stdlib-only; sin cambios en flujos existentes; `fia assets fetch` y `init --assets`
siguen igual; plantillas nuevas con anti-drift en verde.

### 7. Visibilidad SEO/AEO/GEO — No aplica (kit sin superficie pública).

### 8. Tests
`309/309 passed` (suite completa, Windows / Python 3.11; evidencia EV-025) + E2E
con `ui setup` completo, `--recetas` y `status` (EV-024) + verificación manual del
wheel (uv build → contenido con `UI_ASSETS.json` → venv limpio → `fia init` OK).

### 9. Typecheck
N/A (stdlib-only; sin typecheck configurado).

### 10. Lint
N/A (sin linter configurado en el kit).

### 11. Build
N/A (paquete stdlib-only; sin build propio).

### 12. Seguridad (Fase J2): sin secretos; descarga verificada y opt-in; status
offline; la URL oficial es pública y se puede sustituir por `--url`/env.

### 13. Archivos NO modificados
`core/receipts.py`, `core/router.py`, `core/verify.py` y el resto del núcleo.

### 14. Git: `Commit: SÍ` · `Push: SÍ (autorizado)` · `Deploy: NO` (no aplica)

### 15. Prueba manual recomendada
En un proyecto sin pack: `fia ui status` (ausente) → `fia ui setup --recetas` →
`fia ui status` (parcial/completo según lo instalado) → `fia ui setup` (completo).

### 16. Resultado final:
```text
TAREA COMPLETADA
```

### 17. Próximo paso sugerido
Retomar F8 (validación externa) o el gate mecánico de UI (v3.6+ candidato).

### 18. Skills/MCP y aprobación humana
No aplica (sin capacidades externas). `APPROVAL-006` y ADR-013 amparan el cambio.

### 19. UI/UX diferencial — Aplica: es el flujo del entorno UI/UX.

### 20. Contexto y prompt injection — No aplica.
