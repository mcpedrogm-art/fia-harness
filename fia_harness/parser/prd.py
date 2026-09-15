"""Extracción de metadatos del PRD con niveles de confianza (F2 — Parser Engine).

Principio del plan v3: `heurística → recomendación → decisión`, nunca
`palabra clave → autoridad`. Cada campo extraído lleva su nivel de confianza
(`alta` / `media` / `ninguna`) y el método que lo resolvió; `CONTEXT.md` refleja
ese nivel en sus avisos en vez de tratar el regex como verdad binaria.

Estrategias por orden:
1. Encabezado (H2/H3) que coincide exactamente con un sinónimo → `alta`.
2. Encabezado que contiene un sinónimo → `media` (`heading_partial`).
3. Sección con densidad de palabras clave del campo → `media` (`density`).
4. Sin resolver → `ninguna`.

Los sinónimos y palabras clave viven en `data/parser/synonyms.json` (config
versionada): añadir un sinónimo no toca código.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from fia_harness.parser.discovery import NON_PRD_FILES, find_prd_file  # noqa: F401
from fia_harness.parser.markdown import strip_md

CONFIDENCE_LEVELS = ("alta", "media", "ninguna")
TEXT_FIELDS = ("problem", "users")
LIST_FIELDS = ("features", "out_of_scope")
ALL_FIELDS = ("title",) + TEXT_FIELDS + LIST_FIELDS
DEFAULT_TEXT = "No especificado. Por favor, completa este campo."
CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "parser" / "synonyms.json"

# Palabras clave para activar el módulo de extensión RAG/vectorial si el PRD lo pide.
RAG_KEYWORDS = re.compile(
    r"\b(rag|embeddings?|vectorial|pgvector|pinecone|qdrant|milvus|weaviate|"
    r"chroma(?:db)?|faiss|llamaindex|langchain|b[uú]squeda\s+sem[aá]ntica|"
    r"similitud\s+sem[aá]ntica|bases?\s+de\s+datos\s+vectoria(?:l|les))\b",
    re.IGNORECASE,
)


@dataclass
class ExtractionResult:
    """Resultado de extraer un campo: valor, nivel de confianza y método usado."""
    value: object
    confidence: str
    method: str


def load_config(path=None) -> dict:
    """Carga la config versionada de sinónimos/fallback. Fail-closed: sin config
    no se adivina (mejor un error claro que un campo inventado en silencio)."""
    config_path = Path(path) if path else CONFIG_PATH
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"No se pudo cargar la config del parser PRD ({config_path}): {exc}") from exc


def _fold(text: str) -> str:
    """Normaliza para comparar: sin marcado Markdown, minúsculas y sin acentos."""
    text = strip_md(text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _sections(content: str):
    """Secciones (nivel, título, cuerpo) en orden de aparición, con índice estable."""
    sections, current = [], None
    for line in content.split("\n"):
        header = re.match(r"^(#{1,6})\s+(.*)", line)
        if header:
            if current is not None:
                current["body"] = "\n".join(current.pop("lines")).strip()
                sections.append(current)
            current = {"index": len(sections), "level": len(header.group(1)),
                       "title": header.group(2).strip(), "lines": []}
        elif current is not None:
            current["lines"].append(line)
    if current is not None:
        current["body"] = "\n".join(current.pop("lines")).strip()
        sections.append(current)
    return sections


def _bullets(body: str):
    """Viñetas de una sección (comportamiento histórico: *, -, 1., 2.)."""
    lines = (body or "").strip().split("\n")
    return [l.strip("* - ") for l in lines if l.strip().startswith(("*", "-", "1.", "2."))]


def _value_of(field: str, section: dict):
    return _bullets(section["body"]) if field in LIST_FIELDS else section["body"].strip()


def _extract_fields(content: str, field_names, config: dict) -> dict:
    """Extrae varios campos con estrategias en cascada y secciones reclamadas
    (una misma sección no puede resolver dos campos)."""
    sections = _sections(content)
    folded = {f: [_fold(s) for s in config["fields"][f]] for f in field_names}
    all_synonyms = {_fold(s) for syns in config["fields"].values() for s in syns}
    keywords_cfg = config.get("fallback_keywords", {})
    results, claimed = {}, set()

    def take(field, section, confidence, method):
        results[field] = ExtractionResult(_value_of(field, section), confidence, method)
        claimed.add(section["index"])

    # 1) Encabezado exacto → alta
    for field in field_names:
        for syn, syn_folded in zip(config["fields"][field], folded[field]):
            match = next((s for s in sections
                          if s["level"] in (2, 3) and s["index"] not in claimed
                          and _fold(s["title"]) == syn_folded), None)
            if match is not None:
                take(field, match, "alta", f"heading:{syn}")
                break

    # 2) Encabezado parcial → media (excluye títulos que son sinónimo exacto de OTRO campo)
    for field in field_names:
        if field in results:
            continue
        for syn, syn_folded in zip(config["fields"][field], folded[field]):
            match = next((s for s in sections
                          if s["level"] in (2, 3) and s["index"] not in claimed
                          and _fold(s["title"]) not in all_synonyms
                          and syn_folded in _fold(s["title"])), None)
            if match is not None:
                take(field, match, "media", f"heading_partial:{syn}")
                break

    # 3) Densidad de palabras clave en secciones no reclamadas → media
    for field in field_names:
        if field in results:
            continue
        keywords = [_fold(k) for k in keywords_cfg.get(field, [])]
        best, best_score = None, 0
        for section in sections:
            if section["level"] not in (2, 3) or section["index"] in claimed:
                continue
            head, body = _fold(section["title"]), _fold(section["body"])[:600]
            score = 0
            for kw in keywords:
                if not kw:
                    continue
                if re.search(rf"\b{re.escape(kw)}\b", head):
                    score += 3
                if re.search(rf"\b{re.escape(kw)}\b", body):
                    score += 1
            if score > best_score:
                best, best_score = section, score
        if best is not None and best_score >= 2:
            take(field, best, "media", f"density:{best_score}")

    # 4) Sin resolver (o valor vacío) → ninguna
    for field in field_names:
        result = results.get(field)
        if result is None:
            results[field] = ExtractionResult([] if field in LIST_FIELDS else "", "ninguna", "none")
        elif not result.value:
            results[field] = ExtractionResult(result.value, "ninguna", result.method)
    return results


def extract_field(content: str, field_name: str, config: dict = None) -> ExtractionResult:
    """Extrae un campo del PRD con nivel de confianza y método explícitos.

    `field_name`: title | problem | users | features | out_of_scope.
    `config`: config ya cargada (tests/overrides); por defecto, la versionada.
    """
    config = config or load_config()
    if field_name == "title":
        match = re.search(r"^#\s+(.*)", content or "", re.MULTILINE)
        if match:
            return ExtractionResult(match.group(1).strip(), "alta", "h1")
        return ExtractionResult("", "ninguna", "none")
    if field_name not in config["fields"]:
        raise ValueError(f"Campo desconocido para el parser PRD: {field_name!r}")
    return _extract_fields(content or "", [field_name], config)[field_name]


def extract_prd_metadata(prd_path: Path) -> dict:
    """Extrae los metadatos del PRD para pre-rellenar CONTEXT.md.

    Mantiene la interfaz histórica (`title`, `problem`, `users`, `features`,
    `out_of_scope`, `unresolved`) y añade `confidence`: {campo: {level, method}}.
    `unresolved` es exactamente la lista de campos con confianza `ninguna`.
    """
    metadata = {
        "title": None,
        "problem": DEFAULT_TEXT,
        "users": DEFAULT_TEXT,
        "features": [],
        "out_of_scope": [],
        "unresolved": [],
        "confidence": {},
    }

    if not prd_path or not prd_path.exists():
        metadata["title"] = "Nuevo Proyecto"
        metadata["unresolved"] = list(ALL_FIELDS)
        for field in ALL_FIELDS:
            metadata["confidence"][field] = {"level": "ninguna", "method": "none"}
        return metadata

    content = prd_path.read_text(encoding="utf-8")

    title_result = extract_field(content, "title")
    if title_result.confidence == "ninguna":
        metadata["title"] = prd_path.stem.replace("_", " ").replace("-", " ").strip().title()
        metadata["confidence"]["title"] = {"level": "media", "method": "filename"}
    else:
        metadata["title"] = title_result.value
        metadata["confidence"]["title"] = {"level": title_result.confidence,
                                           "method": title_result.method}

    results = _extract_fields(content, list(TEXT_FIELDS) + list(LIST_FIELDS), load_config())

    for field in TEXT_FIELDS:
        result = results[field]
        if result.confidence == "ninguna":
            metadata[field] = DEFAULT_TEXT
            metadata["unresolved"].append(field)
        else:
            metadata[field] = result.value
        metadata["confidence"][field] = {"level": result.confidence, "method": result.method}

    for field in LIST_FIELDS:
        result = results[field]
        value = list(result.value or [])
        metadata[field] = value
        if not value:
            metadata["unresolved"].append(field)
        metadata["confidence"][field] = {"level": result.confidence, "method": result.method}

    return metadata
