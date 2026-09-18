# TASK-F12 — UI/UX: cuatro direcciones divergentes + recetas (v3.4)

## Tipo de tarea
- [x] Construcción de funcionalidad nueva (fase del plan de ejecución)
- [ ] Diagnóstico / corrección de bug
- [ ] Auditoría / refactor
- [ ] Optimización de visibilidad (SEO / AEO / GEO)
- [x] Diseño UI/UX diferencial
- [ ] Seguridad / hardening (auth, RLS, servidor, secretos)
- [ ] Otro: <especificar>

## Contexto y rol

Actúa como responsable del sistema UI/UX del proyecto **FIA Harness**.

Estado actual del trabajo (resumen desde `PROGRESS.md`):
- F0–F11 cerradas (v3.3 publicada en PyPI; F8 en pausa).
- F12 en curso: corregir la convergencia de variantes en la fase H3 e integrar
  recetas de sección. Amparada por `APPROVAL-004` y el ADR-011.

Reglas de commit/push/deploy: commit y push autorizados por el humano en esta
sesión; deploy no aplica.

## ALCANCE PERMITIDO (scope)

- templates/**
- fia_harness/**
- tests/**
- docs/**
- governance/**
- README.md
- README.es.md
- .gitignore

---

# OBJETIVO DE LA TAREA

**Objetivo (desde PROGRESS.md):** UI/UX: cuatro direcciones divergentes + esquema de
recetas + `UI_RECIPES.md`.
**Dependencias:** F11.

**Problema observado (humano):** en pruebas reales, la selección de direcciones
acababa en dos variantes parecidas. **Decisión:** forzar 4 direcciones con roles
fijos y una matriz de divergencia verificable, y dar material concreto (recetas)
para que la diferencia no dependa de la "creatividad" del modelo.

---

# FASE A — AUDITORÍA

Revisados: `UI_UX_EXCLUSIVA.md` (prompt maestro pedía "tres direcciones" sin
mecanismo anti-convergencia), H3 de `TASK_TEMPLATE.md`, `QUICKSTART_LITE.md`,
inyección (`build_ui_ux_block`) y listas de plantillas (`cli`, `bootstrap`,
`discovery`, tests). Aportadas por el humano 12 recetas de referencia (PDF, 22
páginas) con patrones concretos: composición exacta, técnica de fondo (shader
WebGL2, Three.js, vídeo, tipográfico), fuentes, motion, assets y responsive.

# FASE E — IMPLEMENTACIÓN

- `UI_UX_EXCLUSIVA.md`: §3 (divergencia obligatoria), §8 (prompt: 4 direcciones con
  roles, matriz, autochequeo), **§8.1 recetas de sección (12 campos)** y **§8.2
  matriz de divergencia (6 ejes)**, §10 (criterio de divergencia) y §12
  (entregable `UI_RECIPES.md`).
- Plantilla nueva `UI_RECIPES.md` (direcciones, matriz, recetas, decisión) con
  copia en el paquete, `fia init`, `bootstrap` y `NON_PRD_FILES`.
- H3 de `TASK_TEMPLATE.md` y `QUICKSTART_LITE.md` (2 direcciones divergentes en Lite).
- README EN/ES: plantilla nueva listada.
- **Biblioteca privada** `UI_LIBRARY.local.md` (gitignored): 12 recetas aportadas
  por el humano desde su cuenta de Dínamo Sites; el kit público (MIT) no incluye
  prompts ni assets de terceros, solo el esquema y el flujo.

# FASE I — TESTS

`python -m unittest discover tests` → 282/282 (anti-drift de plantillas y
`init` e2e incluyen la plantilla nueva).

# FASE J2 — SEGURIDAD

No aplica: sin secretos ni permisos. La biblioteca privada queda fuera de git por
licencia (no por secreto).

# FASE K — VALIDACIÓN

```bash
python -m unittest discover tests
python -m fia_harness.cli sync -d governance
python -m fia_harness.cli verify -d governance --strict-receipts
```

---

# FASE L — INFORME FINAL OBLIGATORIO

## TASK-F12 — INFORME FINAL

### 1. Resumen de lo realizado
La fase H3 ya no puede presentar "tres direcciones" abstractas: entrega cuatro
direcciones con roles fijos, cada una desde una receta distinta, validadas con una
matriz de divergencia antes de mostrarse. Plantilla `UI_RECIPES.md` para registrar
recetas, matriz y decisión; biblioteca privada local con el material de referencia.

### 2. Diagnóstico o decisiones de diseño tomadas
- La convergencia no se arregla pidiendo "más creatividad": se arregla forzando el
  eje que más diferencia (técnica de fondo/medio) y un chequeo pairwise explícito.
- El kit público no puede embeber prompts/assets de terceros (MIT vs licencia de la
  biblioteca de referencia): esquema y flujo sí; material concreto, privado.
- Diferido a v3.5: gate mecánico de UI (decisión humana registrada), mismo patrón
  que el gate de riesgo v3.1 (ADR-011).

### 3. Archivos modificados (lista + explicación concreta)
- `templates/UI_UX_EXCLUSIVA.md` (+ copia del paquete): §3, §8, §8.1–8.2, §10, §12.
- `templates/UI_RECIPES.md` (nuevo) + copia del paquete.
- `templates/TASK_TEMPLATE.md`, `templates/QUICKSTART_LITE.md` (+ copias).
- `fia_harness/cli.py`, `fia_harness/generators/bootstrap.py`,
  `fia_harness/parser/discovery.py` (plantilla nueva en init/bootstrap/PRD).
- `tests/test_packaging.py`, `tests/test_harness.py`, `tests/test_parser_prd.py`.
- `README.md`, `README.es.md`, `.gitignore`, `UI_LIBRARY.local.md` (privada).
- `governance/*` (SPEC §8, ADR-011, APPROVAL-004, PROGRESS, TASK).

### 4. Máquina de estados (si aplica)
No aplica.

### 5. Protección contra duplicados/errores implementada
Anti-drift de plantillas (test) cubre la plantilla nueva en las dos copias;
`NON_PRD_FILES` evita que `UI_RECIPES.md` se confunda con un PRD.

### 6. Compatibilidad verificada (entornos/plataformas)
Proyectos existentes: no cambia el estado ni el CI; las plantillas nuevas aplican a
proyectos nuevos o al actualizarlas. `fia init`/`bootstrap` copian la plantilla
nueva sin pisar nada. Suite multiplataforma en verde.

### 7. Visibilidad SEO/AEO/GEO — No aplica (kit sin superficie pública).

### 8. Tests
`282/282 passed` (suite completa, Windows / Python 3.11; evidencia EV-012).

### 9. Typecheck
N/A (stdlib-only; sin typecheck configurado).

### 10. Lint
N/A (sin linter configurado en el kit).

### 11. Build
N/A (paquete stdlib-only; sin build propio).

### 12. Seguridad (Fase J2): sin API keys, tokens, credenciales ni datos privados;
sin dependencias nuevas. La biblioteca privada no se commitea (`*.local.md`).

### 13. Archivos NO modificados
`core/*` (sin cambios de comportamiento), inyección H3 (`build_ui_ux_block` se
mantiene: extrae Gate de entrada y Reglas de exclusividad, que siguen existiendo).

### 14. Git: `Commit: SÍ` · `Push: SÍ (autorizado)` · `Deploy: NO`

### 15. Prueba manual recomendada
`fia init` en carpeta temporal y comprobar que `docs/UI_RECIPES.md` existe; abrir
`UI_UX_EXCLUSIVA.md` §8.2 y verificar que el prompt exige la matriz antes de mostrar
las direcciones.

### 16. Resultado final:
```text
TAREA COMPLETADA
```

### 17. Próximo paso sugerido
Probar el flujo de 4 direcciones en un proyecto real (o reanudar F8). v3.5
candidato: gate mecánico de UI (ADR-011).

### 18. Skills/MCP y aprobación humana
No aplica (sin capacidades externas). `APPROVAL-004` ampara el cambio; ADR-011 lo
registra.

### 19. UI/UX diferencial — Esta tarea **es** la unidad UI/UX; aplica §8.1–8.2.

### 20. Contexto y prompt injection — No aplica.
