"""Core documentation validation primitives.

Parsing and classification logic for documentation command blocks. Execution,
sandboxing, and reporting are handled by higher-level orchestration (no legacy
script shims retained in this private repository).
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
from typing import ClassVar


class Platform(Enum):
    WINDOWS_CMD = "windows_cmd"
    WINDOWS_POWERSHELL = "windows_powershell"
    MACOS_LINUX = "macos_linux"


class CommandType(Enum):
    SAFE = "safe"
    SANDBOX = "sandbox"
    DESTRUCTIVE = "destructive"
    NETWORK = "network"


@dataclass
class Command:
    content: str
    platform: Platform
    file_path: str
    line_number: int
    command_type: CommandType = CommandType.SAFE


class DocumentationValidator:
    """Lightweight parser facade.

    Provides extraction utilities separated from execution concerns for clear
    unit testing and reuse.
    """

    COMMAND_BLOCK_PATTERNS: ClassVar[dict[Platform, list[str]]] = {
        Platform.WINDOWS_CMD: [r"```cmd\s*\n(.*?)\n```", r"```batch\s*\n(.*?)\n```"],
        Platform.WINDOWS_POWERSHELL: [r"```powershell\s*\n(.*?)\n```", r"```ps1\s*\n(.*?)\n```"],
        Platform.MACOS_LINUX: [r"```(?:bash|sh|shell)\s*\n(.*?)\n```"],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def extract_commands_from_text(self, text: str, file_path: Path) -> list[Command]:
        commands: list[Command] = []
        for platform, patterns in self.COMMAND_BLOCK_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.DOTALL):
                    block = match.group(1).strip()
                    if not block:
                        continue
                    start_line = text[: match.start()].count("\n") + 1
                    for offset, cmd in enumerate(self._split_block(block)):
                        commands.append(
                            Command(
                                content=cmd,
                                platform=platform,
                                file_path=str(file_path),
                                line_number=start_line + offset,
                            )
                        )
        return commands

    def _split_block(self, block: str) -> Iterable[str]:
        current: list[str] = []
        for raw in block.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith("\\"):
                current.append(line[:-1].strip())
                continue
            current.append(line)
            if current:
                cmd = " ".join(current).strip()
                if self._looks_like_command(cmd):
                    yield cmd
                current = []
        if current:
            cmd = " ".join(current).strip()
            if self._looks_like_command(cmd):
                yield cmd

    def _looks_like_command(self, text: str) -> bool:
        if len(text) < 2 or len(text) > 300:
            return False
        descriptive = ("for ", "this ", "ensure ", "you can ")
        low = text.lower()
        if any(low.startswith(d) for d in descriptive):
            return False
        patterns = [
            r"^[a-zA-Z0-9._-]+(\s+|$)",  # tool name optionally with args
            r"^(python|pip|git|pytest)(\s+|$)",
            r"^(cd|ls|dir|echo|mkdir)(\s+|$)",
        ]
        return any(re.match(p, text) for p in patterns)


__all__ = ["Command", "CommandType", "DocumentationValidator", "Platform"]
