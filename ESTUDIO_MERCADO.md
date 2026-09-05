# ESTUDIO_MERCADO.md — ¿Existen herramientas como FIA Harness?

**Fecha:** 2026-09-06 · **Alcance:** estudio ligero (barrido web, no entrevistas) · **Producto:** FIA Harness v2.0.0 — kit local de especificación, control de fases y enforcement para desarrollo con agentes de IA.

---

## 1. Veredicto en una frase

**La categoría existe, está en pleno auge y está dominada por Silicon Valley; el hueco específico de FIA Harness (kit local, cero dependencias, en español, con enforcement mecánico de reglas y gobernanza de Skills/MCP) está vacío, pero no lo estará mucho tiempo.**

## 2. El contexto de mercado (por qué ahora)

- El 92% de los desarrolladores de EE. UU. ya usan IA a diario; el mercado se estima en ~4.700 M$ y el 63% de los usuarios ya no son desarrolladores profesionales (Keyhole Software, 2026).
- El consenso del sector en 2026 es que el "vibe coding" choca con un muro de calidad al llegar a producción ("3-month wall") y que el sustituto natural es el **spec-driven development** — exactamente la categoría que FIA Harness implementa a su manera (AugmentCode, Appwrite, InfoWorld).
- El estándar abierto **AGENTS.md** (anunciado por OpenAI, custodiado ahora por la Linux Foundation) ya lo usan 60.000+ proyectos y 20+ herramientas: el mercado ha normalizado "instrucciones en Markdown en la raíz del repo", que es la materia prima del kit.

## 3. Panorama de competidores y sustitutos

| Herramienta | Qué es | Modelo | Fuerte | Débil (vs FIA) |
|---|---|---|---|---|
| **GitHub Spec Kit** | Toolkit open-source de spec-driven development: constitución → spec → plan → tareas, con slash-commands para Copilot/Claude Code/Gemini CLI | Open source, gratis | Sello GitHub, multi-agente, comunidad enorme, extensible | En inglés; sin enforcement de seguridad (el checklist lo marca el agente); sin gobernanza de Skills/MCP; sin UI/UX |
| **Amazon Kiro** | IDE agéntico: convierte prompts en requisitos (EARS), diseño y tareas; ejecuta con agentes paralelos | Comercial (freemium) | Producto pulido, hooks de calidad, integración AWS | Te ata a su IDE y su nube; proceso cerrado; no es tuyo ni auditable |
| **BMAD Method** | Framework open-source de "personas" agénticas (PM, arquitecto, dev, QA, UX) para agilidad con agentes | Open source | Muy completo en roles y flujo ágil | Mucha ceremonia; inglés; enforcement igualmente confiado al agente |
| **Claude Task Master** | CLI que parsea un PRD en grafo de tareas con dependencias y las alimenta a Claude Code | Open source | Simple y popular para descomposición | Solo cubre trocear tareas; nada de entrevista, seguridad, CI ni aprobaciones |
| **AGENTS.md** | Estándar de archivo de contexto (no es proceso) | Estándar abierto | Portable entre 20+ herramientas | Es un convenio, no un método ni un enforcement |
| **Reglas de IDE (Cursor rules, Claude Skills…)** | Instrucciones y micro-skills por herramienta | Vario | Bajo esfuerzo | Fragmentados por proveedor; sin fase, sin validación de estado |

## 4. Diferenciadores reales de FIA Harness (verificados, no aspiracionales)

1. **Enforcement mecánico de reglas:** `progress.json` validado + `task_generator.py --check` + gitleaks + auditoría de dependencias en CI. En Spec Kit/BMAD el checklist lo cumple el agente "bajo palabra"; aquí un push que viola una regla no pasa el merge. Es el mismo salto convención→infraestructura que dio origen a la v2.
2. **Gobernanza de Skills/MCP con sello:** ningún competidor trata la instalación de herramientas del agente como gate de seguridad con aprobaciones `APPROVAL-ID` verificables.
3. **Cero dependencias y local:** Python 3.8+ y Markdown. Sin cuenta, sin nube, sin telemetría; auditable en una tarde.
4. **Español nativo:** toda la categoría relevante está en inglés; el mercado hispanohablante (LATAM + España, ~600M hablantes) está desatendido en este nicho.
5. **Capas que nadie incluye:** visibilidad SEO/AEO/GEO como checklist por fase, dirección UI/UX anti-clon con Design DNA, y módulo RAG condicional.

## 5. Debilidades honestas frente a la competencia

- **Sin comunidad ni distribución:** Spec Kit tiene a GitHub detrás; Task Master, miles de estrellas. FIA Harness hoy es un proyecto personal sin repo público.
- **Sin integraciones de agente:** los rivales se enchufan a los agentes con slash-commands/MCP nativos; aquí el "enchufe" es copiar archivos y dar contexto al agente.
- **Mantenimiento individual:** Kiro/Spec Kit tienen equipos; el kit depende de una persona.
- **Adopción friccional:** exige disciplina de proceso (entrevista, SPEC, checkpoints) — un desarrollador acostumbrado al vibe coding puede verlo como burocracia, que es justo lo que los sostenedores del SDD ya están dispuestos a aceptar.

## 6. Posicionamiento recomendado

> **"El enclavamiento ferroviario de los agentes de IA": el kit ligero, local y en español donde las reglas de oro no son consejos — son checks de merge.**

- **No competir** con Spec Kit en comunidad ni con Kiro en producto pulido: competir en **rigor ejecutable + soberanía (local) + español**.
- Segmento diana: desarrolladores individuales y estudios pequeños hispanohablantes que ya usan agentes y les ha estallado algún proyecto sin especificación.
- Canal natural: GitHub público + contenido en español sobre spec-driven development (long-tail AEO: "qué es spec-driven development", "cómo evitar que la IA rompa producción").

## 7. Conclusión

Herramientas "así" hay — y buenas. Lo que **no** hay es una que combine proceso SDD + enforcement mecánico en CI + gobernanza de capacidades + idioma español + cero dependencias en un kit local. Ese es el hueco real y medible de FIA Harness; la ventana es de 12-18 meses mientras la categoría se consolida.

---

## Fuentes

- [github/spec-kit](https://github.com/github/spec-kit) · [Documentación Spec Kit](https://github.github.com/spec-kit/) · [Anuncio en GitHub Blog](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- [Kiro (kiro.dev)](https://kiro.dev/) · [Introducing Kiro](https://kiro.dev/blog/introducing-kiro/) · [InfoQ sobre Kiro](https://www.infoq.com/news/2025/08/aws-kiro-spec-driven-agent/)
- [BMAD-METHOD (GitHub)](https://github.com/bmad-code-org/BMAD-METHOD) · [Análisis BMAD (Reenbit)](https://reenbit.com/the-bmad-method-how-structured-ai-agents-turn-vibe-coding-into-production-ready-software/)
- [AGENTS.md](https://agents.md/) · [Comparativa AGENTS.md vs alternativas](https://blog.buildbetter.ai/agents-md-vs-cursorrules-vs-claude-skills-2026-comparison/)
- [Vibe Coding vs SDD (AugmentCode)](https://www.augmentcode.com/guides/vibe-coding-vs-spec-driven-development) · [Tendencias vibe coding 2026 (Keyhole)](https://keyholesoftware.com/vibe-coding-trends-2026/) · [7 tendencias 2026 (Appwrite)](https://appwrite.io/blog/post/7-vibe-coding-trends-every-developer-should-know-in-2026) · [InfoWorld: cómo elegir](https://www.infoworld.com/article/4166817/vibe-coding-or-spec-driven-development-how-to-choose.html)

*Nota: Claude Task Master (eyaltoledano/claude-task-master) se documenta por conocimiento directo; las búsquedas en vivo dieron timeout en el momento de redactar este estudio.*
