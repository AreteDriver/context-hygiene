"""Controlled exact-duplicate detector benchmark.

Synthetic positive and negative controls, not a representative external corpus.
No claims about semantic equivalence or whether removal is safe.
"""

from __future__ import annotations

from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.models import Role, Segment

TEXT_A = "The build pipeline must retain its signed release artifacts for thirty days."
TEXT_B = "Every release must pass reproducibility checks before it can be distributed."
TEXT_C = "The build pipeline must retain its signed release artifacts for sixty days."


def _segments(*texts: str) -> list[Segment]:
    return [Segment(index=i, role=Role.SYSTEM, content=text) for i, text in enumerate(texts)]


def _duplicate_indices(*texts: str) -> set[int]:
    return {
        result.segment_index
        for result in deadweight_fast(_segments(*texts))
        if result.reason.startswith("exact duplicate of segment ")
    }


def test_true_exact_duplicate_is_detected() -> None:
    assert _duplicate_indices(TEXT_A, TEXT_B, TEXT_A) == {2}


def test_unique_sections_do_not_trigger() -> None:
    assert _duplicate_indices(TEXT_A, TEXT_B, TEXT_C) == set()


def test_near_duplicate_is_not_reported_as_exact() -> None:
    assert _duplicate_indices(TEXT_A, TEXT_C) == set()


def test_repeated_identical_content_reports_each_later_occurrence() -> None:
    assert _duplicate_indices(TEXT_A, TEXT_A, TEXT_A) == {1, 2}


def test_short_exact_duplicate_below_token_threshold_not_flagged() -> None:
    assert _duplicate_indices("hello", "hello") == set()
