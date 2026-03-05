"""Tests for the cleaner / pruning engine."""

from __future__ import annotations

from datetime import datetime, timezone

from context_hygiene.cleaner import PruningPlan, build_pruning_plan, segments_to_markdown
from context_hygiene.models import (
    DeadweightResult,
    HygieneReport,
    Role,
    Segment,
    StalenessResult,
)


def _seg(index: int, content: str = "hello world", role: Role = Role.USER) -> Segment:
    return Segment(index=index, role=role, content=content, token_estimate=10)


def _report(
    deadweight: list[DeadweightResult] | None = None,
    staleness: list[StalenessResult] | None = None,
) -> HygieneReport:
    return HygieneReport(
        file_path="test.md",
        analyzed_at=datetime.now(timezone.utc),
        deadweight=deadweight or [],
        staleness_results=staleness or [],
    )


class TestPruningPlan:
    def test_empty_report(self):
        segments = [_seg(0), _seg(1), _seg(2)]
        plan = PruningPlan(_report(), segments)
        assert plan.segments_to_remove == 0
        assert plan.segments_to_keep == 3
        assert plan.apply() == segments

    def test_removes_deadweight(self):
        dw = [DeadweightResult(segment_index=1, reason="filler", tokens_recoverable=10)]
        segments = [_seg(0), _seg(1), _seg(2)]
        plan = PruningPlan(_report(deadweight=dw), segments)
        assert plan.segments_to_remove == 1
        assert plan.segments_to_keep == 2
        result = plan.apply()
        assert [s.index for s in result] == [0, 2]

    def test_removes_stale_above_threshold(self):
        staleness = [
            StalenessResult(segment_index=0, score=0.3, reasons=["low"]),
            StalenessResult(segment_index=1, score=0.8, reasons=["high"]),
            StalenessResult(segment_index=2, score=0.61, reasons=["above"]),
        ]
        segments = [_seg(0), _seg(1), _seg(2)]
        plan = PruningPlan(_report(staleness=staleness), segments)
        assert plan.segments_to_remove == 2
        result = plan.apply()
        assert [s.index for s in result] == [0]

    def test_stale_at_threshold_not_removed(self):
        staleness = [StalenessResult(segment_index=0, score=0.6, reasons=["exact"])]
        segments = [_seg(0)]
        plan = PruningPlan(_report(staleness=staleness), segments)
        assert plan.segments_to_remove == 0

    def test_combined_deadweight_and_staleness(self):
        dw = [DeadweightResult(segment_index=0, reason="ack", tokens_recoverable=5)]
        staleness = [StalenessResult(segment_index=2, score=0.9, reasons=["old"])]
        segments = [_seg(0), _seg(1), _seg(2)]
        plan = PruningPlan(_report(deadweight=dw, staleness=staleness), segments)
        assert plan.segments_to_remove == 2
        result = plan.apply()
        assert [s.index for s in result] == [1]

    def test_overlap_deadweight_and_staleness(self):
        dw = [DeadweightResult(segment_index=1, reason="ack", tokens_recoverable=5)]
        staleness = [StalenessResult(segment_index=1, score=0.9, reasons=["old"])]
        segments = [_seg(0), _seg(1)]
        plan = PruningPlan(_report(deadweight=dw, staleness=staleness), segments)
        assert plan.segments_to_remove == 1

    def test_tokens_before_after(self):
        dw = [DeadweightResult(segment_index=1, reason="x", tokens_recoverable=10)]
        segments = [_seg(0), _seg(1), _seg(2)]
        plan = PruningPlan(_report(deadweight=dw), segments)
        assert plan.tokens_before == 30
        assert plan.tokens_after == 20
        assert plan.tokens_saved == 10

    def test_summary(self):
        dw = [DeadweightResult(segment_index=0, reason="x", tokens_recoverable=10)]
        segments = [_seg(0), _seg(1)]
        plan = PruningPlan(_report(deadweight=dw), segments)
        s = plan.summary()
        assert "remove 1/2" in s
        assert "Remove indices: [0]" in s

    def test_summary_no_removals(self):
        plan = PruningPlan(_report(), [_seg(0)])
        s = plan.summary()
        assert "remove 0/1" in s
        assert "Remove indices" not in s


class TestBuildPruningPlan:
    def test_builds_from_file(self, generic_file):
        report = _report()
        report.file_path = str(generic_file)
        plan = build_pruning_plan(report, str(generic_file))
        assert plan.segments_to_keep > 0


class TestSegmentsToMarkdown:
    def test_converts_segments(self):
        segments = [
            _seg(0, "Hello there", Role.USER),
            _seg(1, "Hi back", Role.ASSISTANT),
        ]
        md = segments_to_markdown(segments)
        assert "## User" in md
        assert "## Assistant" in md
        assert "Hello there" in md
        assert "Hi back" in md

    def test_empty_segments(self):
        md = segments_to_markdown([])
        assert md == ""
