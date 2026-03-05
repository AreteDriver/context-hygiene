"""Tests for context_hygiene.models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from context_hygiene.models import (
    AnalysisMode,
    AuditSummary,
    CompressionCandidate,
    Contradiction,
    DeadweightResult,
    Grade,
    HygieneReport,
    Role,
    Segment,
    StalenessResult,
    estimate_tokens,
)


class TestRole:
    def test_values(self):
        assert Role.USER == "user"
        assert Role.ASSISTANT == "assistant"
        assert Role.SYSTEM == "system"

    def test_str(self):
        assert str(Role.USER) == "user"


class TestGrade:
    def test_all_grades(self):
        for g in ["A", "B", "C", "D", "F"]:
            assert Grade(g) is not None

    def test_comparison(self):
        assert Grade.A == "A"
        assert Grade.F == "F"


class TestAnalysisMode:
    def test_values(self):
        assert AnalysisMode.FAST == "fast"
        assert AnalysisMode.DEEP == "deep"


class TestSegment:
    def test_creation(self):
        seg = Segment(index=0, role=Role.USER, content="Hello world")
        assert seg.index == 0
        assert seg.role == Role.USER
        assert seg.content == "Hello world"
        assert seg.token_estimate > 0

    def test_auto_token_estimate(self):
        seg = Segment(index=0, role=Role.USER, content="one two three four five")
        assert seg.token_estimate >= 5

    def test_explicit_token_estimate(self):
        seg = Segment(index=0, role=Role.USER, content="hello", token_estimate=42)
        assert seg.token_estimate == 42

    def test_empty_content(self):
        seg = Segment(index=0, role=Role.USER, content="")
        assert seg.token_estimate == 0

    def test_timestamp(self):
        now = datetime.now(timezone.utc)
        seg = Segment(index=0, role=Role.USER, content="test", timestamp=now)
        assert seg.timestamp == now

    def test_no_timestamp(self):
        seg = Segment(index=0, role=Role.USER, content="test")
        assert seg.timestamp is None


class TestStalenessResult:
    def test_creation(self):
        r = StalenessResult(segment_index=0, score=0.5, reasons=["stale"])
        assert r.segment_index == 0
        assert r.score == 0.5
        assert r.reasons == ["stale"]

    def test_defaults(self):
        r = StalenessResult(segment_index=0)
        assert r.score == 0.0
        assert r.reasons == []


class TestContradiction:
    def test_creation(self):
        c = Contradiction(segment_a=1, segment_b=3, description="conflicting", confidence=0.8)
        assert c.segment_a == 1
        assert c.segment_b == 3
        assert c.confidence == 0.8


class TestDeadweightResult:
    def test_creation(self):
        d = DeadweightResult(segment_index=2, reason="ack", tokens_recoverable=5)
        assert d.segment_index == 2
        assert d.tokens_recoverable == 5


class TestCompressionCandidate:
    def test_creation(self):
        cc = CompressionCandidate(
            segment_indices=[0, 1, 2],
            current_tokens=300,
            estimated_compressed_tokens=100,
            reason="test",
        )
        assert cc.savings_tokens == 200
        assert cc.savings_pct == pytest.approx(66.67, abs=0.1)

    def test_zero_current_tokens(self):
        cc = CompressionCandidate(
            segment_indices=[0], current_tokens=0, estimated_compressed_tokens=0
        )
        assert cc.savings_pct == 0.0

    def test_defaults(self):
        cc = CompressionCandidate()
        assert cc.segment_indices == []
        assert cc.current_tokens == 0


class TestHygieneReport:
    def test_defaults(self):
        r = HygieneReport()
        assert r.total_segments == 0
        assert r.grade == Grade.A

    def test_compute_grade_a(self):
        r = HygieneReport(staleness_score=0.0, total_tokens=1000, tokens_recoverable=0)
        assert r.compute_grade() == Grade.A

    def test_compute_grade_b(self):
        r = HygieneReport(staleness_score=0.3, total_tokens=1000, tokens_recoverable=100)
        assert r.compute_grade() == Grade.B

    def test_compute_grade_c(self):
        r = HygieneReport(
            staleness_score=0.5,
            total_tokens=1000,
            tokens_recoverable=200,
            contradictions=[Contradiction(segment_a=0, segment_b=1, description="x")],
        )
        assert r.compute_grade() == Grade.C

    def test_compute_grade_d(self):
        r = HygieneReport(
            staleness_score=0.7,
            total_tokens=1000,
            tokens_recoverable=400,
            contradictions=[
                Contradiction(segment_a=0, segment_b=1, description="x"),
                Contradiction(segment_a=2, segment_b=3, description="y"),
            ],
        )
        assert r.compute_grade() == Grade.D

    def test_compute_grade_f(self):
        r = HygieneReport(
            staleness_score=1.0,
            total_tokens=1000,
            tokens_recoverable=800,
            contradictions=[
                Contradiction(segment_a=0, segment_b=1, description="x"),
                Contradiction(segment_a=2, segment_b=3, description="y"),
                Contradiction(segment_a=4, segment_b=5, description="z"),
            ],
        )
        assert r.compute_grade() == Grade.F

    def test_zero_total_tokens(self):
        r = HygieneReport(total_tokens=0, tokens_recoverable=0)
        assert r.compute_grade() == Grade.A

    def test_json_serialization(self):
        r = HygieneReport(file_path="test.md", total_segments=5)
        data = r.model_dump_json()
        assert "test.md" in data

    def test_mode(self):
        r = HygieneReport(mode=AnalysisMode.DEEP)
        assert r.mode == AnalysisMode.DEEP


class TestAuditSummary:
    def test_creation(self):
        s = AuditSummary(
            audit_id=1,
            file_path="test.md",
            grade=Grade.B,
            total_tokens=500,
        )
        assert s.audit_id == 1
        assert s.grade == Grade.B


class TestEstimateTokens:
    def test_empty(self):
        assert estimate_tokens("") == 0

    def test_single_word(self):
        assert estimate_tokens("hello") >= 1

    def test_sentence(self):
        tokens = estimate_tokens("this is a test sentence with several words")
        assert tokens >= 8

    def test_whitespace_only(self):
        assert estimate_tokens("   ") == 0
