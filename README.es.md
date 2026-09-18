# 🧬 FIA HARNESS

> **Los agentes de IA no fallan escribiendo código — fallan por desviarse.**
> FIA Harness convierte "especificación, disciplina y cero resultados inventados"
> de buenas intenciones en **checks de merge que el agente no puede saltarse en
> silencio — dentro del trust boundary de tu Git + CI**. Local, cero dependencias,
> LLM-agnóstico.

[![CI](https://github.com/mcpedrogm-art/fia-harness/actions/workflows/tests.yml/badge.svg)](https://github.com/mcpedrogm-art/fia-harness/actions/workflows/tests.yml)
[![PyPI](https://badgen.net/pypi/v/fia-harness)](https://pypi.org/project/fia-harness/)
[![Python 3.8+](https://badgen.net/badge/python/3.8%2B/blue)](#)
[![License: MIT](https://badgen.net/badge/license/MIT/blue)](LICENSE)

`Python 3.8+` · `Sin dependencias externas` · `Mono o multi-agente` · `2 modos de trabajo` · `Reglas verificadas en CI` · `LLM-agnóstico` *(Claude, DeepSeek, GPT, OpenCode — el agente que uses)*

**En una frase:** un protocolo de ingeniería local-first para trabajar con agentes
sin entregarles el control — *un freno de mano, no un piloto automático de
calidad.* No escribe código por ti ni juzga lo bueno que es: hace **verificable el
estado** del proyecto y mantiene al humano decidiendo qué se mergea.

**📖 English:** [README.md](README.md)

---

## ⚡ Qué problema resuelve

Un agente con spec *y* conciencia igual se desvía: cierra una fase que nunca
terminó, relaja sus propias reglas o escribe un informe lleno de tests que jamás
corrieron. Los prompts y los flujos de "confía en mí" no pueden evitarlo.

FIA Harness convierte el **estado del proyecto en un dato validado por máquina** y
se niega a que el agente se auto-certifique en silencio:

| | Prompts sueltos | SaaS cerrado | **FIA Harness** |
|---|---|---|---|
| Dónde corre | tu chat | la nube de otro | **tu máquina** |
| Spec antes que código | lo esperas | opinión del vendor | **se impone** |
| Las reglas tienen dientes | ❌ | parcialmente | **✅ checks de merge** |
| Tus secretos salen del repo | ❌ | quizá | **nunca** |
| Coste | por token | suscripción | **gratis, local** |

El histórico nunca se reenvía completo: cada fase carga solo unos pocos archivos de
control comprimidos. Contexto pequeño = respuestas más baratas, más rápidas y con
menos deriva.

---

## ⚡ Instalación en un comando

```bash
uvx fia-harness init        # o: pipx run fia-harness init
```

Monta un proyecto nuevo al instante: las plantillas del kit en `/docs`, fachadas
finas en la raíz (`bootstrap.py`, `task_generator.py`) y un `PRD.md` de partida.
Luego `python bootstrap.py` y estás sobre raíles. ¿Prefieres clonar? Este repo es
una **plantilla de GitHub** — pulsa *Use this template*.

---

## 🎬 Mira cómo el interlock atrapa al agente (60 segundos)

Las reglas aquí no son consejo — son **checks de merge** que ningún agente puede
saltarse. El repo [`fia-harness-demo`](https://github.com/mcpedrogm-art/fia-harness-demo)
es un proyecto pequeño y real cuyo CI bloquea a un agente tramposo que intenta
cerrar una fase sin su archivo de tarea, sin su checkpoint o sin evidencia
verificable:

```bash
git clone https://github.com/mcpedrogm-art/fia-harness-demo.git && cd fia-harness-demo
pip install fia-harness
fia verify                               # ✅ PASS — merge elegible
cp PROGRESS.F2_tampered.md PROGRESS.md   # Windows: copy ...
fia verify                               # ❌ exit 1 — el merge queda bloqueado
```

---

## 🧭 El modelo mental (3 pasos)

```text
1. PENSAR  — PRD → entrevista (M1) → SPEC.md aprobado por un humano (M2). Aún sin código.
2. PLANEAR — la spec se trocea en fases pequeñas verificables F0…Fn (M3).
3. CONSTRUIR — una fase = una tarea = un ciclo cerrado: auditar → diseñar → codificar → verificar.
```

Cada transición deja un **artefacto validado**: `PROGRESS.md` es la superficie de
edición y `progress.json` la verdad compilada que lee el CI. Editar el Markdown sin
recompilar pone el CI en rojo.

---

## ⚙️ Cómo funciona: tres motores

### 1️⃣ Fases de proceso (M0–M3) — *pensar antes de construir*

| Fase | Qué pasa | Entregable |
|:---:|---|---|
| **M0** | `bootstrap.py` lee el PRD y activa el harness | `CONTEXT.md` + `PROGRESS.md` + plantillas |
| **M1** | El agente te entrevista: stack, BBDD, seguridad, visibilidad, UI/UX, Skills/MCP | `SECURITY.md` y `AEO_GEO_SEO.md` completos |
| **M2** | El agente redacta la especificación técnica (SDD) | `SPEC.md` **aprobado por un humano** |
| **M3** | El plan se trocea en fases pequeñas y verificables | Tabla `F0-Fn` pegada en `PROGRESS.md` |

> 🚫 Hasta que M3 cierra, **no se escribe una sola línea de código de producción.**

### 2️⃣ Fases de ejecución (F0–Fn) — *construir fase a fase*

Cada fase del plan = **una tarea** = un ciclo completo y cerrado. Ejemplo de plan:

| Fase | Objetivo | Entregable |
|:---:|---|---|
| F0 | Bootstrap del repo, tooling, CI | Repo funcionando |
| F1 | Modelo de datos + migraciones | BBDD versionada |
| F2 | Backend core | API mínima |
| F3 | Frontend core | UI navegable |
| F4 | Auth y permisos | Login/roles |

`fia task` **detecta automáticamente la primera fase pendiente** y genera
su tarea. Tú decides cuándo arrancar la siguiente; el agente nunca encadena fases solo.

### 3️⃣ El ciclo de tarea (A–L) — *disciplina en cada fase*

```
A. Auditoría → B. Diseño → C. Hipótesis → E. Implementación → F. Edge cases
→ I. Tests → J2. Seguridad → H2. Visibilidad → H3. UI/UX → K. Validación → L. Informe
```

Seguridad (J2), visibilidad (H2) y UI/UX (H3) **se inyectan automáticamente solo si
la fase las necesita**, con el contenido *real y vivo* de tus `SECURITY.md`,
`AEO_GEO_SEO.md` y `UI_UX_EXCLUSIVA.md`. Si no aplican, el generador lo dice
explícitamente — nunca se omite en silencio.

---

## 🚀 Arranque en 4 pasos

> ⚡ **O en un solo comando (PyPI):** `uvx fia-harness init` monta el proyecto
> nuevo automáticamente — plantillas en `/docs`, scripts en la raíz y `PRD.md` de
> partida. Salta al paso 2.

```text
1. Prepara el proyecto nuevo
   ├── pip install fia-harness  (los scripts de la raíz son fachadas finas: importan el paquete)
   ├── bootstrap.py + task_generator.py en la raíz
   ├── /docs con las plantillas maestras
   ├── (opcional) RAG_VECTOR_EXTENSION.md dentro de /docs si habrá búsqueda semántica
   └── PRD.md en la raíz

2. python bootstrap.py          → Fase M0 automática
   Genera CONTEXT.md, PROGRESS.md, progress.json, DECISIONS.md,
   activa las plantillas y emite .github/workflows/harness.yml

3. Abre tu agente con la carpeta → inicia la entrevista (M1)
   El agente lee CONTEXT.md y NO programa nada todavía.

4. Aprueba SPEC.md, pega la tabla F0-Fn en PROGRESS.md y compila:
   fia sync                  → valida el estado en progress.json (schema 3.0)
   fia task                  → genera la tarea de la fase pendiente
   fia run -- <tus tests>    → registra evidencia (EV-NNN, artifacts hasheados)
   fia receipt create F0 --tests N/N   → recibo de fase (nº16): manifiesto canónico + hash
   fia verify                → merge gate: estado + evidencia + procedencia + recibos
```

> 📖 Protocolo completo: **[templates/INICIO_PROYECTO.md](templates/INICIO_PROYECTO.md)** · Visión general en inglés: **[README.md](README.md)**

---

## 📁 Mapa de archivos

> En un **proyecto de usuario** las plantillas viven en la raíz (las copian
> `fia init` / `bootstrap.py`). En este repo viven en `templates/`, y el proyecto
> gobernado del propio repo vive en `governance/`.

| Archivo | Qué es |
|---|---|
| ⚙️ `bootstrap.py` · 🤖 `task_generator.py` | Fachadas finas en la raíz del proyecto: la implementación vive en el paquete instalado (ADR-001) |
| 📦 `fia_harness/` + `pyproject.toml` | Paquete PyPI y **única fuente de verdad**: `fia init/check/sync/task/status/approve/seal/reopen/run/evidence/receipt/route/verify` |
| 🗂️ `templates/` | Plantillas maestras del kit: protocolo (`INICIO_PROYECTO.md`), `SECURITY.md`, `AEO_GEO_SEO.md`, `UI_UX_EXCLUSIVA.md`, `UI_RECIPES.md`, `SKILLS_MCP.md`, `TASK_TEMPLATE.md`, `TASK_LITE_TEMPLATE.md`, `QUICKSTART_LITE.md`, `AGENTS.md`, `PRD_TEMPLATE.md`, `MODELOS.md` y el módulo RAG |
| 🏛️ `governance/` | Proyecto dogfood del propio repo (se opera con `-d governance`): `PROGRESS.md`, `SPEC.md`, `DECISIONS.md`, `progress.json`, `TASK-F0…F11.md`, `evidence/` (incl. recibos de fase) |
| 📖 `docs/` | Baseline v3 (`V3_BASELINE.md`), la decisión de captura de evidencia (ADR-005) y el plan/diseño v3.3 (`PLAN_RECIBO_ROUTER.md`, `RECEIPT_DESIGN.md`, `RECEIPT_ROUTER.md`) |
| 🧪 `tests/` | Tests automatizados de los parsers, la máquina de estado, evidencia, verificación, empaquetado y el ciclo completo |
| 📜 `CHANGELOG_FIXES.md` | Historial de correcciones aplicadas y cómo se verificaron |

---

## ⚡ Dos modos de trabajo

| | 🔵 **Completo** | ⚡ **Lite** |
|---|---|---|
| Para | MVPs, productos reales | Prototipos, vertical slices, cambios acotados |
| Documentación | `CONTEXT` + `SPEC` + `PROGRESS` + `DECISIONS` | Solo `QUICK_CONTEXT.md` |
| Tareas | `TASK-Fx.md` desde `TASK_TEMPLATE.md` | `TASK-QUICK.md` desde `TASK_LITE_TEMPLATE.md` |
| Seguridad, aprobación humana | ✅ Siempre | ✅ Siempre (no se negocian) |

**Promoción automática a Completo** si aparece cualquiera de estos: auth/roles,
pagos, PII/salud, migraciones críticas, escritura en servicios externos,
deploy/secretos, alcance incierto. La promoción **conserva** el trabajo ya validado.

> Para activar Lite: declara `Modo de trabajo: Lite` en `CONTEXT.md`
> (lo detecta `task_generator.py` solo) o fuerza con `--lite`.

---

## 🧩 Módulos condicionales

El harness base es común; estas capas se activan solo cuando el proyecto las necesita:

| Condición | Módulo que se activa |
|---|---|
| El PRD menciona RAG, embeddings, búsqueda semántica o memoria vectorial | `RAG_VECTOR_EXTENSION.md` — *bootstrap.py lo detecta y copia solo* |
| Hay páginas públicas indexables (landing, blog, docs) | `AEO_GEO_SEO.md` + Fase H2 en las tareas de contenido |
| Hay interfaz de usuario | `UI_UX_EXCLUSIVA.md` + Design DNA aprobado antes de implementar |
| El proyecto es multi-agente | `AGENTS.md` con roles y protocolo de handoff |

---

## 🚨 Enforcement: las reglas tienen dientes

Desde la v3, el harness obliga por **infraestructura**, no solo por convención.
`bootstrap.py` emite un workflow de GitHub Actions que ejecuta `fia verify` en cada
push y PR:

| Regla de oro | Cómo se hace cumplir mecánicamente |
|---|---|
| Nunca cerrar fases con dependencias abiertas (nº4) | `progress.json` validado: cerrar F2 con F1 abierta **rompe el build** |
| Nunca cerrar una fase sin Definition of Done (nº5) | Toda fase `done` exige su checkpoint de contexto en `PROGRESS.md` |
| Nunca cerrar una fase sin evidencia real (nº7) | Toda fase F `done` exige un bloque de salida cruda, `Evidencia: <archivo>` o `Evidencia: EV-NNN` (cadena validada) |
| Nunca inventar resultados (nº7) | La evidencia de `fia run` está **hasheada**: editar un artifact de `evidence/EV-*.txt` pone `PROVENANCE` en rojo; los digests de CI la marcan `trusted` |
| Nunca ejecutar una fase sin su `TASK-Fx.md` (nº7) | El validador exige `TASK-F<N>.md` para cada fase F cerrada |
| Nunca reescribir las reglas (nº2) | Los documentos normativos están **sellados** (SHA-256); editarlos pone el CI en rojo hasta `--seal` |
| Nunca derivar la spec sin aprobación (nº6) | `SPEC.md` queda snapshotteado; cambiarla sin `--approval` pone el CI en rojo |
| Nunca hacer commit con secretos (nº8) | **gitleaks** escanea todo el historial en cada push |
| Dependencias sin vulnerabilidades conocidas | `npm audit` / `pip-audit` según el stack detectado |
| Tests obligatorios antes de dar una fase por cerrada | Job de CI con pytest/unittest o `npm test`, según lo que detecte |
| Aprobaciones humanas rastreables | Toda `APPROVAL-NNN` citada en una TASK debe existir en `DECISIONS.md` |

El flujo de estado: `PROGRESS.md` es la superficie de edición (humano o agente);
`fia sync` lo compila y valida en `progress.json`. Si editas el Markdown a mano y
no compilas, el CI se pone rojo hasta que hagas `fia sync`. Y `fia sync` es
*fail-closed*: si el estado viola una regla, **no escribe nada**.

```bash
fia sync        # compila y valida PROGRESS.md -> progress.json
fia verify      # merge gate: estado + dependencias + evidencia + procedencia + recibos + sellos + spec
fia run -- pytest -q                 # ejecuta y registra evidencia (EV-NNN, artifacts hasheados)
fia evidence --ingest manifest.json  # ancla los digests de CI (procedencia trusted)
fia seal / fia approve / fia reopen  # sellos, aprobaciones humanas, reapertura auditada
fia receipt create F3 --tests 42/42  # recibo de fase (nº16): manifiesto canónico + hash
fia receipt verify F3                # recalcula y comprueba el recibo (siempre estricto)
fia route "fix typo en docs"         # propuesta determinista Lite/Full (fail-closed, v3.3)
fia verify --strict-receipts         # CI: los recibos dirty (sin commitear) bloquean el merge
fia verify --reproduce EV-001        # re-ejecuta evidencia allowlisted y compara la salida (opt-in)
fia verify --scope-base origin/main  # alcance post-hoc: diff vs el alcance declarado en la TASK
```

> Los flags de v2.2 (`python task_generator.py --sync/--check/--seal/--approval/--reopen`)
> siguen funcionando a través de la fachada — los proyectos y CI antiguos no se tocan.

---

## 🆕 Qué añade la v3

| | v2.2 | **v3.0** |
|---|---|---|
| Estado | `harness-state/1` | **schema 3.0**: IDs estables, timestamps, huella de deriva + hash de integridad, migración con backup `.bak` |
| Evidencia | bloque pegado o archivo (existencia) | **registros `EV-NNN`**: comando, exit code, timestamps, entorno y **artifacts hasheados** |
| Verificación | `--check` | **`fia verify`**: STATE · DEPENDENCIES · EVIDENCE · **PROVENANCE** · SEALS · SPEC SNAPSHOT |
| Procedencia | — | `local` vs **`trusted`** (digest del artifact de la plataforma CI, ADR-005) |
| Parser de PRD | regex binario | **niveles de confianza** (alta/media/ninguna) + sinónimos versionados + corpus de regresión |
| Distribución | scripts copiables | **paquete + fachadas finas** (`pip install fia-harness`) |
| Alcance | — | **post-hoc**: el diff debe caer dentro del alcance declarado en la TASK (`fia verify --scope-base`) |
| Reproducción | — | **opt-in**: `fia verify --reproduce` re-ejecuta comandos allowlisted y compara la salida |

---

## 🧾 Qué añade la v3.3

| | v3.2 | **v3.3** |
|---|---|---|
| Cierre de fase | evidencia + Definition of Done | **recibo**: manifiesto canónico (hashes de archivos + checks) atado a un commit; la manipulación posterior es detectable |
| Recibos en CI | — | `fia verify --strict-receipts`: los recibos `dirty` (sin commitear) bloquean el merge |
| Elección de carril | Lite/Full manual | **`fia route`**: propuesta determinista con razones, fail-closed (riesgo o ambigüedad → Full) |

> Límite honesto: un recibo ata **contenido**, no verdad. Prueba qué archivos y
> checks existían al cerrar y los ancla a un commit; no puede probar que los
> resultados declarados sean ciertos. En local puedes re-emitir un recibo `dirty`
> contra tu árbol de trabajo; el CI solo acepta limpios.

---

## 🧭 Qué añade la v3.4

| | v3.3 | **v3.4** |
|---|---|---|
| Direcciones UI/UX | "tres direcciones" libres | **cuatro direcciones divergentes** con roles fijos (segura, composición opuesta, interacción/movimiento, arquetipo inesperado) |
| Chequeo de divergencia | — | **esquema de receta (12 campos) + matriz de divergencia (6 ejes)**: extremo en ≥3 ejes, ningún par coincidiendo en >2, autochequeo antes de mostrar |
| Artefacto de proyecto | — | `UI_RECIPES.md` registra las recetas, la matriz y la decisión humana |

> Límite honesto: es un **método para el agente**, no un gate mecánico todavía
> (diferido a v3.5, ADR-011). Las recetas de referencia concretas viven en una
> **biblioteca privada local** (`*.local.md`, no se distribuye); el kit público lleva
> el esquema y el flujo, y los assets siempre se autohospedan.

---

## 🛡️ Las reglas que nunca se rompen

1. 🚫 **Nunca codificar sin spec aprobada** — ni una línea antes del M3.
2. 🗣️ **Nunca asumir en silencio** — toda asunción se declara y se confirma.
3. 📦 **Nunca reenviar contexto innecesario** — los archivos de control son la fuente comprimida.
4. ✅ **Nunca cerrar una fase sin su Definition of Done** — ni mezclar fases.
5. 🔐 **Nunca cerrar una fase de seguridad sin su checklist** — la seguridad no se pospone a un audit final.
6. 🙋 **Nunca instalar/buscar/conectar una Skill, MCP o librería sin aprobación humana** — el silencio no es permiso.
7. 🧪 **Nunca inventar resultados** — los tests que no se ejecutaron no existen.
8. 🛑 **Nunca hacer commit/push/deploy sin autorización explícita.**

> 🚨 Desde la v3, las reglas 4, 5, 7, 8 y 16 además se **verifican automáticamente en CI** en cada proyecto que arranca con `bootstrap.py` (sección anterior).

---

## ⚠️ Limitaciones — lo que el CI no puede garantizar

**FIA es un freno de mano, no un piloto automático de calidad.** Hace detectable y
caro el estado deshonesto; no juzga la calidad. La frontera, explícita:

| ✅ FIA garantiza | ❌ FIA no garantiza | 🙋 El humano debe |
|---|---|---|
| Una fase no puede cerrarse deshonestamente: dependencias, Definition of Done, `TASK-Fx.md` y evidencia se comprueban mecánicamente | Que el **código**, la **arquitectura** o la **SPEC** sean *buenos* | Asumir las decisiones de calidad: revisión de la spec, arquitectura, prioridades |
| La evidencia tiene **integridad** (hashes) y **procedencia** (`local` vs `trusted` con el digest de CI) | Reproducción independiente de cada resultado (opt-in, roadmap v3.2) | Revisar la evidencia que importa — las fases de riesgo exigen una decisión humana registrada (v3.1) |
| Las ediciones silenciosas de docs normativos, spec o estado son **detectables** (sellos, snapshots, hash de integridad) | Un sandbox: el agente comparte filesystem y shell | Mantener el trust boundary donde toca: **Git + CI**, no la palabra del agente |
| El merge se **bloquea** cuando el estado no es verificable | Comportamiento en runtime, rendimiento, product-market fit | Escribir qué significa "terminado"; FIA solo comprueba que lo hiciste |

El harness eleva el coste de desviarse de *trivial* a *deliberado y rastreable*,
pero **no** es una frontera a prueba de manipulación. Conoce sus bordes:

- **Confía en la máquina, no en la persona.** El agente y el validador comparten el
  mismo filesystem y shell. Un actor malicioso con acceso de escritura total podría
  re-sellar un documento o fabricar evidencia. El harness lo hace *detectable e
  incómodo*, no imposible.
- **Las aprobaciones son conversacionales, no criptográficas.** `--approval`
  congela un snapshot de `SPEC.md`, pero la entrada de aprobación en sí puede
  seguir siendo escrita por el agente. La firma por autoría git es una opción
  planificada, aún no el valor por defecto.
- **La procedencia de la evidencia es real, no mágica.** Los registros de `fia run`
  están atados a artifacts hasheados, así que *editar* evidencia es detectable; los
  bloques pegados a mano siguen siendo "solo existencia". En local la máquina es
  tuya, así que un registro fabricado puede pasar — la procedencia `trusted`
  requiere el digest de artifact de la plataforma CI (ADR-005).
- **Los recibos atan contenido, no verdad.** El recibo de fase (v3.3) hashea los
  archivos finales y los checks contra un commit, así que la manipulación posterior
  es detectable; no prueba que los checks se ejecutaran como se declara. Los recibos
  `dirty` son anclas locales hasta que commiteas y los re-emites
  (`fia verify --strict-receipts` exige los limpios).
- **Modelo de confianza local.** No hay nube, ni telemetría, ni autoridad remota —
  es el precio de no enviar tu código a ningún sitio.

Estos límites son la frontera honesta de un kit que corre en *tu* máquina con
*tus* reglas. Para un dev en solitario + agente construyendo MVPs, es el equilibrio
correcto.

---

## 🐕 Dogfooding

Este repositorio se gobierna con el kit que distribuye:

- El badge de arriba es el CI de este propio repo: **282 tests**, un job de
  **auto-aplicación** (`fia-harness init` → `bootstrap.py` → `--check` sobre un
  proyecto temporal nuevo) y un job de **gobernanza** que ejecuta
  `fia verify --strict-receipts` sobre este mismo repo — sus registros de evidencia
  (`EV-001…EV-009`) y recibos de fase (`F9`, `F10`) se revalidan en cada push.
- El repo [`fia-harness-demo`](https://github.com/mcpedrogm-art/fia-harness-demo)
  se genera con el kit y su CI de reglas de oro atrapa al agente tramposo en vivo.

---

## ✅ Verificar el kit

```bash
python -m unittest discover tests -v
```

Los tests cubren el parser de `PROGRESS.md`, el **parser de PRD con niveles de
confianza** (81% resuelto sobre un corpus de 20 PRDs), los inyectores por
marcadores, la heurística de palabras clave, la **máquina de estado 3.0**
(huellas, integridad, migración con backup, dependencias, checkpoints, evidencia,
aprobaciones, sellos, snapshot de spec, fail-closed, reapertura), el **motor de
evidencia** (artifacts hasheados, detección de manipulación, digests de CI), el
**motor de verificación** (reporte PASS/FAIL, gate de riesgo, alcance, reproducción,
recibos), el **recibo de fase** (hash canónico, determinismo, manipulación,
CRLF/BOM, grandfathering) y el **router de carril** (riesgo → Full, allowlist →
Lite, fail-closed) más el **empaquetado** (fachadas, `init` e2e, consolas cp1252) y
un **ciclo completo e2e** en carpeta temporal.

En un proyecto ya arrancado, puedes comprobar su estado en cualquier momento:

```bash
fia verify    # reporte completo — el gate del CI
fia check     # validación legacy solo del estado
```

---

## 📜 Documentación y fuentes de verdad

| Documento | Rol |
|---|---|
| `README.md` *(este archivo)* | Índice y visión general del sistema (inglés) |
| `README.es.md` | La misma visión general en español |
| `INICIO_PROYECTO.md` | **Fuente de verdad del protocolo** — si algo diverge, manda este |
| `AGENTS.md` | Gobernanza nativa del agente: arranque, entrevista 3×3, guardarraíl de aprobación, enmienda de PRD |
| `CHANGELOG_FIXES.md` | Historial de versiones: qué cambió, por qué y cómo se verificó |

---

## 📄 Licencia

MIT — ver [LICENSE](LICENSE). El kit es tuyo: local, auditable, sin nube, sin
telemetría, sin cuentas.
