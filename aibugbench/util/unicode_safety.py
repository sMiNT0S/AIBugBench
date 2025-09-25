"""Unicode / TTY helpers extracted from legacy code.

Only lightweight standard-library code is used so this file has *no* external
runtime dependencies.
"""

from __future__ import annotations

import sys
from typing import TextIO

__all__ = [
    "is_unicode_safe",
    "safe_print",
]


def is_unicode_safe(stream: TextIO | None = None) -> bool:
    """Return *True* if *stream* is capable of rendering Unicode safely.

    The logic mirrors the previous ad-hoc checks scattered in legacy files:
    1. If the stream is not a tty ``isatty()`` -> assume safe (redirected to
      file or pipe).
    2. On Windows, we rely on UTF-8 mode (code page 65001) or *utf-8* encoding
      on the text wrapper.
    3. Otherwise, check that encoding contains *utf*.
    """
    stream = stream or sys.stdout

    try:
        if not stream.isatty():
            return True
    except Exception:  # pragma: no cover - safety
        return True

    enc = (stream.encoding or "").lower()
    if "utf" in enc:
        return True

    if sys.platform.startswith("win"):
        # Code page 65001 is UTF-8 on modern Windows terminals.
        try:
            import ctypes  # pragma: no cover - Windows-only

            windll = getattr(ctypes, "windll", None)
            if windll is not None and hasattr(windll, "kernel32"):
                get_cp = getattr(windll.kernel32, "GetConsoleOutputCP", None)
                if callable(get_cp):
                    cp = int(get_cp())
                    return cp == 65001
        except Exception:  # pragma: no cover
            return False
    return False  # Non-Windows or Windows without UTF-8 code page


def safe_print(message: str, *, ascii_replace: bool = True, stream: TextIO | None = None) -> None:
    """Print *message* with fallback replacement if Unicode is unsafe."""
    stream = stream or sys.stdout
    if ascii_replace and not is_unicode_safe(stream):
        message = message.encode("ascii", "replace").decode("ascii")
    print(message, file=stream)
