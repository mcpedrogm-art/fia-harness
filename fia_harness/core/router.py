"""Router de carril (v3.3, F10): propone Lite o Full con razonamiento explícito.

Determinista y fail-closed: las señales de riesgo (`policy.RISK_KEYWORDS`) fuerzan
el carril Full; solo se propone Lite cuando la descripción coincide con la
allowlist cerrada. No mantiene estado ni presupuesto anti-gaming (gameable por el
agente; si algún día se quiere, se calcula en CI desde el diff de git — ADR-010).

El router **propone**: la decisión sigue siendo humana y el enforcement real sigue
siendo el gate v3.1 (regla de oro nº13) en `--check`/`fia verify`.
"""

import re

from fia_harness.core import policy

LITE_CATEGORIES = (
    ("fix-bug", "fix de bug acotado",
     ("bug", "fix", "corregir", "corrige", "arreglar", "arregla", "fallo",
      "excepcion", "excepción")),
    ("refactor-local", "refactor local sin cambio de contrato público",
     ("refactor", "refactorizar", "renombrar", "renombra", "extraer", "extrae",
      "limpieza", "limpiar")),
    ("solo-tests", "cambios solo en tests",
     ("test", "tests", "prueba", "pruebas", "cobertura", "fixture", "unittest")),
    ("lint-estilo", "lint / estilo / typos",
     ("lint", "estilo", "formato", "formateo", "typo", "typos", "ortografia",
      "ortografía")),
    ("docs", "actualización de documentación",
     ("doc", "docs", "documentacion", "documentación", "readme", "comentario",
      "comentarios")),
)


def _matches(text: str, keywords) -> bool:
    pattern = r"\b(?:" + "|".join(re.escape(word) for word in keywords) + r")\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def classify(description: str) -> dict:
    """Clasifica una descripción. Devuelve carril, razón, categorías y señales.

    Orden: señales de riesgo → Full; allowlist → Lite; resto → Full (fail-closed)."""
    text = (description or "").strip()
    signals = policy.risk_signals({"title": text, "objective": ""})
    categories = [label for _key, label, words in LITE_CATEGORIES
                  if _matches(text, words)]
    if signals:
        return {"lane": "FULL", "reason": "señales de riesgo: " + ", ".join(signals),
                "categories": categories, "risk_signals": signals}
    if categories:
        return {"lane": "LITE",
                "reason": "coincide con la allowlist: " + " · ".join(categories),
                "categories": categories, "risk_signals": signals}
    return {"lane": "FULL",
            "reason": "sin coincidencia en la allowlist (fail-closed: el error barato es la fricción)",
            "categories": categories, "risk_signals": signals}


def cmd_route(description: str) -> int:
    """`fia route "<descripción>"`: imprime la propuesta y las razones (no ejecuta)."""
    result = classify(description)
    print("[ROUTER] Propuesta de carril (solo clasifica; no ejecuta nada)")
    print(f"[ROUTER] Carril: {result['lane']}")
    print(f"[ROUTER] Razón: {result['reason']}")
    if result["lane"] == "LITE":
        print("[ROUTER] Lite no exime del gate de riesgo (regla nº13): una señal de "
              "riesgo lo bloquea en `--check`.")
        print("[ROUTER] Para ejecutar en Lite: `fia task --lite` (QUICKSTART_LITE.md).")
    else:
        print("[ROUTER] Sigue el ciclo formal (SPEC → TASK → ciclo A–L).")
    return 0
