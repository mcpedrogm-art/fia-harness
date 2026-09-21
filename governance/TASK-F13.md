# TASK-F13 — Pack de assets UI (v3.5.0)

## Tipo de tarea
- [x] Construcción de funcionalidad nueva (fase del plan de ejecución)
- [ ] Diagnóstico / corrección de bug
- [ ] Auditoría / refactor
- [ ] Optimización de visibilidad (SEO / AEO / GEO)
- [x] Diseño UI/UX diferencial
- [ ] Seguridad / hardening (auth, RLS, servidor, secretos)
- [ ] Otro: <especificar>

## Contexto y rol

Actúa como responsable de distribución del proyecto **FIA Harness**.

Estado actual del trabajo (resumen desde `PROGRESS.md`):
- F0–F12 cerradas (v3.4.4 publicada; F8 en pausa).
- F13 en curso: pack de assets UI para que los usuarios descarguen e integren
  assets en su proyecto sin que el kit distribuya contenido de terceros.
- Amparada por `APPROVAL-005` y el ADR-012.

Reglas de commit/push/deploy: commit y push autorizados por el humano en esta
sesión; deploy del pack pendiente de acceso al VPS.

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

**Objetivo (desde PROGRESS.md):** pack de assets UI con manifiesto y descarga
verificada (`fia assets fetch/manifest`, `fia init --assets`).
**Dependencias:** F12.

El kit (MIT) lleva el **mecanismo**; el **contenido** lo aloja quien tenga derechos
(p. ej. Supabase self-hosted del mantenedor). Nada se descarga por defecto.

---

# FASE A — AUDITORÍA

Revisados: estructura de plantillas y anti-drift, CLI (`init`, subparsers), E2E
manual y el flujo de UI/UX (§8.1, campo 10 "assets"). Decisión de diseño: manifiesto
JSON con `path`/`url`/`sha256`, descarga stdlib, verificación fail-closed.

# FASE E — IMPLEMENTACIÓN

- `core/assets.py`: `load_manifest` (URL http/https/file o ruta), `fetch_manifest`
  (idempotente, `.part` → `os.replace`, hash SHA-256, sin traversal), `build_manifest`
  (genera el manifiesto al publicar).
- CLI: `fia assets fetch [URL|manifiesto]`, `fia assets manifest --dir-source
  --base-url`, `fia init --assets <url>`.
- Plantilla `UI_ASSETS.json` (raíz + paquete + `bootstrap`), `docs/UI_ASSETS.md`,
  nota en `UI_UX_EXCLUSIVA.md` §8.1, README EN/ES («What v3.5 adds», comandos y
  lista de plantillas).

# FASE I — TESTS

`tests/test_core_assets.py` (8 casos: manifiesto con hashes/URLs, fetch file://
idempotente, hash incorrecto sin restos, traversal, manifiesto inexistente, versión
no soportada, CLI y `init --assets`) + paso 8 en el E2E manual.

# FASE J2 — SEGURIDAD

Aplicado en el diseño: rutas relativas sin traversal, verificación SHA-256
fail-closed, escritura atómica, sin ejecución de contenido descargado, opt-in y sin
llamadas por defecto. Limitación documentada: el manifiesto no está firmado (v1);
el pack debe vivir en infraestructura propia sobre HTTPS.

# FASE K — VALIDACIÓN

```bash
python -m unittest discover tests
python tests/e2e_manual.py
python -m fia_harness.cli verify -d governance --strict-receipts
```

---

# FASE L — INFORME FINAL OBLIGATORIO

## TASK-F13 — INFORME FINAL

### 1. Resumen de lo realizado
Los usuarios pueden descargar e integrar un pack de assets UI con un comando
(`fia assets fetch` o `fia init --assets <url>`), con verificación SHA-256 e
idempotencia; el mantenedor genera el manifiesto con `fia assets manifest`.

### 2. Diagnóstico o decisiones de diseño tomadas
- El kit no empaqueta media de terceros (tamaño + licencia): mecanismo público,
  contenido en infraestructura del mantenedor (Supabase self-hosted previsto).
- Manifiesto v1 sin firma (documentado); `file://` solo para pruebas.
- Rutas seguras: el manifiesto no puede escribir fuera del proyecto.

### 3. Archivos modificados (lista + explicación concreta)
- `fia_harness/core/assets.py` (nuevo): lógica completa.
- `fia_harness/cli.py`: subcomando `assets` y `init --assets`; plantilla nueva.
- `fia_harness/generators/bootstrap.py`: copia `UI_ASSETS.json` a la raíz.
- `templates/UI_ASSETS.json` + copia del paquete; `templates/UI_UX_EXCLUSIVA.md`.
- `tests/test_core_assets.py` (nuevo), listas de plantillas en tests, E2E paso 8.
- `docs/UI_ASSETS.md` (nuevo), `README.md`, `README.es.md`, `CHANGELOG_FIXES.md`,
  `pyproject.toml`, `fia_harness/__init__.py`, `governance/*`.

### 4. Máquina de estados (si aplica)
No aplica.

### 5. Protección contra duplicados/errores implementada
Idempotencia por hash (si coincide, no descarga); `.part` + `os.replace` (sin
archivos a medias); fail-closed ante hash incorrecto; manifiesto validado
(versión, entradas, sha256 de 64 hex).

### 6. Compatibilidad verificada (entornos/plataformas)
stdlib-only (Windows/Linux/macOS); sin cambios en flujos existentes; plantilla
nueva con anti-drift en verde; `fia init` sin `--assets` idéntico a antes.

### 7. Visibilidad SEO/AEO/GEO — No aplica (kit sin superficie pública).

### 8. Tests
`299/299 passed` (suite completa, Windows / Python 3.11; evidencia EV-020) +
E2E completo con pack (EV-021).

### 9. Typecheck
N/A (stdlib-only; sin typecheck configurado).

### 10. Lint
N/A (sin linter configurado en el kit).

### 11. Build
N/A (paquete stdlib-only; sin build propio).

### 12. Seguridad (Fase J2): sin secretos ni credenciales en el código; descarga
opt-in con verificación SHA-256; sin traversal; sin ejecución de lo descargado.

### 13. Archivos NO modificados
`core/receipts.py`, `core/router.py`, `core/verify.py` y el resto del núcleo.

### 14. Git: `Commit: SÍ` · `Push: SÍ (autorizado)` · `Deploy: NO` (pack pendiente)

### 15. Prueba manual recomendada
`fia assets manifest --dir-source <pack> --base-url <url>` y luego
`fia assets fetch <manifiesto>` en un proyecto: archivos descargados, segundo run
idempotente, hash manipulado → bloqueo.

### 16. Resultado final:
```text
TAREA COMPLETADA
```

### 17. Próximo paso sugerido
Publicar el pack en el Supabase self-hosted (bucket + manifiesto) y validar
`fia init --assets <URL real>`; después, retomar F8.

### 18. Skills/MCP y aprobación humana
No aplica (sin capacidades externas). `APPROVAL-005` y ADR-012 amparan el cambio.
El hosting del pack usará el playbook `vps-stack-security` cuando se ejecute.

### 19. UI/UX diferencial — Aplica al flujo de assets (§8.1, campo 10).

### 20. Contexto y prompt injection — No aplica.
