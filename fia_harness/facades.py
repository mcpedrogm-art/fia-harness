"""Plantillas de las fachadas de compatibilidad que `fia init` escribe en la raíz.

ADR-001: el paquete es la única fuente de verdad. Los scripts `bootstrap.py` y
`task_generator.py` de cada proyecto son fachadas finas que importan `fia_harness`
y re-exportan la API histórica (tests y proyectos v2.2 la usan). Se definen aquí
para que `init`, los tests anti-drift y el propio repo compartan el mismo texto.
"""

FACADE_BOOTSTRAP = '''#!/usr/bin/env python3
"""Fachada de compatibilidad de FIA Harness (v3). La implementación vive en el paquete.

Requiere el paquete instalado:   pip install fia-harness
"""
import sys

try:
    from fia_harness.generators.bootstrap import (
        REQUIRED_TEMPLATES, DEFAULT_FOLDERS, RAG_MODULE_NAME, main)
    from fia_harness.parser.prd import extract_prd_metadata, find_prd_file, NON_PRD_FILES
except ImportError:
    sys.exit("Falta el paquete fia-harness. Instálalo con: pip install fia-harness")

if __name__ == "__main__":
    raise SystemExit(main())
'''

FACADE_TASK_GENERATOR = '''#!/usr/bin/env python3
"""Fachada de compatibilidad de FIA Harness (v3). La implementación vive en el paquete.

Requiere el paquete instalado:   pip install fia-harness
"""
import sys

try:
    from fia_harness.core.state import (
        REQUIRED_SEALED, STATE_FILE, SCHEMA_NAME, STATUS_VALUES,
        compile_state_from_md, state_fingerprint, sha256_hex, validate_state,
        compute_doc_hashes, validate_sealed_docs, validate_spec_snapshot)
    from fia_harness.core.commands import (
        cmd_sync, cmd_check, cmd_seal, cmd_approval, cmd_reopen, cmd_stats)
    from fia_harness.parser.markdown import (
        parse_progress_table, detect_next_phase, get_phase_row, extract_section)
    from fia_harness.core.policy import analyze_phase_requirements
    from fia_harness.generators.task import (
        inject, detect_lite_mode, strip_template_meta_header)
    from fia_harness.legacy import main_task_generator as main
except ImportError:
    sys.exit("Falta el paquete fia-harness. Instálalo con: pip install fia-harness")

if __name__ == "__main__":
    raise SystemExit(main())
'''


def facade_files() -> dict:
    """{nombre de archivo: contenido} de las fachadas de la raíz de un proyecto."""
    return {
        "bootstrap.py": FACADE_BOOTSTRAP,
        "task_generator.py": FACADE_TASK_GENERATOR,
    }
