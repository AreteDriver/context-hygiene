"""Tests for context_hygiene.llm.anthropic."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from context_hygiene.exceptions import LLMError
from context_hygiene.llm.anthropic import AnthropicProvider


class TestAnthropicProvider:
    def test_init_defaults(self):
        p = AnthropicProvider()
        assert p._model == "claude-sonnet-4-6"
        assert p._client is None

    def test_init_custom(self):
        p = AnthropicProvider(
            model="claude-haiku-4-5-20251001",
            api_key="test",
            max_tokens=1024,
            max_retries=0,
        )
        assert p._model == "claude-haiku-4-5-20251001"
        assert p._api_key == "test"
        assert p._max_tokens == 1024
        assert p._max_retries == 0

    def test_get_client_no_anthropic(self):
        p = AnthropicProvider()
        with (
            patch.dict("sys.modules", {"anthropic": None}),
            pytest.raises(LLMError, match="not installed"),
        ):
            p._get_client()

    def test_get_client_with_mock(self):
        mock_anthropic = MagicMock()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            p = AnthropicProvider(api_key="test-key")
            p._client = None  # Reset
            client = p._get_client()
            assert client is not None
            mock_anthropic.Anthropic.assert_called_once_with(api_key="test-key", max_retries=2)

    def test_get_client_cached(self):
        p = AnthropicProvider()
        p._client = MagicMock()
        assert p._get_client() is p._client

    def test_generate_success(self):
        mock_response = SimpleNamespace(
            content=[SimpleNamespace(text="Hello from Claude")],
            usage=SimpleNamespace(input_tokens=12, output_tokens=7),
        )
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        p = AnthropicProvider()
        p._client = mock_client
        result = p.generate("test prompt")
        assert result == "Hello from Claude"
        assert p.usage == {"input_tokens": 12, "output_tokens": 7, "requests": 1}
        assert p.model_id == "claude-sonnet-4-6"
        assert mock_client.messages.create.call_args.kwargs["max_tokens"] == 4096

    def test_invalid_limits_rejected(self):
        with pytest.raises(ValueError, match="max_tokens"):
            AnthropicProvider(max_tokens=0)
        with pytest.raises(ValueError, match="max_retries"):
            AnthropicProvider(max_retries=-1)

    def test_generate_with_system(self):
        mock_response = SimpleNamespace(content=[SimpleNamespace(text="reply")])
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        p = AnthropicProvider()
        p._client = mock_client
        p.generate("prompt", system="be helpful")
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "be helpful"

    def test_generate_error(self):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")

        p = AnthropicProvider()
        p._client = mock_client
        with pytest.raises(LLMError, match="Anthropic request failed"):
            p.generate("test")

    def test_is_available_true(self):
        p = AnthropicProvider()
        p._client = MagicMock()
        assert p.is_available()

    def test_is_available_false(self):
        p = AnthropicProvider()
        with patch.dict("sys.modules", {"anthropic": None}):
            assert not p.is_available()
