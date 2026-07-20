"""Generic markdown/text conversation parser.

Handles:
1. Conversation files with explicit role markers (## User, **Assistant**, etc.)
2. AI instruction files (CLAUDE.md, AGENTS.md) — splits by markdown headers
   into SYSTEM segments when no role markers are detected.
"""

from __future__ import annotations

import re
from pathlib import Path

from context_hygiene.exceptions import ParseError
from context_hygiene.models import Role, Segment
from context_hygiene.parsers.base import BaseParser

_I = re.IGNORECASE
_ASST = r"assistant|ai|claude|chatgpt|gpt|codex"

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

# Detect markdown headers for AI instruction file splitting
_HEADER_RE = re.compile(r"^(#{1,6}\s+.+)$", re.MULTILINE)


class GenericParser(BaseParser):
    """Parse plain text, markdown conversations, or AI instruction files."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in {".md", ".txt", ".text", ""}

    def parse(self, file_path: Path) -> list[Segment]:
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            raise ParseError(f"Failed to read {file_path}: {e}") from e

        if not text.strip():
            return []

        # First pass: try role-based parsing
        segments = self._parse_role_based(text)

        # If no role markers found, try section-based parsing (AI instruction files)
        if not segments or self._all_system_no_markers(text, segments):
            section_segments = self._parse_section_based(text)
            if section_segments:
                return section_segments

        return segments

    def _parse_role_based(self, text: str) -> list[Segment]:
        """Parse text with explicit User/Assistant/System role markers."""
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

    def _all_system_no_markers(self, text: str, segments: list[Segment]) -> bool:
        """Check if the parsed result is a single SYSTEM segment with no role markers."""
        if len(segments) != 1:
            return False
        if segments[0].role != Role.SYSTEM:
            return False
        # Make sure there were actually no role markers in the original text
        return all(self._detect_role(line) is None for line in text.splitlines())

    def _parse_section_based(self, text: str) -> list[Segment]:
        """Parse AI instruction files by splitting on markdown headers.

        Each top-level section becomes a SYSTEM segment. This allows the
        analyzer to detect stale sections, contradictions between rules, and
        compression opportunities within CLAUDE.md / AGENTS.md files.
        """
        lines = text.splitlines()
        if not lines:
            return []

        # Quick check: does this file have markdown headers?
        has_headers = any(_HEADER_RE.match(line.strip()) for line in lines)
        if not has_headers:
            return []

        segments: list[Segment] = []
        current_lines: list[str] = []
        idx = 0

        for line in lines:
            stripped = line.strip()
            if _HEADER_RE.match(stripped):
                # Save previous section
                if current_lines:
                    content = "\n".join(current_lines).strip()
                    if content:
                        segments.append(Segment(index=idx, role=Role.SYSTEM, content=content))
                        idx += 1
                current_lines = [line]
            else:
                current_lines.append(line)

        # Final section
        if current_lines:
            content = "\n".join(current_lines).strip()
            if content:
                segments.append(Segment(index=idx, role=Role.SYSTEM, content=content))

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
