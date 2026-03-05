"""Tests for deep (LLM-powered) analyzers."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from context_hygiene.analyzers.deep import (
    _format_segments,
    _load_prompt,
    compression_deep,
    contradictions_deep,
    deadweight_deep,
    staleness_deep,
)
from context_hygiene.exceptions import AnalysisError
from context_hygiene.models import Role, Segment


def _seg(index: int, content: str = "Test content", role: Role = Role.USER) -> Segment:
    return Segment(index=index, role=role, content=content, token_estimate=20)


def _mock_provider(response: str) -> MagicMock:
    provider = MagicMock()
    provider.generate.return_value = response
    return provider


class TestLoadPrompt:
    def test_loads_existing_prompt(self):
        text = _load_prompt("staleness")
        assert "{segments}" in text

    def test_missing_prompt_raises(self):
        with pytest.raises(AnalysisError, match="not found"):
            _load_prompt("nonexistent_prompt_xyz")


class TestFormatSegments:
    def test_formats_segments(self):
        segments = [_seg(0, "Hello"), _seg(1, "World", Role.ASSISTANT)]
        result = _format_segments(segments)
        assert "[Segment 0]" in result
        assert "[Segment 1]" in result
        assert "(user" in result
        assert "(assistant" in result

    def test_truncates_long_content(self):
        long = "x" * 600
        segments = [_seg(0, long)]
        result = _format_segments(segments)
        assert "truncated" in result


class TestStalenessDeep:
    def test_parses_response(self):
        response = json.dumps(
            {
                "results": [
                    {"segment_index": 0, "score": 0.5, "reasons": ["outdated"]},
                    {"segment_index": 1, "score": 0.2, "reasons": ["recent"]},
                ]
            }
        )
        provider = _mock_provider(response)
        results = staleness_deep([_seg(0), _seg(1)], provider)
        assert len(results) == 2
        assert results[0].score == 0.5
        assert results[0].reasons == ["outdated"]

    def test_bad_response_raises(self):
        provider = _mock_provider("not json at all")
        with pytest.raises(AnalysisError):
            staleness_deep([_seg(0)], provider)

    def test_missing_results_key_raises(self):
        provider = _mock_provider(json.dumps({"other": []}))
        with pytest.raises(AnalysisError):
            staleness_deep([_seg(0)], provider)


class TestContradictionsDeep:
    def test_parses_response(self):
        response = json.dumps(
            {
                "contradictions": [
                    {
                        "segment_a": 0,
                        "segment_b": 2,
                        "description": "conflicting",
                        "confidence": 0.9,
                    }
                ]
            }
        )
        provider = _mock_provider(response)
        results = contradictions_deep([_seg(0), _seg(1), _seg(2)], provider)
        assert len(results) == 1
        assert results[0].confidence == 0.9

    def test_bad_response_raises(self):
        provider = _mock_provider("garbage")
        with pytest.raises(AnalysisError):
            contradictions_deep([_seg(0)], provider)


class TestDeadweightDeep:
    def test_parses_response(self):
        response = json.dumps(
            {
                "deadweight": [
                    {"segment_index": 1, "reason": "filler", "tokens_recoverable": 15}
                ]
            }
        )
        provider = _mock_provider(response)
        results = deadweight_deep([_seg(0), _seg(1)], provider)
        assert len(results) == 1
        assert results[0].tokens_recoverable == 15

    def test_missing_key_raises(self):
        provider = _mock_provider(json.dumps({"wrong": []}))
        with pytest.raises(AnalysisError):
            deadweight_deep([_seg(0)], provider)


class TestCompressionDeep:
    def test_parses_response(self):
        response = json.dumps(
            {
                "candidates": [
                    {
                        "segment_indices": [0, 1],
                        "current_tokens": 200,
                        "estimated_compressed_tokens": 50,
                        "reason": "repetitive",
                    }
                ]
            }
        )
        provider = _mock_provider(response)
        results = compression_deep([_seg(0), _seg(1)], provider)
        assert len(results) == 1
        assert results[0].savings_tokens == 150

    def test_missing_key_raises(self):
        provider = _mock_provider(json.dumps({"other": []}))
        with pytest.raises(AnalysisError):
            compression_deep([_seg(0)], provider)

    def test_json_in_markdown_fence(self):
        data = {
            "candidates": [
                {
                    "segment_indices": [0],
                    "current_tokens": 100,
                    "estimated_compressed_tokens": 30,
                    "reason": "verbose",
                }
            ]
        }
        response = f"```json\n{json.dumps(data)}\n```"
        provider = _mock_provider(response)
        results = compression_deep([_seg(0)], provider)
        assert len(results) == 1
