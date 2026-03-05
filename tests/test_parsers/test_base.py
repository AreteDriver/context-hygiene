"""Tests for context_hygiene.parsers.base."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_hygiene.parsers.base import BaseParser


class TestBaseParser:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseParser()

    def test_subclass_must_implement(self):
        class IncompleteParser(BaseParser):
            pass

        with pytest.raises(TypeError):
            IncompleteParser()

    def test_complete_subclass(self):
        class GoodParser(BaseParser):
            def can_parse(self, file_path: Path) -> bool:
                return True

            def parse(self, file_path: Path) -> list:
                return []

        p = GoodParser()
        assert p.can_parse(Path("test.md"))
        assert p.parse(Path("test.md")) == []
