"""Tests for context_hygiene.analyzers.deadweight."""

from __future__ import annotations

from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.models import Role, Segment


class TestDeadweightFast:
    def test_empty(self):
        assert deadweight_fast([]) == []

    def test_ok_message(self):
        segs = [Segment(index=0, role=Role.USER, content="ok")]
        result = deadweight_fast(segs)
        assert len(result) == 1
        assert "acknowledgment" in result[0].reason

    def test_thanks_message(self):
        segs = [Segment(index=0, role=Role.USER, content="thanks")]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_sure_message(self):
        segs = [Segment(index=0, role=Role.USER, content="sure")]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_got_it(self):
        segs = [Segment(index=0, role=Role.USER, content="got it")]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_understood(self):
        segs = [Segment(index=0, role=Role.USER, content="understood")]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_filler_hmm(self):
        segs = [Segment(index=0, role=Role.USER, content="hmm")]
        result = deadweight_fast(segs)
        assert len(result) >= 1
        assert "filler" in result[0].reason

    def test_filler_um(self):
        segs = [Segment(index=0, role=Role.USER, content="um")]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_ellipsis(self):
        segs = [Segment(index=0, role=Role.USER, content="...")]
        result = deadweight_fast(segs)
        assert len(result) >= 1
        assert "ellipsis" in result[0].reason

    def test_assistant_preamble(self):
        segs = [
            Segment(
                index=0,
                role=Role.ASSISTANT,
                content="Sure, let me help.",
                token_estimate=8,
            )
        ]
        result = deadweight_fast(segs)
        assert len(result) >= 1
        assert "confirmation" in result[0].reason

    def test_assistant_long_not_deadweight(self):
        segs = [
            Segment(
                index=0,
                role=Role.ASSISTANT,
                content="Sure, " + "word " * 50,
                token_estimate=60,
            )
        ]
        result = deadweight_fast(segs)
        # Long assistant message shouldn't match preamble pattern
        assert all("confirmation" not in r.reason for r in result)

    def test_duplicate_detection(self):
        segs = [
            Segment(
                index=0,
                role=Role.USER,
                content="The same message repeated here",
                token_estimate=10,
            ),
            Segment(
                index=1,
                role=Role.USER,
                content="The same message repeated here",
                token_estimate=10,
            ),
        ]
        result = deadweight_fast(segs)
        assert any("duplicate" in r.reason for r in result)

    def test_empty_message(self):
        segs = [Segment(index=0, role=Role.USER, content="", token_estimate=0)]
        result = deadweight_fast(segs)
        assert any("empty" in r.reason for r in result)

    def test_real_content_not_deadweight(self):
        segs = [
            Segment(
                index=0,
                role=Role.USER,
                content="How do I implement a binary search tree?",
            )
        ]
        result = deadweight_fast(segs)
        assert result == []

    def test_tokens_recoverable(self):
        segs = [Segment(index=0, role=Role.USER, content="ok", token_estimate=5)]
        result = deadweight_fast(segs)
        assert result[0].tokens_recoverable == 5

    def test_great_message(self):
        segs = [Segment(index=0, role=Role.USER, content="great")]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_perfect_message(self):
        segs = [Segment(index=0, role=Role.USER, content="perfect")]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_yes_message(self):
        segs = [Segment(index=0, role=Role.USER, content="yes")]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_no_message(self):
        segs = [Segment(index=0, role=Role.USER, content="no")]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_certainly_assistant(self):
        segs = [
            Segment(
                index=0,
                role=Role.ASSISTANT,
                content="Certainly!",
                token_estimate=5,
            )
        ]
        result = deadweight_fast(segs)
        assert len(result) >= 1

    def test_short_duplicate_not_flagged(self):
        # Very short duplicates (<=5 tokens) should not be flagged
        segs = [
            Segment(index=0, role=Role.USER, content="hi", token_estimate=2),
            Segment(index=1, role=Role.USER, content="hi", token_estimate=2),
        ]
        result = deadweight_fast(segs)
        assert not any("duplicate" in r.reason for r in result)
