"""Base LLM provider ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> str:
        """Generate a text response from the LLM."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""
