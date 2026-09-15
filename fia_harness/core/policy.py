"""Reglas y heurísticas hoy hardcodeadas (sin motor de políticas formal todavía).

El Policy Engine declarativo (YAML `when/requires`) es v3.2+ (roadmap diferido).
Aquí viven las palabras clave, los marcadores de inyección de plantillas, los
textos de "No aplica", las señales de riesgo y la detección de Modo Lite.

Principio (heredado del plan): `heurística → recomendación → decisión`, nunca
`palabra clave → autoridad`. Las señales de riesgo NO bloquean por sí mismas:
exigen una decisión humana registrada (ver `core.quality`).
"""

import re

# Palabras clave para el análisis semántico (heurístico, no sustituye la revisión humana)
SEC_KEYWORDS = ["bbdd", "database", "migracion", "migración", "auth", "login", "password",
                "seguridad", "permisos", "permiso", "rls", "secret", "secreto", "token",
                "api", "servidor", "vps", "infra", "deploy", "despliegue", "credencial"]
VIS_KEYWORDS = ["frontend", "landing", "blog", "docs", "public", "seo", "aeo", "geo",
                "web", "contenido", "despliegue", "deploy"]
UI_KEYWORDS = ["frontend", "ui", "ux", "pantalla", "interfaz", "diseño", "componente",
               "animacion", "animación", "motion", "formulario", "vista", "page"]

# Señales de riesgo alto (v3.1): si una fase las toca, exige una **decisión humana
# registrada** (aprobación o exención motivada). Es una heurística de recomendación:
# el gate no bloquea por la palabra clave, bloquea por la ausencia de decisión.
RISK_KEYWORDS = [
    # auth y control de acceso
    "auth", "login", "password", "contraseña", "permisos", "permiso", "roles",
    "oauth", "jwt", "2fa", "mfa",
    # datos y migraciones
    "bbdd", "database", "migracion", "migración", "migration", "schema", "esquema", "rls",
    # secretos y credenciales
    "secret", "secreto", "token", "credencial", "api key", "apikey",
    # pagos y datos personales
    "pago", "pagos", "payment", "stripe", "billing", "facturacion", "facturación",
    "pii", "datos personales", "rgpd", "gdpr", "dni",
    # infraestructura, despliegue y servicios externos
    "infra", "vps", "firewall", "deploy", "despliegue", "servidor",
    "webhook", "sdk", "integracion", "integración",
]

# Marcadores de inyección esperados dentro de TASK_TEMPLATE.md.
# El bloque completo <!-- INJECT:X --> ... <!-- /INJECT --> se sustituye entero.
INJECT_MARKERS = {
    "visibility": "VISIBILITY_CHECKLIST",
    "security": "SECURITY_CHECKLIST",
    "ui_ux": "UIUX_CHECKLIST",
}

NOT_APPLICABLE_TEXT = {
    "visibility": "No aplica: esta tarea no toca superficie pública ni contenido indexable.",
    "security": "No aplica: esta tarea no toca auth, datos de usuario, secretos ni infraestructura.",
    "ui_ux": "No aplica: esta tarea no toca UI/UX ni assets visuales.",
}


def _compile_keyword_regex(keywords):
    # \b exige límite de palabra real: evita falsos positivos como "vista" dentro de
    # "entrevista", o "api" dentro de "rápido" (aunque en ese caso ni coincidiría, es
    # el mismo tipo de error que sí ocurría por subcadena simple).
    return re.compile(r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")\b", re.IGNORECASE)


_SEC_RE = _compile_keyword_regex(SEC_KEYWORDS)
_VIS_RE = _compile_keyword_regex(VIS_KEYWORDS)
_UI_RE = _compile_keyword_regex(UI_KEYWORDS)


def analyze_phase_requirements(row: dict) -> dict:
    text = f"{row['title']} {row['objective']}"
    return {
        "security": bool(_SEC_RE.search(text)),
        "visibility": bool(_VIS_RE.search(text)),
        "ui_ux": bool(_UI_RE.search(text)),
    }


def risk_signals(row: dict) -> list:
    """Señales de riesgo alto detectadas en la fase (heurística, ordenadas)."""
    text = f"{row.get('title', '')} {row.get('objective', '')}"
    return sorted({kw for kw in RISK_KEYWORDS
                   if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE)})


def detect_lite_mode(context_content: str, project_dir, forced: bool) -> bool:
    """Modo Lite: forzado, declarado en CONTEXT.md o marcado por QUICK_CONTEXT.md."""
    if forced:
        return True
    if (project_dir / "QUICK_CONTEXT.md").exists():
        return True
    # Exige que "Lite" sea el valor declarado justo tras "Modo de trabajo:" (permitiendo
    # negrita/código de Markdown entre medias) — NO basta con que "Lite" se mencione más
    # adelante en la misma línea como una de las opciones posibles (p. ej. "Completo / Lite").
    return bool(re.search(r"modo\s+de\s+trabajo\**\s*:\**\s*lite\b",
                          context_content, re.IGNORECASE))
