# Módulo de Extensión: Arquitectura RAG y Bases de Datos Vectoriales

> **Propósito:** Definir los estándares técnicos, el conjunto de herramientas (Skills/MCP), el esquema de datos y las salvaguardas de seguridad para proyectos que implementen búsqueda semántica, embeddings y sistemas RAG.
> **Estado de activación:** Este documento se activa únicamente cuando `SPEC.md` requiere procesamiento de documentos, búsqueda por similitud o memoria a largo plazo.

---

## 1. Stack Tecnológico Recomendado

Elige una combinación de la siguiente matriz según el volumen y la infraestructura del proyecto:

| Capa | Opción Preferente (Self-Hosted / Servidor) | Opción Managed / Serverless | Criterio de Selección |
|---|---|---|---|
| **Base de Datos Vectorial** | **Supabase (pgvector)** | **Pinecone / Qdrant Cloud** | `pgvector` si ya usas PostgreSQL / Supabase. Qdrant/Pinecone para >1M de vectores o búsquedas híbridas avanzadas. |
| **Modelos de Embeddings** | **text-embedding-3-small** (OpenAI) / **multilingual-e5-large** | **Cohere Embed v3** | `text-embedding-3-small` para relación calidad/precio; Cohere para compresión de contexto y búsqueda multilingüe. |
| **Framework RAG / Orquestación** | **LlamaIndex** / **LangChain (JS/Python)** | **Vercel AI SDK** | Vercel AI SDK para apps React/Next.js; LlamaIndex/LangChain para canalizaciones complejas de ingestión. |
| **Reranking (Reordenamiento)** | **Cohere Rerank v3** | **BGE-Reranker-Large** | Imprescindible para filtrar contexto irrelevante antes de inyectar en el LLM. |

---

## 2. Inventario de Skills y Servidores MCP Recomendados

Para operar con este módulo bajo la regla de **Gobernanza de Capacidades (Aprobación Humana Obligatoria)**, se definen los siguientes servidores MCP y Skills:

### Servidores MCP Sugeridos
1. **`mcp-server-pgvector` / `mcp-server-supabase`**:
   * **Propósito:** Permitir al agente inspeccionar esquemas de tablas con vectores, ejecutar consultas de prueba de distancia de coseno (`<=>`) o L2 (`<->`).
   * **Permiso por defecto:** `read-only`.
2. **`mcp-server-filesystem` / `mcp-server-gdrive`**:
   * **Propósito:** Ingestión de documentos de origen (PDFs, Markdown, DOCX) para el pipeline de preparación de datos.
3. **`mcp-server-fetch`**:
   * **Propósito:** Extracción e ingesta de contenido web para chunking y embedding dinámico.

### Skills de Desarrollo / Agente
* **`rag-chunking-evaluator`**: Evaluación y prueba de estrategias de fragmentación (Recursive Text Splitter, Semantic Chunking).
* **`embedding-cost-calculator`**: Cálculo preventivo de tokens y costes de vectorización antes de ejecutar la ingesta masiva.

---

## 3. Arquitectura del Pipeline RAG y Reglas de Control

Todo pipeline RAG dentro del protocolo debe seguir este ciclo estricto de 5 pasos:
### A. Estrategia de Chunking (Fragmentación)
* **Regla de oro:** Nunca vectorizar documentos completos en un solo bloque.
* **Tamaños estándar recomendados:**
  * **Texto general / Artículos:** 512 tokens con solapamiento (*overlap*) de 50 tokens.
  * **Código / Especificaciones:** Chunking basado en AST (funciones/clases) o bloques Markdown completos (`h2`/`h3`).
* **Metadatos Obligatorios:** Cada chunk DEBE incluir en la base de datos:
  * `source_id` (origen del documento)
  * `chunk_index` (orden relativo)
  * `created_at`
  * `access_level` (para control de permisos / RLS)

### B. Recuperación Híbrida (Hybrid Search) + Reranking
1. **Búsqueda Vectorial (Similitud Coseno):** Recupera contexto semántico.
2. **Búsqueda Full-Text (BM25 / tsvector en Postgres):** Recupera nombres exactos, IDs, fechas y códigos.
3. **Reranking obligatorio:** Recuperar los top 20 resultados combinados y aplicar un modelo de *Rerank* para inyectar solo los **top 3 a 5 chunks** más afines al prompt del LLM.

---

## 4. Estrategia GEO (Generative Engine Optimization) y Estándar `llms.txt`

Para garantizar que el sistema o contenido del proyecto sea fácilmente citable e ingerible por otros asistentes generativos (ChatGPT, Perplexity, Claude, Gemini), se implementa la capa GEO.

### A. Diferenciación Arquitectónica
* **SEO Tradicional:** Diseñado para humanos y crawlers web (HTML, rendimiento Core Web Vitals, clics).
* **GEO:** Diseñado para LLMs y agentes RAG (densidad semántica, factualidad, formato Markdown limpio, citabilidad).

### B. Especificación del Archivo `/llms.txt`
El proyecto DEBE exponer en la raíz web (`/llms.txt`) un mapa de sitio estructurado en Markdown limpio para agentes:

```markdown
# [Nombre del Proyecto / Entidad]

> Resumen ejecutivo en una frase clara (máximo 150 caracteres) que defina la propuesta de valor y el propósito del sitio.

## Información Principal
- [Acerca del Sistema](https://ejemplo.com/docs/about.md): Descripción técnica de la arquitectura y servicios.
- [Catálogo / Servicios](https://ejemplo.com/docs/services.md): Lista de servicios con especificaciones clave y precios.
- [Preguntas Frecuentes](https://ejemplo.com/docs/faq.md): Respuestas concisas a problemas comunes.

## Documentación Ampliada
- [Estructura de Datos](https://ejemplo.com/docs/schema.md): Esquema completo de APIs o datos del sistema.
- [Casos de Uso](https://ejemplo.com/docs/use-cases.md): Ejemplos prácticos y métricas de rendimiento.