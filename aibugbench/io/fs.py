"""Phase-0 façade for basic text I/O.

Delegates to legacy helpers when available to avoid behaviour changes.
Only UTF-8 text helpers are exposed for now.
"""

from __future__ import annotations

from pathlib import Path

_StrPath = str | Path

# Try to import legacy helpers if present. Fallbacks keep tests green.
try:
    from validation.repo_audit_enhanced import read_text as _read_text  # type: ignore
except ImportError:  # pragma: no cover - legacy path missing in some envs

    def _read_text(p: _StrPath) -> str:
        """Read UTF-8 text with replacement on errors (fallback)."""
        return Path(p).read_text(encoding="utf-8", errors="replace")


try:
    from validation.repo_audit_enhanced import write_text as _write_text  # type: ignore
except ImportError:  # pragma: no cover

    def _write_text(p: _StrPath, data: str) -> None:
        """Write UTF-8 text (fallback)."""
        Path(p).write_text(data, encoding="utf-8")


__all__ = ["read_text", "write_text"]

# Public proxies
read_text = _read_text
write_text = _write_text
