"""Entorno UI/UX avanzado (v3.6): instalación asistida del pack.

`fia ui setup` descarga el pack oficial (o el indicado con `--url` /
`FIA_UI_PACK_URL`) reutilizando la descarga verificada de `core.assets`
(SHA-256, idempotente, atómica) y guarda el manifiesto usado en el
`UI_ASSETS.json` del proyecto (permite `fia ui status` sin red y re-descargas).
`fia ui status` informa del estado local: completo / parcial / ausente.

El protocolo (`UI_UX_EXCLUSIVA.md` §8, Paso 0) exige **confirmación humana**
antes de instalar: nada se descarga automáticamente.
"""

import json
import os
from pathlib import Path

from fia_harness.core import assets
from fia_harness.core.console import fail, fix_windows_console_encoding

# Pack oficial mantenido por PGMIA (Supabase self-hosted). Override: --url o env.
UI_PACK_URL = "https://supabase.pgmia.es/storage/v1/object/public/fia-assets/UI_ASSETS.json"
RECIPES_PREFIX = "library/"
MANIFEST_NAME = "UI_ASSETS.json"


def pack_url(override: str = None) -> str:
    """Precedencia: --url > FIA_UI_PACK_URL > pack oficial."""
    return override or os.environ.get("FIA_UI_PACK_URL") or UI_PACK_URL


def cmd_ui_setup(project_dir: Path, recipes_only: bool = False, url: str = None) -> int:
    """Instala el entorno UI/UX (o solo las recetas) con verificación."""
    fix_windows_console_encoding()
    ref = pack_url(url)
    manifest = assets.load_manifest(ref)
    entries = manifest["assets"]
    if recipes_only:
        entries = [entry for entry in entries
                   if str(entry.get("path", "")).startswith(RECIPES_PREFIX)]
        if not entries:
            fail(f"El manifiesto no contiene recetas ({RECIPES_PREFIX}*): {ref}")
    manifest = dict(manifest, assets=entries)
    manifest_path = project_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    mode = "solo recetas" if recipes_only else "entorno completo"
    print(f"-> Entorno UI/UX ({mode}): {len(entries)} asset(s) desde {ref}")
    print(f"   Manifiesto guardado en {MANIFEST_NAME} (permite `fia ui status` sin red)")
    return assets.fetch_manifest(project_dir, str(manifest_path))


def cmd_ui_status(project_dir: Path) -> int:
    """Estado local del entorno UI/UX (sin red)."""
    fix_windows_console_encoding()
    manifest_path = project_dir / MANIFEST_NAME
    if not manifest_path.exists():
        print("UI/UX avanzado: ausente (no hay UI_ASSETS.json en el proyecto)")
        return 0
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fail(f"{MANIFEST_NAME} no es JSON válido.")
    if not manifest.get("assets"):
        print("UI/UX avanzado: ausente (UI_ASSETS.json vacío; usa `fia ui setup`)")
        return 0
    state = assets.check_manifest(project_dir, manifest)
    if state["ok"] == state["total"]:
        print(f"UI/UX avanzado: completo ({state['ok']}/{state['total']} assets verificados)")
        return 0
    print(f"UI/UX avanzado: parcial ({state['ok']}/{state['total']} ok · "
          f"{len(state['missing'])} ausentes · {len(state['modified'])} modificados)")
    for path in state["missing"][:5]:
        print(f"   falta: {path}")
    for path in state["modified"][:5]:
        print(f"   modificado: {path}")
    print("   Repara con: fia ui setup")
    return 0
