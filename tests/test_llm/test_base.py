"""Tests for context_hygiene.llm.base."""

from __future__ import annotations

import pytest

from context_hygiene.llm.base import BaseLLMProvider


class TestBaseLLMProvider:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseLLMProvider()

    def test_subclass_must_implement(self):
        class IncompleteProvider(BaseLLMProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_complete_subclass(self):
        class GoodProvider(BaseLLMProvider):
            def generate(self, prompt: str, system: str = "") -> str:
                return "ok"

            def is_available(self) -> bool:
                return True

        p = GoodProvider()
        assert p.generate("test") == "ok"
        assert p.is_available()
