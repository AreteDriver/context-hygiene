"""Generic markdown/text conversation parser."""

from __future__ import annotations

import re
from pathlib import Path

from context_hygiene.exceptions import ParseError
from context_hygiene.models import Role, Segment
from context_hygiene.parsers.base import BaseParser

_I = re.IGNORECASE
_ASST = r"assistant|ai|claude|chatgpt|gpt"

# Patterns for detecting role markers in markdown
_ROLE_PATTERNS = [
    (re.compile(r"^#{1,3}\s*(user|human)\s*:?\s*$", _I), Role.USER),
    (re.compile(rf"^#{{1,3}}\s*({_ASST})\s*:?\s*$", _I), Role.ASSISTANT),
    (re.compile(r"^#{1,3}\s*(system)\s*:?\s*$", _I), Role.SYSTEM),
    (re.compile(r"^\*\*(user|human)\*\*\s*:?\s*$", _I), Role.USER),
    (re.compile(rf"^\*\*({_ASST})\*\*\s*:?\s*$", _I), Role.ASSISTANT),
    (re.compile(r"^\*\*(system)\*\*\s*:?\s*$", _I), Role.SYSTEM),
    (re.compile(r"^(user|human)\s*:\s*", _I), Role.USER),
    (re.compile(rf"^({_ASST})\s*:\s*", _I), Role.ASSISTANT),
    (re.compile(r"^(system)\s*:\s*", _I), Role.SYSTEM),
]


class GenericParser(BaseParser):
    """Parse plain text or markdown conversations."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in {".md", ".txt", ".text", ""}

    def parse(self, file_path: Path) -> list[Segment]:
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            raise ParseError(f"Failed to read {file_path}: {e}") from e

        if not text.strip():
            return []

        segments: list[Segment] = []
        current_role: Role | None = None
        current_lines: list[str] = []
        idx = 0

        for line in text.splitlines():
            detected_role = self._detect_role(line)
            if detected_role is not None:
                # Save previous segment
                if current_role is not None and current_lines:
                    content = "\n".join(current_lines).strip()
                    if content:
                        segments.append(Segment(index=idx, role=current_role, content=content))
                        idx += 1
                current_role = detected_role
                current_lines = []
                # Check if the line has inline content after the role marker
                inline = self._extract_inline_content(line)
                if inline:
                    current_lines.append(inline)
            elif current_role is not None:
                current_lines.append(line)
            else:
                # Lines before any role marker — treat as system
                current_role = Role.SYSTEM
                current_lines.append(line)

        # Final segment
        if current_role is not None and current_lines:
            content = "\n".join(current_lines).strip()
            if content:
                segments.append(Segment(index=idx, role=current_role, content=content))

        return segments

    @staticmethod
    def _detect_role(line: str) -> Role | None:
        stripped = line.strip()
        if not stripped:
            return None
        for pattern, role in _ROLE_PATTERNS:
            if pattern.match(stripped):
                return role
        return None

    @staticmethod
    def _extract_inline_content(line: str) -> str:
        """Extract content after a role marker like 'User: hello'."""
        stripped = line.strip()
        for pattern, _ in _ROLE_PATTERNS:
            m = pattern.match(stripped)
            if m:
                after = stripped[m.end() :].strip()
                return after
        return ""
