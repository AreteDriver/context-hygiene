"""Anthropic LLM provider (optional dependency)."""

from __future__ import annotations

from context_hygiene.exceptions import LLMError
from context_hygiene.llm.base import BaseLLMProvider

_DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider (requires anthropic extra)."""

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        api_key: str = "",
        *,
        max_tokens: int = 4096,
        max_retries: int = 2,
    ) -> None:
        if max_tokens < 1:
            raise ValueError("max_tokens must be positive")
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self._model = model
        self._api_key = api_key
        self._max_tokens = max_tokens
        self._max_retries = max_retries
        self._client = None
        self._usage = {"input_tokens": 0, "output_tokens": 0, "requests": 0}

    @property
    def model_id(self) -> str:
        """Exact configured provider model identifier."""
        return self._model

    @property
    def usage(self) -> dict[str, int]:
        """Cumulative successful-request usage for the current analysis."""
        return dict(self._usage)

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise LLMError(
                    "anthropic package not installed. "
                    "Install with: pip install context-hygiene[anthropic]"
                ) from e
            kwargs = {"max_retries": self._max_retries}
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
                "max_tokens": self._max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            response = client.messages.create(**kwargs)
            usage = getattr(response, "usage", None)
            self._usage["requests"] += 1
            self._usage["input_tokens"] += int(getattr(usage, "input_tokens", 0))
            self._usage["output_tokens"] += int(getattr(usage, "output_tokens", 0))
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
