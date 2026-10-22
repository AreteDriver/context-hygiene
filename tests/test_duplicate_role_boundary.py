"""Duplicate-detection regression tests for conversational role boundaries."""

from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.models import Role, Segment


TEXT = "Preserve the full original source reference in the final report."


def duplicate_findings(segments):
    return [
        finding
        for finding in deadweight_fast(segments)
        if finding.reason.startswith("exact duplicate of segment ")
    ]


def test_cross_role_echo_is_not_duplicate():
    segments = [
        Segment(index=0, role=Role.ASSISTANT, content=TEXT),
        Segment(index=1, role=Role.USER, content=TEXT),
    ]
    assert duplicate_findings(segments) == []


def test_same_role_duplicate_still_detected():
    segments = [
        Segment(index=10, role=Role.USER, content=TEXT),
        Segment(index=40, role=Role.ASSISTANT, content=TEXT),
        Segment(index=90, role=Role.USER, content=TEXT),
    ]
    matches = duplicate_findings(segments)
    assert len(matches) == 1
    assert matches[0].segment_index == 90
    assert matches[0].reason == "exact duplicate of segment 10"


def test_system_and_user_instructions_are_not_interchangeable():
    segments = [
        Segment(index=1, role=Role.SYSTEM, content=TEXT),
        Segment(index=2, role=Role.USER, content=TEXT),
    ]
    assert duplicate_findings(segments) == []
