"""Synthetic duplicate safety matrix; detector findings are not removal authorization."""

import pytest

from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.models import Role, Segment

LONG = "Preserve every original source citation when preparing the final report."
OTHER = "Check each source against the actual version of the document."


def duplicates(segments):
    return [
        (result.segment_index, result.reason)
        for result in deadweight_fast(segments)
        if result.reason.startswith("exact duplicate of segment ")
    ]


@pytest.mark.parametrize(
    ("roles", "texts", "expected"),
    [
        ([Role.USER, Role.USER], [LONG, LONG], [(90, "exact duplicate of segment 10")]),
        ([Role.USER, Role.ASSISTANT], [LONG, LONG], []),
        ([Role.SYSTEM, Role.USER], [LONG, LONG], []),
        ([Role.ASSISTANT, Role.ASSISTANT], [LONG, LONG], [(90, "exact duplicate of segment 10")]),
        ([Role.USER, Role.USER], [LONG, LONG + " "], []),
        ([Role.USER, Role.USER], [LONG, LONG.lower()], []),
        ([Role.USER, Role.USER], [LONG, OTHER], []),
        ([Role.USER, Role.USER], ["tiny", "tiny"], []),
    ],
)
def test_duplicate_boundaries(roles, texts, expected):
    segments = [
        Segment(index=index, role=role, content=text)
        for index, role, text in zip((10, 90), roles, texts)
    ]
    assert duplicates(segments) == expected


def test_triplicate_with_intervening_cross_role_echo():
    segments = [
        Segment(index=100, role=Role.USER, content=LONG),
        Segment(index=5, role=Role.ASSISTANT, content=LONG),
        Segment(index=300, role=Role.USER, content=LONG),
        Segment(index=2, role=Role.USER, content=LONG),
    ]
    assert duplicates(segments) == [
        (300, "exact duplicate of segment 100"),
        (2, "exact duplicate of segment 100"),
    ]


def test_repeated_system_instruction_is_a_finding_not_a_deletion():
    segments = [
        Segment(index=1, role=Role.SYSTEM, content=LONG),
        Segment(index=2, role=Role.SYSTEM, content=LONG),
    ]
    findings = deadweight_fast(segments)
    assert duplicates(segments) == [(2, "exact duplicate of segment 1")]
    assert all(not hasattr(finding, "delete") for finding in findings)
