"""Ollama LLM provider via httpx."""

from __future__ import annotations

import json
import re

import httpx

from context_hygiene.exceptions import LLMError
from context_hygiene.llm.base import BaseLLMProvider

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.2"


class OllamaProvider(BaseLLMProvider):
    """Local Ollama LLM provider."""

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        model: str = _DEFAULT_MODEL,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def generate(self, prompt: str, system: str = "") -> str:
        """Generate via Ollama API."""
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            resp = httpx.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except httpx.HTTPError as e:
            raise LLMError(f"Ollama request failed: {e}") from e
        except (json.JSONDecodeError, KeyError) as e:
            raise LLMError(f"Invalid Ollama response: {e}") from e

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            resp = httpx.get(f"{self._base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except httpx.HTTPError:
            return False


def extract_json(text: str) -> dict | None:
    """Extract JSON from LLM response with markdown fence fallback.

    Handles models that wrap JSON in preamble/trailing text.
    """
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    stripped = re.sub(r"```(?:json)?\s*", "", text).strip()
    stripped = re.sub(r"```\s*$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Regex fallback — extract outermost {...}
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None
