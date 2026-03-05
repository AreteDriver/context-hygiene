"""Tests for context_hygiene.analyzers.staleness."""

from __future__ import annotations

from context_hygiene.analyzers.staleness import staleness_fast
from context_hygiene.models import Role, Segment


class TestStalenessFast:
    def test_empty_segments(self):
        assert staleness_fast([]) == []

    def test_single_segment(self):
        segs = [Segment(index=0, role=Role.USER, content="Hello")]
        results = staleness_fast(segs)
        assert len(results) == 1
        assert results[0].segment_index == 0

    def test_scores_between_0_and_1(self, sample_segments):
        results = staleness_fast(sample_segments)
        for r in results:
            assert 0.0 <= r.score <= 1.0

    def test_earlier_segments_more_stale(self):
        segs = [
            Segment(index=0, role=Role.USER, content="First message"),
            Segment(index=1, role=Role.ASSISTANT, content="Reply"),
            Segment(index=2, role=Role.USER, content="Second message"),
            Segment(index=3, role=Role.ASSISTANT, content="Final reply"),
        ]
        results = staleness_fast(segs)
        # First segment should score higher (more stale)
        assert results[0].score >= results[-1].score

    def test_scratch_that_pattern(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Use pip"),
            Segment(index=1, role=Role.USER, content="Scratch that, use poetry"),
        ]
        results = staleness_fast(segs)
        stale = results[1]
        assert stale.score > 0
        assert any("superseded" in r for r in stale.reasons)

    def test_nevermind_pattern(self):
        segs = [Segment(index=0, role=Role.USER, content="Never mind the previous")]
        results = staleness_fast(segs)
        assert results[0].score > 0

    def test_actually_pattern(self):
        segs = [Segment(index=0, role=Role.USER, content="Actually, do it differently")]
        results = staleness_fast(segs)
        assert results[0].score > 0

    def test_restart_pattern(self):
        segs = [Segment(index=0, role=Role.USER, content="Let me start over")]
        results = staleness_fast(segs)
        assert results[0].score > 0

    def test_from_scratch_pattern(self):
        segs = [Segment(index=0, role=Role.USER, content="Do it from scratch")]
        results = staleness_fast(segs)
        assert results[0].score > 0

    def test_outdated_pattern(self):
        segs = [Segment(index=0, role=Role.USER, content="This is outdated")]
        results = staleness_fast(segs)
        assert any("stale" in r for r in results[0].reasons)

    def test_error_pattern(self):
        segs = [
            Segment(
                index=0,
                role=Role.ASSISTANT,
                content="Traceback (most recent call last):\n  Error occurred",
            )
        ]
        results = staleness_fast(segs)
        assert results[0].score > 0
        assert any("error" in r for r in results[0].reasons)

    def test_short_mid_conversation(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Start"),
            Segment(index=1, role=Role.USER, content="ok"),
            Segment(index=2, role=Role.USER, content="Continue with more text here"),
        ]
        results = staleness_fast(segs)
        # "ok" is short and mid-conversation
        assert results[1].score > results[2].score

    def test_previously_pattern(self):
        segs = [
            Segment(
                index=0,
                role=Role.ASSISTANT,
                content="As I previously mentioned",
            )
        ]
        results = staleness_fast(segs)
        assert any("earlier" in r for r in results[0].reasons)

    def test_ignore_pattern(self):
        segs = [Segment(index=0, role=Role.USER, content="Ignore the above")]
        results = staleness_fast(segs)
        assert results[0].score > 0

    def test_disregard_pattern(self):
        segs = [Segment(index=0, role=Role.USER, content="Disregard that")]
        results = staleness_fast(segs)
        assert results[0].score > 0

    def test_score_capped_at_1(self):
        # Load up with all patterns
        segs = [
            Segment(
                index=0,
                role=Role.USER,
                content=(
                    "Scratch that, actually never mind. "
                    "Let me start over from scratch. "
                    "This is outdated and obsolete. "
                    "Previously mentioned. "
                    "Traceback Error Failed. "
                    "Ignore the above and disregard. "
                    "Correction update."
                ),
            )
        ]
        results = staleness_fast(segs)
        assert results[0].score <= 1.0

    def test_clean_conversation(self):
        segs = [
            Segment(index=0, role=Role.USER, content="How do I use Python?"),
            Segment(index=1, role=Role.ASSISTANT, content="Python is a language."),
        ]
        results = staleness_fast(segs)
        # Clean conversation should have low scores
        assert all(r.score < 0.5 for r in results)

    def test_reasons_populated(self, sample_segments):
        results = staleness_fast(sample_segments)
        scored = [r for r in results if r.score > 0]
        assert any(r.reasons for r in scored)
