"""Auto-detect parser and factory."""

from __future__ import annotations

from pathlib import Path

from context_hygiene.exceptions import ParseError
from context_hygiene.models import Segment
from context_hygiene.parsers.base import BaseParser
from context_hygiene.parsers.claude import ClaudeParser
from context_hygiene.parsers.generic import GenericParser
from context_hygiene.parsers.openai import OpenAIParser

_PARSERS: list[BaseParser] = [
    ClaudeParser(),
    OpenAIParser(),
    GenericParser(),  # fallback — must be last
]


def detect_parser(file_path: Path) -> BaseParser:
    """Auto-detect the appropriate parser for a file."""
    for parser in _PARSERS:
        if parser.can_parse(file_path):
            return parser
    raise ParseError(f"No parser found for {file_path}")


def parse_file(file_path: Path) -> list[Segment]:
    """Parse a conversation file using auto-detection."""
    path = Path(file_path)
    if not path.exists():
        raise ParseError(f"File not found: {file_path}")
    parser = detect_parser(path)
    return parser.parse(path)
