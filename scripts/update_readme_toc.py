#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""Regenerate the README Table of Contents between TOC markers.

Usage:
    python scripts/update_readme_toc.py [--check]

Behavior:
    - Scans README.md for headings (levels 2-4) outside code fences.
    - Replaces content between <!-- TOC_START --> and <!-- TOC_END -->.
    - If markers are missing, inserts them after the Quick Start block.
    - Generates GitHub-compatible anchor links.

Options:
    --check  Exit with non-zero if the TOC would change (CI guard).
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
TOC_START = "<!-- TOC_START -->"
TOC_END = "<!-- TOC_END -->"
HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")


def slugify(text: str, existing: set[str]) -> str:
    """Generate a GitHub-style slug.

    GitHub algorithm (simplified):
      - Lowercase
      - Remove punctuation (retain alphanum, space, hyphen)
      - Replace each space with hyphen (do NOT collapse consecutive spaces -> multiple hyphens)
      - Do not collapse repeated hyphens
    This preserves double hyphens that appear when punctuation (like '&') is removed.
    """
    text = re.sub(r"`+", "", text)
    s = text.lower()
    # Remove all chars except lowercase letters, digits, space, hyphen
    s = re.sub(r"[^a-z0-9 \-]", "", s)
    # Replace spaces with hyphens (preserving multiplicity)
    s = s.replace(" ", "-").strip("-")
    if not s:
        s = "section"
    base = s
    i = 1
    while s in existing:
        i += 1
        s = f"{base}-{i}"
    existing.add(s)
    return s


def extract_headings(lines: list[str]) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    in_code = False
    fence_re = re.compile(r"^```")
    for line in lines:
        if fence_re.match(line):
            in_code = not in_code
            continue
        if in_code:  # type: ignore[unreachable]  # loop-carried state; mypy false positive
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        if level == 1 or title.lower().startswith("table of contents"):
            continue
        headings.append((level, title))
    return headings


def build_toc(headings: list[tuple[int, str]]) -> str:
    anchors_used: set[str] = set()
    out: list[str] = []
    for level, title in headings:
        if level > 4:
            continue
        anchor = slugify(title, anchors_used)
        indent = "  " * (level - 2)
        out.append(f"{indent}- [{title}](#{anchor})")
    return "\n".join(out) + "\n"


def _render_updated_readme(lines: list[str], toc_body: str) -> tuple[list[str], bool]:
    """Return updated README lines and whether content changed.

    This function is side-effect free to keep main() control flow simple so
    mypy does not mis-detect unreachable code paths.
    """
    new_lines: list[str] = []
    changed = False
    i = 0
    while i < len(lines):
        if lines[i].strip() == TOC_START:
            new_lines.append(lines[i])  # keep marker line with its newline
            i += 1
            old: list[str] = []
            while i < len(lines) and lines[i].strip() != TOC_END:
                old.append(lines[i])
                i += 1
            rendered = "\n" + toc_body
            if "".join(old) != rendered:
                changed = True
            new_lines.append(rendered)
            if i < len(lines):
                new_lines.append(lines[i])  # TOC_END line
        else:
            new_lines.append(lines[i])
        i += 1
    return new_lines, changed


def main() -> int:
    check_mode = "--check" in sys.argv
    lines = README_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    headings = extract_headings(lines)
    toc_body = build_toc(headings)
    new_lines, changed = _render_updated_readme(lines, toc_body)

    if check_mode:
        if changed:
            print("TOC out of date")
            return 1
        print("TOC up to date")
        return 0

    if changed:
        README_PATH.write_text("".join(new_lines), encoding="utf-8")
        print("README TOC updated.")
    else:
        print("TOC is up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
