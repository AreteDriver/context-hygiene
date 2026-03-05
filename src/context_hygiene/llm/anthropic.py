"""Anthropic LLM provider (optional dependency)."""

from __future__ import annotations

from context_hygiene.exceptions import LLMError
from context_hygiene.llm.base import BaseLLMProvider

_DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider (requires anthropic extra)."""

    def __init__(self, model: str = _DEFAULT_MODEL, api_key: str = "") -> None:
        self._model = model
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise LLMError(
                    "anthropic package not installed. "
                    "Install with: pip install context-hygiene[anthropic]"
                ) from e
            kwargs = {}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            self._client = anthropic.Anthropic(**kwargs)
        return self._client

    def generate(self, prompt: str, system: str = "") -> str:
        """Generate via Anthropic API."""
        client = self._get_client()
        try:
            kwargs: dict = {
                "model": self._model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            raise LLMError(f"Anthropic request failed: {e}") from e

    def is_available(self) -> bool:
        """Check if Anthropic API key is configured."""
        try:
            self._get_client()
            return True
        except LLMError:
            return False
