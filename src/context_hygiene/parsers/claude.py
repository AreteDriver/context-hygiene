"""Claude export JSON parser."""

from __future__ import annotations

import json
from pathlib import Path

from context_hygiene.exceptions import ParseError
from context_hygiene.models import Role, Segment
from context_hygiene.parsers.base import BaseParser

_ROLE_MAP = {
    "human": Role.USER,
    "user": Role.USER,
    "assistant": Role.ASSISTANT,
    "system": Role.SYSTEM,
}


class ClaudeParser(BaseParser):
    """Parse Claude conversation export JSON."""

    def can_parse(self, file_path: Path) -> bool:
        if file_path.suffix.lower() != ".json":
            return False
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            # Claude exports have chat_messages or a list of messages with sender
            if isinstance(data, dict):
                return "chat_messages" in data or "messages" in data
            if isinstance(data, list) and data:
                return "sender" in data[0] or "role" in data[0]
        except (json.JSONDecodeError, OSError, KeyError, IndexError):
            pass
        return False

    def parse(self, file_path: Path) -> list[Segment]:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise ParseError(f"Failed to parse {file_path}: {e}") from e

        messages = self._extract_messages(data)
        segments: list[Segment] = []

        for idx, msg in enumerate(messages):
            role = self._map_role(msg)
            content = self._extract_content(msg)
            if content.strip():
                segments.append(Segment(index=idx, role=role, content=content))

        return segments

    @staticmethod
    def _extract_messages(data: dict | list) -> list[dict]:
        """Extract message list from various Claude export formats."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if "chat_messages" in data:
                return data["chat_messages"]
            if "messages" in data:
                return data["messages"]
        return []

    @staticmethod
    def _map_role(msg: dict) -> Role:
        sender = msg.get("sender", msg.get("role", "user")).lower()
        return _ROLE_MAP.get(sender, Role.USER)

    @staticmethod
    def _extract_content(msg: dict) -> str:
        """Extract text content from a message."""
        # Simple text field
        if "text" in msg:
            return msg["text"]
        if "content" in msg:
            content = msg["content"]
            if isinstance(content, str):
                return content
            # Content blocks (Claude API format)
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, str):
                        parts.append(block)
                    elif isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                return "\n".join(parts)
        return ""
