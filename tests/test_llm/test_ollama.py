"""Tests for context_hygiene.llm.ollama."""

from __future__ import annotations

import httpx
import pytest
import respx

from context_hygiene.exceptions import LLMError
from context_hygiene.llm.ollama import OllamaProvider, extract_json


class TestOllamaProvider:
    def test_init_defaults(self):
        p = OllamaProvider()
        assert p._model == "llama3.2"

    def test_init_custom(self):
        p = OllamaProvider(base_url="http://custom:1234", model="deepseek", timeout=30)
        assert p._model == "deepseek"
        assert p._base_url == "http://custom:1234"

    @respx.mock
    def test_generate_success(self):
        respx.post("http://localhost:11434/api/generate").mock(
            return_value=httpx.Response(200, json={"response": "Hello from Ollama"})
        )
        p = OllamaProvider()
        result = p.generate("test prompt")
        assert result == "Hello from Ollama"

    @respx.mock
    def test_generate_with_system(self):
        route = respx.post("http://localhost:11434/api/generate").mock(
            return_value=httpx.Response(200, json={"response": "reply"})
        )
        p = OllamaProvider()
        p.generate("prompt", system="system instructions")
        assert route.called

    @respx.mock
    def test_generate_http_error(self):
        respx.post("http://localhost:11434/api/generate").mock(
            return_value=httpx.Response(500, text="Internal error")
        )
        p = OllamaProvider()
        with pytest.raises(LLMError, match="Ollama request failed"):
            p.generate("test")

    @respx.mock
    def test_generate_connection_error(self):
        respx.post("http://localhost:11434/api/generate").mock(
            side_effect=httpx.ConnectError("refused")
        )
        p = OllamaProvider()
        with pytest.raises(LLMError):
            p.generate("test")

    @respx.mock
    def test_generate_invalid_json(self):
        respx.post("http://localhost:11434/api/generate").mock(
            return_value=httpx.Response(200, text="not json")
        )
        p = OllamaProvider()
        with pytest.raises(LLMError, match="Invalid"):
            p.generate("test")

    @respx.mock
    def test_is_available_true(self):
        respx.get("http://localhost:11434/api/tags").mock(
            return_value=httpx.Response(200, json={"models": []})
        )
        p = OllamaProvider()
        assert p.is_available()

    @respx.mock
    def test_is_available_false(self):
        respx.get("http://localhost:11434/api/tags").mock(
            side_effect=httpx.ConnectError("refused")
        )
        p = OllamaProvider()
        assert not p.is_available()

    @respx.mock
    def test_is_available_server_error(self):
        respx.get("http://localhost:11434/api/tags").mock(return_value=httpx.Response(500))
        p = OllamaProvider()
        assert not p.is_available()

    def test_trailing_slash_stripped(self):
        p = OllamaProvider(base_url="http://localhost:11434/")
        assert p._base_url == "http://localhost:11434"

    @respx.mock
    def test_generate_missing_response_key(self):
        respx.post("http://localhost:11434/api/generate").mock(
            return_value=httpx.Response(200, json={"other": "data"})
        )
        p = OllamaProvider()
        result = p.generate("test")
        assert result == ""


class TestExtractJson:
    def test_direct_json(self):
        result = extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_markdown_fenced(self):
        result = extract_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_markdown_no_lang(self):
        result = extract_json('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_preamble_text(self):
        result = extract_json('Here is the JSON:\n\n{"key": "value"}\n\nThat is all.')
        assert result == {"key": "value"}

    def test_invalid_json(self):
        result = extract_json("no json here at all")
        assert result is None

    def test_nested_json(self):
        result = extract_json('{"outer": {"inner": 1}}')
        assert result == {"outer": {"inner": 1}}

    def test_empty_string(self):
        result = extract_json("")
        assert result is None

    def test_json_with_newlines(self):
        result = extract_json('{\n  "key": "value"\n}')
        assert result == {"key": "value"}
