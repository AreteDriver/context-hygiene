"""Regression tests for non-positional segment IDs in duplicate detection."""

from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.models import Role, Segment


def test_non_contiguous_ids_find_prior_duplicate():
    text = "Preserve all cited source references in the final report."
    segments = [
        Segment(index=20, role=Role.USER, content=text),
        Segment(index=40, role=Role.USER, content="A distinct longer instruction for testing."),
        Segment(index=60, role=Role.USER, content=text),
    ]
    matches = [r for r in deadweight_fast(segments) if r.reason.startswith("exact duplicate")]
    assert len(matches) == 1
    assert matches[0].segment_index == 60
    assert matches[0].reason == "exact duplicate of segment 20"


def test_non_monotonic_ids_do_not_match_future_segment():
    text = "Keep original source materials intact during processing."
    segments = [
        Segment(index=99, role=Role.USER, content=text),
        Segment(index=1, role=Role.USER, content=text),
    ]
    matches = [r for r in deadweight_fast(segments) if r.reason.startswith("exact duplicate")]
    assert len(matches) == 1
    assert matches[0].segment_index == 1
    assert matches[0].reason == "exact duplicate of segment 99"


def test_short_duplicate_threshold_preserved():
    segments = [
        Segment(index=8, role=Role.USER, content="tiny"),
        Segment(index=9, role=Role.USER, content="tiny"),
    ]
    assert not any(r.reason.startswith("exact duplicate") for r in deadweight_fast(segments))
