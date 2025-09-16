from __future__ import annotations

import pathlib
import sys


def is_utf8(p: pathlib.Path) -> bool:
    try:
        p.read_text(encoding="utf-8")
        return True
    except UnicodeDecodeError:
        return False


def has_lf(p: pathlib.Path) -> bool:
    try:
        data = p.read_bytes()
    except Exception:
        return True
    return b"\r\n" not in data


def main() -> int:
    failed = []
    for a in sys.argv[1:]:
        p = pathlib.Path(a)
        if not is_utf8(p) or not has_lf(p):
            failed.append(str(p))
    if failed:
        print("Non-UTF8 or CRLF detected:\n" + "\n".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
