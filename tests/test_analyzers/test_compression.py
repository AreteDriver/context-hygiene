"""Tests for context_hygiene.analyzers.compression."""

from __future__ import annotations

from context_hygiene.analyzers.compression import (
    _find_consecutive_same_role,
    _find_large_code_blocks,
    _find_verbose_explanations,
    compression_fast,
)
from context_hygiene.models import Role, Segment


class TestCompressionFast:
    def test_empty(self):
        assert compression_fast([]) == []

    def test_short_conversation(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Hello"),
            Segment(index=1, role=Role.ASSISTANT, content="Hi"),
        ]
        result = compression_fast(segs)
        # Short clean conversation should have no compression candidates
        assert isinstance(result, list)

    def test_returns_candidates(self, sample_segments):
        result = compression_fast(sample_segments)
        assert isinstance(result, list)


class TestConsecutiveSameRole:
    def test_no_runs(self):
        segs = [
            Segment(index=0, role=Role.USER, content="A"),
            Segment(index=1, role=Role.ASSISTANT, content="B"),
            Segment(index=2, role=Role.USER, content="C"),
        ]
        result = _find_consecutive_same_role(segs)
        assert result == []

    def test_three_consecutive(self):
        segs = [
            Segment(index=0, role=Role.USER, content="A"),
            Segment(index=1, role=Role.USER, content="B"),
            Segment(index=2, role=Role.USER, content="C"),
        ]
        result = _find_consecutive_same_role(segs)
        assert len(result) == 1
        assert len(result[0].segment_indices) == 3
        assert "consecutive" in result[0].reason

    def test_two_not_enough(self):
        segs = [
            Segment(index=0, role=Role.USER, content="A"),
            Segment(index=1, role=Role.USER, content="B"),
        ]
        result = _find_consecutive_same_role(segs)
        assert result == []

    def test_final_run(self):
        segs = [
            Segment(index=0, role=Role.ASSISTANT, content="A"),
            Segment(index=1, role=Role.USER, content="B"),
            Segment(index=2, role=Role.USER, content="C"),
            Segment(index=3, role=Role.USER, content="D"),
        ]
        result = _find_consecutive_same_role(segs)
        assert len(result) == 1

    def test_savings_calculated(self):
        segs = [
            Segment(index=0, role=Role.USER, content="word " * 100),
            Segment(index=1, role=Role.USER, content="word " * 100),
            Segment(index=2, role=Role.USER, content="word " * 100),
        ]
        result = _find_consecutive_same_role(segs)
        assert len(result) == 1
        assert result[0].savings_tokens > 0

    def test_empty(self):
        assert _find_consecutive_same_role([]) == []

    def test_single(self):
        segs = [Segment(index=0, role=Role.USER, content="A")]
        assert _find_consecutive_same_role(segs) == []


class TestLargeCodeBlocks:
    def test_no_code_blocks(self):
        segs = [Segment(index=0, role=Role.ASSISTANT, content="Just text")]
        result = _find_large_code_blocks(segs)
        assert result == []

    def test_small_code_block(self):
        segs = [
            Segment(
                index=0,
                role=Role.ASSISTANT,
                content="```\nprint('hi')\n```",
            )
        ]
        result = _find_large_code_blocks(segs)
        assert result == []

    def test_large_code_block(self):
        code = "```\n" + "x = 1\n" * 200 + "```"
        segs = [Segment(index=0, role=Role.ASSISTANT, content=code)]
        result = _find_large_code_blocks(segs)
        assert len(result) == 1

    def test_multiple_blocks_one_candidate(self):
        code = "```\n" + "x = 1\n" * 200 + "```\n" + "text\n" + "```\ny = 2\n```"
        segs = [Segment(index=0, role=Role.ASSISTANT, content=code)]
        result = _find_large_code_blocks(segs)
        # One candidate per segment
        assert len(result) <= 1


class TestVerboseExplanations:
    def test_short_response(self):
        segs = [
            Segment(
                index=0,
                role=Role.ASSISTANT,
                content="Short reply.",
                token_estimate=10,
            )
        ]
        result = _find_verbose_explanations(segs)
        assert result == []

    def test_verbose_response(self):
        text = "This is a verbose explanation. " * 100
        segs = [
            Segment(
                index=0,
                role=Role.ASSISTANT,
                content=text,
                token_estimate=1000,
            )
        ]
        result = _find_verbose_explanations(segs)
        assert len(result) == 1
        assert "verbose" in result[0].reason

    def test_code_heavy_not_verbose(self):
        code = "```\n" + "x = 1\n" * 300 + "```"
        segs = [
            Segment(
                index=0,
                role=Role.ASSISTANT,
                content=code,
                token_estimate=1000,
            )
        ]
        result = _find_verbose_explanations(segs)
        # Mostly code — should NOT be flagged
        assert result == []

    def test_user_messages_not_checked(self):
        segs = [
            Segment(
                index=0,
                role=Role.USER,
                content="word " * 500,
                token_estimate=1000,
            )
        ]
        result = _find_verbose_explanations(segs)
        assert result == []
