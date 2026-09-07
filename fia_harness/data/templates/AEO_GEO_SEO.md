# AEO_GEO_SEO.md — Especificación y checklist de visibilidad

**Propósito:** este documento define cómo el proyecto gestiona su visibilidad en tres tipos de motor distintos, y qué checklist debe aplicar cada `TASK-XXX.md` (Fase H2) que toque contenido o páginas públicas. Se completa en la Fase 1.10 de `INICIO_PROYECTO.md` y se referencia desde `SPEC.md`.

---

## 1. Definiciones

| Sigla | Nombre | Qué optimiza | Ejemplo de resultado |
|---|---|---|---|
| **SEO** | Search Engine Optimization | Posición en resultados de buscadores tradicionales (Google, Bing) | Aparecer en la página 1 de resultados para "<keyword>" |
| **AEO** | Answer Engine Optimization | Ser la respuesta directa extraída (featured snippet, asistentes de voz, resúmenes tipo Google SGE) | Tu contenido aparece como la respuesta destacada, sin clic |
| **GEO** | Generative Engine Optimization | Ser citado o recomendado por motores generativos (ChatGPT, Perplexity, Gemini, Claude) al responder | El asistente cita o menciona tu marca/producto como fuente |

**Principio común a los tres:** contenido claro, bien estructurado, autoritativo, actualizado y con datos verificables (señales tipo E-E-A-T: Experiencia, Pericia, Autoridad, Confianza). No son técnicas alternativas — se refuerzan entre sí.

---

## 2. Decisión del proyecto (rellenar en Fase 1.10)

- **¿Tiene el proyecto superficie pública indexable?** <Sí/No — si es No, este documento no aplica y se marca como "No aplica" en `SPEC.md`>
- **Prioridad relativa:** <p. ej. "SEO alto, AEO medio, GEO medio" o "GEO prioritario por ser un producto B2B técnico citado en foros">
- **Páginas/piezas objetivo:** <landing, blog, docs, ficha de producto, comparativas...>
- **Keywords / temática de referencia:** <lista o "pendiente de investigación de keywords">
- **Competidores/fuentes de referencia a observar:** <lista>

---

## 3. Checklist técnico transversal (todas las páginas públicas)

- [ ] `<title>` y `meta description` únicos por página, alineados con la keyword/tema objetivo.
- [ ] HTML semántico: jerarquía de encabezados (`h1` único, `h2`/`h3` en orden), landmarks (`main`, `nav`, `header`, `footer`).
- [ ] Datos estructurados (`schema.org`) según el tipo de página: `Organization`, `Product`, `Article`, `FAQPage`, `HowTo`, `BreadcrumbList`.
- [ ] `sitemap.xml` actualizado y `robots.txt` correcto (no bloquear por error páginas indexables).
- [ ] URLs canónicas definidas; `hreflang` si hay multi-idioma.
- [ ] Open Graph y Twitter Cards para compartición social.
- [ ] Rendimiento (Core Web Vitals: LCP, CLS, INP) y accesibilidad (afectan a SEO y AEO por igual).
- [ ] Imágenes con `alt` descriptivo.

---

## 4. Checklist específico SEO

- [ ] Investigación de keywords y mapeo keyword → URL (una URL "dueña" por keyword principal, sin canibalización).
- [ ] Enlazado interno coherente entre piezas de contenido relacionadas.
- [ ] Mobile-first y velocidad de carga verificada.
- [ ] Estrategia de backlinks documentada (ejecución fuera del alcance del agente, pero se deja constancia del plan).

---

## 5. Checklist específico AEO

- [ ] Formato "respuesta directa primero, desarrollo después": la primera frase del bloque responde ya a la pregunta.
- [ ] Uso de listas, tablas y bloques FAQ para fragmentos fácilmente extraíbles.
- [ ] Marcado `FAQPage`/`HowTo` en schema.org donde el contenido lo permita.
- [ ] Preguntas frecuentes redactadas tal y como las escribiría el usuario (long-tail, lenguaje natural).

---

## 6. Checklist específico GEO

- [ ] Contenido citable: afirmaciones concretas, con cifras/fuentes verificables (evitar vaguedad genérica).
- [ ] Bloques de contenido autocontenidos: un LLM debe poder extraer un párrafo y que tenga sentido completo sin el resto de la página.
- [ ] Archivo `llms.txt` en la raíz del sitio (estándar emergente para orientar a los LLMs sobre qué es el sitio y dónde está el contenido clave).
- [ ] Consistencia de la información de marca/producto en todas las páginas y perfiles externos (los motores generativos ponderan la consistencia entre fuentes).
- [ ] Presencia en fuentes que los LLMs suelen indexar/citar: documentación oficial, GitHub, foros técnicos, directorios relevantes del sector.

---

## 7. Integración con el plan de fases

| Fase típica (ver `INICIO_PROYECTO.md`) | Qué checklist aplica |
|---|---|
| F3 — Frontend/contenido | Transversal + AEO (estructura de contenido) + GEO (citabilidad) |
| F5 — Integraciones | Transversal (Open Graph, structured data si depende de integración) |
| F7 — Despliegue | Transversal (sitemap, robots.txt, `llms.txt`, Core Web Vitals en producción) |

- **Responsable:** el agente de Frontend/Contenido (o el rol equivalente en `AGENTS.md` si el proyecto es multi-agente).
- **Validación:** en la Fase K de la `TASK-Fx.md` correspondiente, añadir verificación con herramientas tipo Lighthouse (Core Web Vitals) y un validador de datos estructurados, además del pipeline habitual de tests/build.

---

## 8. Plantilla de checklist por página/pieza (rellenar una por cada página pública relevante)

| Página/URL | Title/meta ✅ | Schema.org | Respuesta directa (AEO) | Bloque citable (GEO) | Core Web Vitals | Estado |
|---|---|---|---|---|---|---|
| `<ruta 1>` | | | | | | Pendiente / OK |
| `<ruta 2>` | | | | | | Pendiente / OK |
