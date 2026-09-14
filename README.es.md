# 🧬 FIA HARNESS

> **Los agentes de IA no fallan escribiendo código — fallan por desviarse.**
> FIA Harness convierte "especificación, disciplina y cero resultados inventados"
> de buenas intenciones en **checks de merge que ningún agente puede saltarse**.
> Local, cero dependencias, LLM-agnóstico.

[![CI](https://github.com/mcpedrogm-art/fia-harness/actions/workflows/tests.yml/badge.svg)](https://github.com/mcpedrogm-art/fia-harness/actions/workflows/tests.yml)
[![PyPI](https://badgen.net/pypi/v/fia-harness)](https://pypi.org/project/fia-harness/)
[![Python 3.8+](https://badgen.net/badge/python/3.8%2B/blue)](#)
[![License: MIT](https://badgen.net/badge/license/MIT/blue)](LICENSE)

`Python 3.8+` · `Sin dependencias externas` · `Mono o multi-agente` · `2 modos de trabajo` · `Reglas verificadas en CI` · `LLM-agnóstico` *(Claude, DeepSeek, GPT, OpenCode — el agente que uses)*

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

Monta un proyecto nuevo al instante: las plantillas del kit en `/docs`, los dos
scripts en la raíz y un `PRD.md` de partida. Luego `python bootstrap.py` y estás
sobre raíles. ¿Prefieres clonar? Este repo es una **plantilla de GitHub** — pulsa
*Use this template*.

---

## 🎬 Mira cómo el interlock atrapa al agente (60 segundos)

Las reglas aquí no son consejo — son **checks de merge** que ningún agente puede
saltarse. El repo [`fia-harness-demo`](https://github.com/mcpedrogm-art/fia-harness-demo)
es un proyecto pequeño y real cuyo CI bloquea a un agente tramposo que intenta
cerrar una fase sin su archivo de tarea o checkpoint:

```bash
git clone https://github.com/mcpedrogm-art/fia-harness-demo.git && cd fia-harness-demo
python task_generator.py --check     # ✅ verde
copy PROGRESS.F2_tampered.md PROGRESS.md
python task_generator.py --check     # ❌ exit 1 — el merge queda bloqueado
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

`task_generator.py` **detecta automáticamente la primera fase pendiente** y genera
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
   python task_generator.py --sync   → valida el estado en progress.json
   python task_generator.py          → genera la tarea de la fase pendiente
```

> 📖 Guía detallada paso a paso: **[INSTRUCCIONES DE APLICACION.txt](INSTRUCCIONES%20DE%20APLICACION.txt)** · Protocolo completo: **[INICIO_PROYECTO.md](INICIO_PROYECTO.md)**

---

## 📁 Mapa de archivos

| Archivo | Qué es |
|---|---|
| 🧭 `INICIO_PROYECTO.md` | **Fuente de verdad del protocolo**: rol del agente, fases, entrevista, reglas de oro |
| ⚙️ `bootstrap.py` | Inicializador (M0): lee el PRD, genera los archivos de control, sella las normas y emite el CI de reglas de oro |
| 🤖 `task_generator.py` | Genera `TASK-Fx.md`, compila/valida el estado (`--sync`, `--check`), sella docs (`--seal`), registra aprobaciones (`--approval`) y reabre fases (`--reopen`) |
| 📦 `fia_harness/` + `pyproject.toml` | Paquete PyPI: `fia-harness init` (CLI instalador). Las copias del paquete están vigiladas por tests de sincronización |
| 🗃️ `progress.json` | Estado compilado y validado: la máquina de verdad que lee el CI |
| 📋 `TASK_TEMPLATE.md` | Plantilla maestra de tarea (ciclo completo A–L, 20 puntos de informe) |
| ⚡ `TASK_LITE_TEMPLATE.md` | Plantilla de tarea rápida para el Modo Lite |
| 📄 `PRD_TEMPLATE.md` | PRD de partida para la ruta de clonado (con los encabezados que `bootstrap.py` parsea) |
| 🛡️ `SECURITY.md` | Checklist de seguridad **obligatorio en todo proyecto**: auth/2FA, RLS, secretos, firewall, Skills/MCP, prompt injection |
| 🔎 `AEO_GEO_SEO.md` | Visibilidad en SEO (buscadores), AEO (asistentes) y GEO (LLMs) — solo si hay superficie pública |
| 🎨 `UI_UX_EXCLUSIVA.md` | Design DNA, arquetipos, motion system y auditoría anti-clon |
| 🔌 `SKILLS_MCP.md` | Gobernanza de capacidades: nada se busca/instala/conecta sin **aprobación humana explícita** |
| ⚡ `QUICKSTART_LITE.md` | Protocolo reducido para prototipos, con promoción obligatoria si aparece riesgo |
| 🧩 `PROYECTOS RAG Y VECTORIALES/` | Módulo de extensión: stack vectorial, chunking, recuperación híbrida + reranking, `llms.txt` |
| 🧪 `tests/` | Tests automatizados de los parsers, la máquina de estado, el empaquetado y el ciclo completo |
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

Desde la v2, el harness obliga por **infraestructura**, no solo por convención.
`bootstrap.py` emite un workflow de GitHub Actions que se ejecuta en cada push y PR:

| Regla de oro | Cómo se hace cumplir mecánicamente |
|---|---|
| Nunca cerrar fases con dependencias abiertas (nº4) | `progress.json` validado: cerrar F2 con F1 abierta **rompe el build** |
| Nunca cerrar una fase sin Definition of Done (nº5) | Toda fase `done` exige su checkpoint de contexto en `PROGRESS.md` |
| Nunca cerrar una fase sin evidencia real (nº7) | Toda fase F `done` exige un bloque de salida cruda o `Evidencia: <archivo>` |
| Nunca ejecutar una fase sin su `TASK-Fx.md` (nº7) | El validador exige `TASK-F<N>.md` para cada fase F cerrada |
| Nunca reescribir las reglas (nº2) | Los documentos normativos están **sellados** (SHA-256); editarlos pone el CI en rojo hasta `--seal` |
| Nunca derivar la spec sin aprobación (nº6) | `SPEC.md` queda snapshotteado; cambiarla sin `--approval` pone el CI en rojo |
| Nunca hacer commit con secretos (nº8) | **gitleaks** escanea todo el historial en cada push |
| Dependencias sin vulnerabilidades conocidas | `npm audit` / `pip-audit` según el stack detectado |
| Tests obligatorios antes de dar una fase por cerrada | Job de CI con pytest/unittest o `npm test`, según lo que detecte |
| Aprobaciones humanas rastreables | Toda `APPROVAL-NNN` citada en una TASK debe existir en `DECISIONS.md` |

El flujo de estado: `PROGRESS.md` es la superficie de edición (humano o agente);
`task_generator.py --sync` lo compila y valida en `progress.json`. Si editas el
Markdown a mano y no compilas, el CI se pone rojo hasta que hagas `--sync`. Y
`--sync` es *fail-closed*: si el estado viola una regla, **no escribe nada**.

```bash
python task_generator.py --sync      # compila y valida PROGRESS.md -> progress.json
python task_generator.py --check     # valida sin modificar (lo ejecuta el CI)
python task_generator.py --seal      # sella los documentos normativos (SHA-256)
python task_generator.py --approval "instalar Skill X v1.2" --phase F2 --ref "chat 5-sep"
python task_generator.py --reopen F3 --reason "regresión detectada en auth"
```

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

> 🚨 Desde la v2, las reglas 4, 5, 7 y 8 además se **verifican automáticamente en CI** en cada proyecto que arranca con `bootstrap.py` (sección anterior).

---

## ⚠️ Limitaciones — lo que el CI no puede garantizar

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
- **La evidencia se declara, no se reproduce.** El CI comprueba que el bloque de
  salida cruda *existe y no está vacío*; no puede verificar que sea genuino.
- **Modelo de confianza local.** No hay nube, ni telemetría, ni autoridad remota —
  es el precio de no enviar tu código a ningún sitio.

Estos límites son la frontera honesta de un kit que corre en *tu* máquina con
*tus* reglas. Para un dev en solitario + agente construyendo MVPs, es el equilibrio
correcto.

---

## 🐕 Dogfooding

Este repositorio se gobierna con el kit que distribuye:

- El badge de arriba es el CI de este propio repo: **73 tests** más un job de
  **auto-aplicación** que ejecuta `fia-harness init` → `bootstrap.py` → `--check`
  sobre un proyecto temporal nuevo en cada push.
- El repo [`fia-harness-demo`](https://github.com/mcpedrogm-art/fia-harness-demo)
  se genera con el kit y su CI de reglas de oro atrapa al agente tramposo en vivo.

---

## ✅ Verificar el kit

```bash
python -m unittest discover tests -v
```

Los tests cubren el parser de `PROGRESS.md`, la extracción de secciones, los
inyectores por marcadores, la heurística de palabras clave, el recorte de plantilla,
la detección de Modo Lite, la **máquina de estado** (dependencias, checkpoints,
evidencia, aprobaciones, sellos, snapshot de spec, drift, fail-closed, reapertura),
el **empaquetado** (copias anti-drift, `init` e2e, consolas cp1252) y un **ciclo
completo e2e** en carpeta temporal.

En un proyecto ya arrancado, puedes comprobar su estado en cualquier momento:

```bash
python task_generator.py --check
```

---

## 📜 Documentación y fuentes de verdad

| Documento | Rol |
|---|---|
| `README.md` *(este archivo)* | Índice y visión general del sistema (inglés) |
| `README.es.md` | La misma visión general en español |
| `INICIO_PROYECTO.md` | **Fuente de verdad del protocolo** — si algo diverge, manda este |
| `AGENTS.md` | Gobernanza nativa del agente: arranque, entrevista 3×3, guardarraíl de aprobación, enmienda de PRD |
| `INSTRUCCIONES DE APLICACION.txt` | Guía rápida de arranque paso a paso |
| `guia-automatizacion-tareas.md` | Guía del generador de tareas |
| `PROTOCOLO DE GESTION....txt` | Síntesis ejecutiva (lectura rápida) |
| `Guia_arranque_del_proyecto.pdf` | Snapshot estático de la guía para lectura cómoda |
| `CHANGELOG_FIXES.md` | Qué se corrigió, por qué y cómo se verificó |

---

## 📄 Licencia

MIT — ver [LICENSE](LICENSE). El kit es tuyo: local, auditable, sin nube, sin
telemetría, sin cuentas.
