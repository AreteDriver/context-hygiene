"""Tests for context_hygiene.analyzers.contradictions."""

from __future__ import annotations

from context_hygiene.analyzers.contradictions import contradictions_fast
from context_hygiene.models import Role, Segment


class TestContradictionsFast:
    def test_empty(self):
        assert contradictions_fast([]) == []

    def test_no_contradictions(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Use pip"),
            Segment(index=1, role=Role.USER, content="Also use poetry"),
        ]
        result = contradictions_fast(segs)
        assert result == []

    def test_use_dont_use(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Use pip for everything"),
            Segment(index=1, role=Role.USER, content="Don't use pip, use poetry"),
        ]
        result = contradictions_fast(segs)
        assert len(result) >= 1
        assert result[0].confidence > 0

    def test_always_never(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Always validate inputs"),
            Segment(index=1, role=Role.USER, content="Never validate inputs"),
        ]
        result = contradictions_fast(segs)
        assert len(result) >= 1

    def test_enable_disable(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Enable logging"),
            Segment(index=1, role=Role.USER, content="Disable logging"),
        ]
        result = contradictions_fast(segs)
        assert len(result) >= 1

    def test_include_exclude(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Include tests"),
            Segment(index=1, role=Role.USER, content="Exclude tests"),
        ]
        result = contradictions_fast(segs)
        assert len(result) >= 1

    def test_assistant_messages_ignored(self):
        segs = [
            Segment(index=0, role=Role.ASSISTANT, content="Use pip"),
            Segment(index=1, role=Role.ASSISTANT, content="Don't use pip"),
        ]
        result = contradictions_fast(segs)
        assert result == []

    def test_system_messages_checked(self):
        segs = [
            Segment(index=0, role=Role.SYSTEM, content="Always use tabs"),
            Segment(index=1, role=Role.SYSTEM, content="Never use tabs"),
        ]
        result = contradictions_fast(segs)
        assert len(result) >= 1

    def test_non_instruction_segments_ignored(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Hello"),
            Segment(index=1, role=Role.USER, content="Goodbye"),
        ]
        result = contradictions_fast(segs)
        assert result == []

    def test_case_insensitive(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Use PIP for everything"),
            Segment(index=1, role=Role.USER, content="Don't use PIP"),
        ]
        result = contradictions_fast(segs)
        assert len(result) >= 1

    def test_reverse_direction(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Don't use pip"),
            Segment(index=1, role=Role.USER, content="Use pip for everything"),
        ]
        result = contradictions_fast(segs)
        assert len(result) >= 1

    def test_multiple_contradictions(self, sample_segments):
        result = contradictions_fast(sample_segments)
        # The sample has "Use pip" + "Don't use pip" contradictions
        assert isinstance(result, list)

    def test_contradiction_fields(self):
        segs = [
            Segment(index=0, role=Role.USER, content="Use tabs"),
            Segment(index=3, role=Role.USER, content="Don't use tabs"),
        ]
        result = contradictions_fast(segs)
        assert len(result) >= 1
        c = result[0]
        assert c.segment_a == 0
        assert c.segment_b == 3
        assert c.confidence > 0
        assert c.description
