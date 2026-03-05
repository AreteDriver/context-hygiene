"""Base parser ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from context_hygiene.models import Segment


class BaseParser(ABC):
    """Abstract base class for conversation parsers."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""

    @abstractmethod
    def parse(self, file_path: Path) -> list[Segment]:
        """Parse a conversation file into segments."""
