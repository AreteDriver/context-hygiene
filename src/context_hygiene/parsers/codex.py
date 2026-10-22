"""Codex session JSONL parser.

Parses Codex CLI session exports (JSONL format) where each line is a JSON object
containing conversation turns between the user and Codex ("developer" role).
"""

from __future__ import annotations

import json
from pathlib import Path

from context_hygiene.exceptions import ParseError
from context_hygiene.models import Role, Segment
from context_hygiene.parsers.base import BaseParser

_ROLE_MAP = {
    "user": Role.USER,
    "human": Role.USER,
    "assistant": Role.ASSISTANT,
    "developer": Role.ASSISTANT,  # Codex uses "developer" for the agent
    "system": Role.SYSTEM,
}


class CodexParser(BaseParser):
    """Parse Codex session export JSONL files."""

    def can_parse(self, file_path: Path) -> bool:
        if file_path.suffix.lower() != ".jsonl":
            return False
        try:
            with file_path.open("r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if not first_line:
                    return False
                data = json.loads(first_line)
                # Codex exports have response_item or session_meta entries
                return (
                    isinstance(data, dict)
                    and "type" in data
                    and data["type"] in ("response_item", "session_meta")
                )
        except (json.JSONDecodeError, OSError):
            pass
        return False

    def parse(self, file_path: Path) -> list[Segment]:
        try:
            with file_path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
        except (OSError, UnicodeDecodeError) as e:
            raise ParseError(f"Failed to read {file_path}: {e}") from e

        segments: list[Segment] = []
        idx = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(data, dict):
                continue

            # Skip metadata-only entries
            if data.get("type") != "response_item":
                continue

            payload = data.get("payload", {})
            if payload.get("type") != "message":
                continue

            role = _ROLE_MAP.get(payload.get("role", "user"), Role.USER)
            content = self._extract_content(payload)

            if content.strip():
                segments.append(Segment(index=idx, role=role, content=content))
                idx += 1

        return segments

    @staticmethod
    def _extract_content(payload: dict) -> str:
        """Extract text from a Codex message payload."""
        content = payload.get("content", [])
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts: list[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "input_text":
                    texts.append(block.get("text", ""))
                elif isinstance(block, str):
                    texts.append(block)
            return "\n".join(texts)
        if isinstance(content, dict):
            return content.get("text", "")
        return ""
