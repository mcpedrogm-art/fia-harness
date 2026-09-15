"""Reglas y heurísticas hoy hardcodeadas (sin motor de políticas formal todavía).

El Policy Engine declarativo (YAML `when/requires`) es v3.1+ (roadmap diferido).
Aquí viven las palabras clave, los marcadores de inyección de plantillas y los
textos de "No aplica", para que los generadores no dependan de constantes sueltas.

Principio (heredado del plan): `heurística → recomendación → decisión`, nunca
`palabra clave → autoridad`.
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
