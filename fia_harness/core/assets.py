"""Pack de assets UI (v3.5): manifiesto + descarga verificada.

El kit no distribuye contenido de terceros: `fia assets fetch` descarga un pack
descrito por un manifiesto (`UI_ASSETS.json`) y **verifica SHA-256 antes de
escribir**. Opt-in, stdlib-only, idempotente y fail-closed. `fia assets manifest`
genera el manifiesto para quien publica el pack. Doc: `docs/UI_ASSETS.md`.
"""

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from fia_harness.core.console import fail, fix_windows_console_encoding

MANIFEST_VERSION = 1
DEFAULT_MANIFEST = "UI_ASSETS.json"
DOWNLOAD_TIMEOUT = 60
_CHUNK = 64 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_target(project_dir: Path, raw_path: str) -> Path:
    """Ruta destino dentro del proyecto; rechaza absolutas y traversal."""
    if not raw_path or Path(raw_path).is_absolute():
        fail(f"Ruta de asset inválida (absoluta o vacía): {raw_path!r}")
    target = (project_dir / raw_path).resolve()
    root = project_dir.resolve()
    if target != root and root not in target.parents:
        fail(f"Ruta de asset fuera del proyecto: {raw_path!r}")
    return target


def load_manifest(ref: str) -> dict:
    """Carga el manifiesto desde URL (http/https), file:// o ruta local."""
    if ref.startswith(("http://", "https://", "file://")):
        try:
            with urllib.request.urlopen(ref, timeout=DOWNLOAD_TIMEOUT) as response:
                data = response.read()
        except (urllib.error.URLError, OSError) as error:
            fail(f"No se pudo leer el manifiesto {ref}: {error}")
    else:
        path = Path(ref)
        if not path.exists():
            fail(f"No existe el manifiesto: {path}")
        data = path.read_bytes()
    try:
        manifest = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(f"Manifiesto inválido (JSON): {error}")
    if manifest.get("version") != MANIFEST_VERSION:
        fail(f"Versión de manifiesto no soportada: {manifest.get('version')!r} "
             f"(se espera {MANIFEST_VERSION})")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        fail("El manifiesto no contiene 'assets'.")
    return manifest


def fetch_manifest(project_dir: Path, ref: str) -> int:
    """Descarga y verifica todos los assets del manifiesto (idempotente)."""
    manifest = load_manifest(ref)
    downloaded = skipped = 0
    for entry in manifest["assets"]:
        path = entry.get("path")
        url = entry.get("url")
        expected = str(entry.get("sha256") or "").lower()
        if not path or not url or len(expected) != 64:
            fail(f"Entrada de asset inválida (path/url/sha256): {entry!r}")
        target = _safe_target(project_dir, path)
        if target.exists() and sha256_file(target) == expected:
            print(f"   [.] Ya existe y coincide: {path}")
            skipped += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name + ".part")
        print(f"   [↓] {path}")
        try:
            with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT) as response, \
                    open(temp, "wb") as handle:
                while True:
                    chunk = response.read(_CHUNK)
                    if not chunk:
                        break
                    handle.write(chunk)
        except (urllib.error.URLError, OSError) as error:
            if temp.exists():
                temp.unlink()
            fail(f"Fallo al descargar {url}: {error}")
        actual = sha256_file(temp)
        if actual != expected:
            temp.unlink()
            fail(f"SHA-256 no coincide para {path}\n"
                 f"   esperado: {expected}\n   obtenido: {actual}")
        os.replace(temp, target)
        downloaded += 1
    print(f"✅ Assets: {downloaded} descargado(s) · {skipped} ya en su sitio · "
          f"{len(manifest['assets'])} en el manifiesto")
    return 0


def cmd_assets_fetch(project_dir: Path, ref: str) -> int:
    fix_windows_console_encoding()
    return fetch_manifest(project_dir, ref)


def build_manifest(source_dir: Path, base_url: str, out_path: Path) -> int:
    """Genera `UI_ASSETS.json` desde un directorio local (para publicar el pack)."""
    if not source_dir.is_dir():
        fail(f"No es un directorio: {source_dir}")
    base = base_url.rstrip("/")
    entries = []
    for file in sorted(source_dir.rglob("*")):
        if not file.is_file():
            continue
        relative = file.relative_to(source_dir).as_posix()
        entries.append({"path": relative,
                        "url": f"{base}/{urllib.parse.quote(relative)}",
                        "sha256": sha256_file(file)})
    if not entries:
        fail(f"Sin archivos en {source_dir}")
    manifest = {"version": MANIFEST_VERSION, "assets": entries}
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"✅ Manifiesto generado: {out_path} ({len(entries)} assets)")
    return 0


def cmd_assets_manifest(source_dir: Path, base_url: str, out_path: Path) -> int:
    fix_windows_console_encoding()
    return build_manifest(source_dir, base_url, out_path)
