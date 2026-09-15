"""FIA Harness — kit local de especificación, control de fases y enforcement
para desarrollo con agentes de IA.

Paquete de instalación (PyPI): `uvx fia-harness init` (o `fia init`) monta un
proyecto nuevo con las plantillas del kit en /docs, fachadas de los scripts en la
raíz y un PRD.md de partida. En v3 el paquete es la única fuente de verdad: los
scripts de los proyectos son fachadas finas que importan `fia_harness` (ADR-001).
Cero dependencias, Python 3.8+.
"""

__version__ = "3.0.0a3"
