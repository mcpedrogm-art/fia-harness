"""Utilidades de consola compartidas: avisos, errores y encoding de Windows."""

import sys


def warn(msg: str):
    print(f"   [!] {msg}", file=sys.stderr)


def fail(msg: str):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def fix_windows_console_encoding():
    """Evita UnicodeEncodeError (✅/❌) en consolas Windows con codificación cp1252."""
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
