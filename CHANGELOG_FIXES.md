# CHANGELOG_FIXES.md — Correcciones aplicadas al harness

Registro de qué se cambió, por qué, y cómo se verificó. Formato ADR-lite, coherente
con `DECISIONS.md` del propio sistema.

---

## 1. `task_generator.py` no leía la tabla real de `PROGRESS.md`

**Síntoma:** `extract_phase_info()` comparaba `parts[0] == phase` (p. ej. `"F1"`),
pero `bootstrap.py` genera el código de fase en negrita (`**F1**`). La comparación
nunca era verdadera, así que título/objetivo/dependencias quedaban vacíos para
**toda fase**, siempre, en silencio.

**Fix:** `parse_progress_table()` ahora detecta las columnas por su cabecera
("Fase", "Estado", "Entregable/Objetivo", "Dependencias"...) y normaliza cada celda
quitando `**`/`` ` ``/`_` antes de comparar. Ya no importa el orden de columnas ni
si el código de fase está en negrita, cursiva o código.

## 2. Ninguna de las tres inyecciones de checklist ("si aplica") se disparaba

**Síntoma:** el script comparaba cadenas literales copiadas a mano de
`TASK_TEMPLATE.md` (p. ej. `"Aplica el checklist correspondiente de AEO_GEO_SEO.md"`),
pero el original real tiene comillas invertidas (`` `AEO_GEO_SEO.md` ``). La
comparación de texto exacto fallaba por ese único carácter, y lo mismo ocurría con
el bloque de seguridad (backticks) y el de UI/UX (backticks). Las tres ramas
"sí aplica" eran código muerto.

**Fix:** se sustituyó el matching literal por marcadores explícitos en
`TASK_TEMPLATE.md`:
```
<!-- INJECT:VISIBILITY_CHECKLIST -->  ... <!-- /INJECT -->
<!-- INJECT:SECURITY_CHECKLIST -->    ... <!-- /INJECT -->
<!-- INJECT:UIUX_CHECKLIST -->        ... <!-- /INJECT -->
```
Son comentarios HTML, invisibles al leer el `.md` renderizado. El script busca el
marcador, no la prosa; un cambio de redacción futuro en la plantilla ya no puede
romper la inyección en silencio. Si el marcador no aparece, el script **avisa por
stderr** en vez de dejar el placeholder sin tocar.

## 3. Las ramas "No aplica" (regex) tampoco se disparaban

**Síntoma:** el patrón `r"Aplica  \*\*solo si\*\*  esta tarea..."` tenía doble
espacio donde el original tiene uno solo. `re.sub` no encontraba nada.

**Fix:** ya no existen esos regex frágiles: al usar marcadores, la rama "No aplica"
simplemente sustituye el bloque completo por una frase fija
(`NOT_APPLICABLE_TEXT`), sin depender de reconocer la prosa circundante.

## 4. `extract_checklist()` no podía extraer tablas

**Síntoma:** el "Gate de entrada" de `UI_UX_EXCLUSIVA.md` es una tabla Markdown,
no una lista con `[ ]`/`-`/`*`. El filtro de línea la descartaba entera →
`TASK-Fx.md` recibía un bloque "Gate de Entrada UX" vacío, sin aviso.

**Fix:** `extract_section()` captura el contenido íntegro bajo un encabezado
(tablas, notas, listas) hasta el siguiente encabezado de **igual o mayor nivel**
(antes se cortaba en cualquier `#`, incluso un subtítulo dentro de la misma
sección). Verificado: la tabla de 10 filas del Gate de entrada ya sale completa.

## 5. Fallback peligroso: fase por defecto `"F0"` en silencio

**Síntoma:** si la detección de fase pendiente fallaba (como pasaba siempre, por
el bug #1), el script devolvía `"F0"` sin avisar — riesgo real de regenerar o
pisar la tarea de bootstrap ya cerrada.

**Fix:** si no hay ninguna fase pendiente, el script lo dice explícitamente y
termina con código 0 sin generar nada. Si se pide una fase que no existe en
`PROGRESS.md`, termina con código 1 y lista las fases disponibles.

## 6. Heurística de palabras clave con falsos positivos por subcadena

**Síntoma real detectado en pruebas:** la fase "Entrevista de Descubrimiento
Técnico" se marcaba con `UI/UX: SÍ` porque `"vista"` (palabra clave de UI) es
subcadena de `"entre_VISTA_"`. Del mismo modo, `AEO_GEO_SEO.md` como nombre de
archivo activaba `visibilidad` por contener las subcadenas "aeo"/"geo"/"seo".

**Fix:** las palabras clave ahora se buscan con límite de palabra (`\b...\b`), no
como subcadena. Verificado con la fase F1: security/visibility/ui_ux dan los tres
`NO` correctamente.

## 7. `bootstrap.py`: valores por defecto del PRD asignados en silencio

**Síntoma:** si el PRD del cliente no usaba exactamente los encabezados
`Problema`/`Usuarios`/`Features`/`Out of scope`, `CONTEXT.md` se rellenaba con
texto genérico ("No especificado...") sin que nadie se enterase — contradice la
propia Regla de Oro nº2 del sistema ("nunca asumir en silencio").

**Fix:** `extract_prd_metadata()` devuelve ahora la lista de campos no resueltos;
`bootstrap.py` los imprime explícitamente por consola **y** los marca inline en el
propio `CONTEXT.md` generado (`⚠️ Sin confirmar: ...`), para que el aviso no se
pierda si nadie lee la consola.

## 8. `bootstrap.py`: el título extraído del PRD nunca se usaba

**Síntoma:** `extract_prd_metadata()` calculaba `metadata["title"]` pero
`generate_context_file()` no lo insertaba en ningún sitio del `CONTEXT.md`
generado — se perdía.

**Fix:** ahora aparece como `**Proyecto:** <título>` en la cabecera de
`CONTEXT.md`. Si tampoco hay `# Título` en el PRD, se usa el nombre de archivo en
vez de "Nuevo Proyecto" a secas, y se marca como no resuelto.

## 9. Campo "Modo de trabajo" no existía en `CONTEXT.md`, pero sí se buscaba

**Síntoma:** la v1 de `task_generator.py` ya buscaba el texto "Modo de trabajo:
Lite" dentro de `CONTEXT.md` para decidir si generar `TASK-QUICK.md`, pero
`bootstrap.py` nunca creaba ese campo — la detección automática de Lite era
inalcanzable salvo con `--lite` explícito o `QUICK_CONTEXT.md` presente.

**Fix:** se añadió el campo `**Modo de trabajo:**` en la plantilla de
`CONTEXT.md` (sección 4, "Decisiones Confirmadas").

**Efecto colateral corregido en el mismo cambio:** al añadir la frase
`"Completo / Lite — ver QUICKSTART_LITE.md"` como ayuda para el humano, la propia
palabra "Lite" (mencionada como opción) generaba un falso positivo de detección.
Se corrigió exigiendo que "Lite" sea el **valor declarado** justo tras los dos
puntos, no una mención posterior en la misma línea.

## 10. Colisión de espacio de nombres entre fases de proceso y fases de ejecución

**Síntoma:** al unificar el formato de tabla, encontré algo más profundo que una
diferencia de columnas. `bootstrap.py` escribía en `PROGRESS.md` una tabla `F0`-`F8`
que mezclaba fases de *proceso* (`F0`=bootstrap del harness, `F1`=entrevista,
`F2`=SPEC.md, `F3`=plan de fases) con una **adivinanza** de fases de *construcción*
(`F4`=Modelo de Datos, `F5`=Backend+Auth, `F6`=Frontend, `F7`=Deploy, `F8`=QA) —
escrita antes de que `SPEC.md` existiera, es decir, antes de que nadie pudiera saber
si el proyecto real tendría ese plan. Mientras tanto, `INICIO_PROYECTO.md` (Fase 3)
instruye al agente a derivar de `SPEC.md` su **propia** tabla `F0`-`Fn`, cuyo `F0`
de ejemplo es "Bootstrap del repo, tooling..." — un `F0` con significado
completamente distinto al `F0` que ya existía en `PROGRESS.md`. Dos fases con el
mismo código y significados incompatibles, condenadas a convivir en el mismo
documento.

**Fix:** se separan los espacios de nombres:
- `M0`-`M3`: fases del *proceso* (lectura de PRD, entrevista, SPEC.md, plan de
  fases) — genéricas, iguales en todo proyecto, y por eso sí se pre-rellenan en
  `bootstrap.py`.
- `F0`-`Fn`: fases de *ejecución* del proyecto real, derivadas de `SPEC.md` en la
  Fase M3 — específicas de cada proyecto, y por eso `bootstrap.py` ya **no** las
  adivina: deja una tabla vacía con una nota explicando qué pegar ahí y cuándo.

Las dos tablas usan exactamente el mismo esquema de columnas
(`Fase | Objetivo | Entregable | Depende de | Estado`), así que la tabla que el
agente redacta en la Fase 3 de `INICIO_PROYECTO.md` se copia **literalmente**
dentro de `PROGRESS.md`, sin reformatear nada.

`task_generator.py` ahora:
- Parsea varias tablas independientes dentro del mismo `PROGRESS.md` (antes solo
  leía la primera tabla que encontraba en todo el documento).
- Solo autodetecta y genera `TASK-Fx.md` para códigos `F<N>` — las fases `M<N>`
  son pasos de descubrimiento, no tareas de código; pedir `--phase M1` explícitamente
  ahora falla con un mensaje claro en vez de intentar rellenar `TASK_TEMPLATE.md`
  con eso.
- Distingue "todavía no existe la tabla F" (avisa qué fases M faltan) de "ya no
  queda ninguna F pendiente" (proyecto de ejecución completo) — antes ambos casos
  daban el mismo mensaje genérico.
- Si la tabla no tiene columna de título separada (el esquema de la Fase 3 no la
  tiene), usa el objetivo truncado como título en vez de repetir el código de fase
  desnudo (`TASK-F0 — F0` → `TASK-F0 — BOOTSTRAP DEL REPO, TOOLING, LINTING...`).

**Verificación:** ejecutado el ciclo completo — bootstrap con solo `M0`-`M3` (sin
ninguna fila `F`), `task_generator.py` avisando correctamente que faltan fases de
proceso, simulación de `M0`-`M3` cerrados con una tabla `F0`-`F3` añadida a mano
(tal como haría el agente en la Fase M3), y generación correcta de `TASK-F0.md` y
`TASK-F1.md` con título e inyección de checklist de seguridad funcionando.

---

## Archivos afectados por el rediseño M/F (además de los ya listados arriba)

- **`INICIO_PROYECTO.md`** — tabla de ejemplo de la Fase 3 actualizada al esquema
  de 5 columnas con `Estado`, y nota explícita sobre el espacio de nombres `M`/`F`
  y cómo integrar la tabla en `PROGRESS.md`.


Se ejecutó el flujo completo sobre un proyecto de prueba ("Reservas Fácil"):
`bootstrap.py` → `CONTEXT.md`/`PROGRESS.md` generados → `task_generator.py` sobre
F1 (ninguno aplica, correcto), F4 (seguridad SÍ, checklist de `SECURITY.md`
completo e inyectado), F6 (visibilidad + UI/UX SÍ, incluida la tabla del Gate de
entrada, antes vacía). Casos límite probados: fase inexistente (falla con
mensaje claro), proyecto con todas las fases cerradas (termina limpio, sin
regenerar nada), Modo Lite forzado.

---

# Ronda de mejoras post-auditoría (2026-09-05)

## 11. Los TASK generados arrastraban la cabecera meta de la plantilla

**Síntoma:** todo `TASK-Fx.md`/`TASK-QUICK.md` generado empezaba con
`# TASK_TEMPLATE.md — Plantilla maestra` y su bloque "Cómo usar esta plantilla"
(rellenar `<placeholders>`, citar el stack...). Eso es documentación para quien
GENERA la tarea, no para el agente que la ejecuta: ruido de contexto en cada
fase, contradictorio con el principio de ahorro de contexto del propio sistema.

**Fix:** `strip_template_meta_header()` en `task_generator.py` recorta la
plantilla hasta el primer encabezado `# TASK-` (la cabecera meta usa
`TASK_..._TEMPLATE.md`, con guion bajo, así que nunca coincide). Si el marcador
no existiera, avisa por stderr y copia la plantilla íntegra — sin fallo
silencioso.

## 12. Referencia colgante a `SESSION.md`

**Síntoma:** `TASK_TEMPLATE.md` pedía leer "`PROGRESS.md` (y `SESSION.md` si el
proyecto lo usa)", pero `SESSION.md` no está definido en ningún documento del
sistema.

**Fix:** referencia eliminada; el requisito operativo queda en `PROGRESS.md` +
`SKILLS_MCP.md`, que sí existen.

## 13. Búsqueda difusa de PRD con falsos positivos

**Síntoma:** el fallback de `find_prd_file()` tomaba cualquier `.md` de la raíz
como PRD salvo 5 nombres. Un `CHANGELOG.md` o un `NOTES.md` suelto en la raíz de
un proyecto nuevo era tratado como documento de negocio.

**Fix:** constante `NON_PRD_FILES` con todos los archivos de control del harness
y exclusión adicional del prefijo `TASK-*`. Los nombres estándar
(`PRD.md`, `MVP.md`, `brief.md`, `requisitos.md`) siguen teniendo prioridad.

## 14. El módulo RAG estaba huérfano en el flujo

**Síntoma:** `PROYECTOS RAG Y VECTORIALES/RAG_VECTOR_EXTENSION.md` no lo
mencionaba ni `INICIO_PROYECTO.md`, ni `SKILLS_MCP.md`, ni `bootstrap.py`: un
proyecto RAG arrancaba sin activar nunca el módulo.

**Fix (tres piezas):**
- `INICIO_PROYECTO.md`: nuevo punto 12 en la Fase 2 (SPEC), nueva entrada en la
  sección 6 de archivos de control y nueva línea en el checklist de la sección 7.
- `SKILLS_MCP.md`: nueva fila en la matriz de recomendación MCP para
  búsqueda semántica / RAG / vectores.
- `bootstrap.py`: `maybe_activate_rag_module()` detecta keywords RAG en el PRD
  (embeddings, pgvector, búsqueda semántica, LlamaIndex...) y copia el módulo de
  `/docs` a la raíz; si el PRD lo pide pero falta en `/docs`, avisa
  explícitamente (Regla de Oro nº2) para copiarlo del kit maestro.

## 15. Documentación desalineada con el comportamiento real

- `INSTRUCCIONES DE APLICACION.txt`: prometía "resumir en menos de 15 líneas"
  (el script extrae las secciones tal cual, no resume), describía el
  `PROGRESS.md` antiguo (F0/F1) y solo decía `python3` (inexistente en Windows).
  Reescrita: extracción literal + avisos "Sin confirmar", fases M0-M3,
  `python` (Windows) / `python3` (Unix), detección de PRD, módulo RAG y
  referencia a `task_generator.py`.
- `PROTOCOLO DE GESTION Y VISIBILIDAD DE PROYECTOS.txt`: ahora declara en su
  cabecera que es una síntesis ejecutiva y que la fuente de verdad es
  `INICIO_PROYECTO.md` (mitiga el riesgo de divergencia entre los tres
  documentos de arranque; el PDF queda como snapshot estático).
- `guia-automatizacion-tareas.md`: `python` vs `python3` según SO, nuevo
  comportamiento de recorte de plantilla y referencia a los tests.
- `README.md` (nuevo): índice atractivo del sistema con diagramas, mapa de
  archivos, flujo completo y reglas.

## 16. Tests automatizados del kit (`tests/test_harness.py`)

Hasta ahora la única verificación era manual (secciones anteriores de este
changelog). Ahora hay 32 tests sin dependencias externas
(`python -m unittest discover tests -v`), siempre en carpetas temporales:

- Parser de `PROGRESS.md`: tablas múltiples, negritas, columnas combinadas,
  filas inválidas, detección de siguiente fase.
- `extract_section()` contra los documentos reales: la tabla del Gate de entrada
  sale completa; la sección 2.1 corta antes de 2.2.
- Inyectores por marcadores (presente/ausente).
- Heurística de keywords: caso "entre**vista**" (falso positivo clásico) y el
  comportamiento por exceso de "api" en fases frontend.
- Recorte de cabecera meta en ambas plantillas.
- Detección de Modo Lite (valor declarado vs mención, `QUICK_CONTEXT.md`, `--lite`).
- Extracción de metadatos del PRD (completo y sin encabezados).
- `find_prd_file()`: prioridad de nombres estándar, exclusión de archivos de control.
- E2E: `bootstrap.py` → aviso sin fases F → simulación M cerradas + tabla F →
  `TASK-F1.md` generado sin cabecera meta y con checklists inyectados →
  rechazo de fases M y fases inexistentes.

**Verificación de esta ronda:** `python -m unittest discover tests` → 32/32 OK.

---

# Ronda v2 — Enforcement: las reglas se vuelven mecánicas (2026-09-06)

Motivación: el kit obligaba por convención (documentos que dicen lo que no se
hace y agentes que prometen cumplirlo). Esta ronda convierte las Reglas de Oro
4, 5, 7 y 8 en comprobaciones que fallan mecánicamente, sin cambiar la filosofía
del kit (cero dependencias, Markdown como superficie de edición humana).

## 17. `bootstrap.py` emite CI, no solo documentos

**Antes:** el kit generaba documentos; nada verificaba nada a distancia.
**Ahora:** `generate_github_workflow()` emite `.github/workflows/harness.yml`
(nunca sobrescribe si existe) con tres jobs:
- `estado`: `python task_generator.py --check` — valida el estado del harness.
- `secretos`: gitleaks sobre todo el historial (`fetch-depth: 0`).
- `calidad`: tests + auditoría de dependencias condicionados al stack detectado
  (`package.json` → npm ci/test/audit; `requirements.txt`/`pyproject.toml` →
  pytest o unittest + pip-audit).

Además el propio kit obtiene `.github/workflows/tests.yml` (suite de unittest
en cada push/PR). Versión del kit declarada: `HARNESS_VERSION = "2.0.0"`.

## 18. Máquina de estado validada: `progress.json` detrás de `PROGRESS.md`

**Diseño:** `PROGRESS.md` sigue siendo la superficie de edición (humano/agente).
`task_generator.py --sync` lo compila al esquema `harness-state/1` y valida;
`--check` valida sin escribir (es lo que ejecuta el CI); el generador de tareas
auto-recompila si detecta edición manual (el CI, en cambio, es estricto: detecta
drift y falla hasta que alguien haga `--sync`). `--sync` es fail-closed: si el
estado es inválido, no escribe.

**Validaciones aplicadas (cada una es una Regla de Oro hecha mecánica):**
- Estados dentro del enum `pending/in_progress/blocked/done`; IDs únicos `M/F\d+`.
- Toda dependencia declarada existe; ninguna fase cerrada con dependencias
  abiertas (nº4).
- Toda fase cerrada tiene checkpoint de contexto en `PROGRESS.md` (nº5/DoD).
- Toda fase F cerrada tiene su `TASK-F<N>.md` en la raíz (nº7).
- `progress.json` y `PROGRESS.md` sin drift.

**Decisión de arquitectura:** `bootstrap.py` no duplica la lógica de compilación —
importa `task_generator` como módulo vecino y compila con la misma función, así
el JSON nace sincronizado por construcción. Si falta el script, avisa en vez de
inventarse el artefacto. El texto libre en "Depende de" ("SPEC aprobado") se
separa en `depends_on_notes` y no se valida como fase.

## 19. Aprobaciones humanas selladas (`APPROVAL-ID`)

**Antes:** la aprobación era una línea de prosa; el agente podía alegar una
aprobación inexistente y nada lo detectaba.
**Ahora:**
- Formato verificable en `DECISIONS.md > ## Aprobaciones`:
  `**APPROVAL-001** (fecha) · Fase: F2 · Acción: ... · Aprobado por: ... · Ref: ...`
- `task_generator.py --approval "acción" --phase F2 --ref "..."` registra la
  entrada con ID autoincremental y fecha del día.
- `--check` falla si una `TASK-*.md` cita un `APPROVAL-NNN` que no existe en
  `DECISIONS.md`, o si una entrada registrada está incompleta (sin fecha,
  `Acción:` o `Aprobado por:`).
- `TASK_TEMPLATE.md` (Fase L, punto 18) y `TASK_LITE_TEMPLATE.md` piden ahora
  citar el `APPROVAL-ID`; `SKILLS_MCP.md` documenta el formato (sección 5.1).

## 20. Suite ampliada y verificación de la ronda

De 32 a 49 tests: compilación del estado, checkpoint parser (formatos con y sin
negrita), validaciones de dependencias/enum/duplicados, drift y fail-closed,
registro de aprobaciones (autoincremento, formato, menciones sin ID ignoradas)
y e2e ampliado (`--check` en verde tras bootstrap, auto-sanado del generador,
bloqueo tras edición manual sin sync).

**Verificación e2e manual:** proyecto de prueba → `bootstrap.py` (genera
`progress.json` + CI) → `--check` verde → intento de trampa (marcar F0 y F1 como
cerradas sin TASK ni checkpoint): detectado primero por drift y, tras compilar,
`--sync` fail-closed listando las 7 violaciones y sin escribir el JSON → flujo
honesto (TASK + checkpoints) → `--sync` y `--check` en verde.

---

# Entregables de producto y marketing (2026-09-06)

## 21. Estudio de mercado ligero (`ESTUDIO_MERCADO.md`)

Barrido web con fuentes en vivo (septiembre 2026): GitHub Spec Kit, Amazon
Kiro, BMAD Method, Task Master y el estándar AGENTS.md; contexto del ciclo
vibe-coding → spec-driven development. Conclusión: la categoría existe y crece;
el hueco libre es "SDD + enforcement mecánico + gobernanza de capacidades +
español + cero dependencias, local". Posicionamiento recomendado y debilidades
honestas incluidas.

## 22. Web del producto (`web/`) aplicando `UI_UX_EXCLUSIVA.md`

- `web/DESIGN_DIRECTION.md`: Gate de entrada completo, tres direcciones Design
  DNA propuestas («ENCLAVAMIENTO», «ACTA NOTARIAL», «SALA DE CONTROL»), DNA
  elegido con ficha, sistema de movimiento con fallback y auditoría anti-clon.
  Dirección recomendada aplicada por encargo directo; las otras dos quedan
  documentadas para alternar.
- `web/index.html`: página única autocontenida en la dirección
  «ENCLAVAMIENTO» (metáfora del interlocking ferroviario: las reglas no son
  consejos, son checks de merge). Tokens del §9 de UI_UX, componente de señal
  de estado como único portador de estado, divisores de vía, banda "túnel" con
  la salida real del CI (demo del 2026-09-06), tablas de reglas y de paisaje
  competitivo, FAQ AEO con JSON-LD (`SoftwareApplication` + `FAQPage`),
  `prefers-reduced-motion` respetado, landmarks y foco visible.
- `web/llms.txt`: mapa del producto para agentes (GEO, según el formato del
  módulo RAG).

**Verificación:** renderizada en navegador a 1366 px y 390 px; dos defectos
detectados y corregidos (bloque de código sin `white-space: pre`; errata
"Otras/Otros toolkits"). Sin imágenes externas ni JS de terceros; fuentes con
fallback de sistema.

## 23. Retirada de la web del kit (2026-09-06)

Por decisión del responsable, la carpeta `web/` (landing del producto,
`DESIGN_DIRECTION.md` y `llms.txt`) sale del proyecto: no forma parte del
kit funcional. Las entradas 21-22 de este changelog se conservan como
registro histórico de lo que se construyó y cómo se verificó. Las
referencias a `web/` restantes en este archivo son solo históricas.

## 24. Retirada del estudio de mercado del kit (2026-09-06)

Por decisión del responsable, `ESTUDIO_MERCADO.md` (barrido de competidores
y posicionamiento) sale del repositorio: es material de negocio/web, no parte
del kit funcional. Se conserva la entrada 21 como registro histórico; la
investigación vive ahora fuera del repo (web y planificación).
