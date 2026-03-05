"""OpenAI/ChatGPT export JSON parser."""

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
    "system": Role.SYSTEM,
    "tool": Role.SYSTEM,
}


class OpenAIParser(BaseParser):
    """Parse ChatGPT/OpenAI conversation export JSON."""

    def can_parse(self, file_path: Path) -> bool:
        if file_path.suffix.lower() != ".json":
            return False
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            # ChatGPT exports: list of conversations with "mapping" or "title"
            if isinstance(data, list) and data:
                first = data[0]
                return isinstance(first, dict) and ("mapping" in first or "title" in first)
            # Single conversation object
            if isinstance(data, dict) and "mapping" in data:
                return True
        except (json.JSONDecodeError, OSError, KeyError, IndexError):
            pass
        return False

    def parse(self, file_path: Path) -> list[Segment]:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise ParseError(f"Failed to parse {file_path}: {e}") from e

        conversations = data if isinstance(data, list) else [data]
        segments: list[Segment] = []
        idx = 0

        for conv in conversations:
            if not isinstance(conv, dict):
                continue
            messages = self._extract_messages(conv)
            for msg in messages:
                role = _ROLE_MAP.get(msg.get("role", "user"), Role.USER)
                content = self._extract_content(msg)
                if content.strip():
                    segments.append(Segment(index=idx, role=role, content=content))
                    idx += 1

        return segments

    @staticmethod
    def _extract_messages(conv: dict) -> list[dict]:
        """Extract messages from a ChatGPT conversation export."""
        # ChatGPT "mapping" format (nested nodes)
        if "mapping" in conv:
            messages = []
            for node in conv["mapping"].values():
                msg = node.get("message")
                if msg and msg.get("content") and msg.get("author"):
                    role = msg["author"].get("role", "user")
                    messages.append({"role": role, "content": msg["content"]})
            return messages
        # Simple messages list
        if "messages" in conv:
            return conv["messages"]
        return []

    @staticmethod
    def _extract_content(msg: dict) -> str:
        """Extract text from a ChatGPT message."""
        content = msg.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            parts = content.get("parts", [])
            return "\n".join(str(p) for p in parts if isinstance(p, str))
        if isinstance(content, list):
            return "\n".join(str(p) for p in content if isinstance(p, str))
        return ""
