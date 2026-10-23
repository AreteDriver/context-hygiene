"""Structured evidence stays conservative across legacy and adversarial inputs."""

import pytest

from context_hygiene.advisories import safety_advisories
from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.models import DeadweightResult, HygieneReport, Role, Segment

TEXT = "Preserve original citations and reference identifiers in every final report."


def pair():
    return [Segment(index=i, role=Role.USER, content=TEXT) for i in (10, 90)]


def test_structured_reference_survives_changed_reason_and_json_roundtrip():
    segments = pair()
    finding = deadweight_fast(segments)[0]
    finding.reason = "localized display text"
    finding = DeadweightResult.model_validate_json(finding.model_dump_json())
    advisory = safety_advisories(segments, [finding])[0]
    assert advisory["provenance"] == {
        "identity_verified": True,
        "exact_content_verified": True,
    }
    assert advisory["dependencies"]["review_status"] == "unknown"
    assert advisory["disposition"] == "insufficient_evidence"
    assert advisory["authorized_to_mutate"] is False
    report = HygieneReport(safety_advisories=[advisory])
    assert HygieneReport.model_validate_json(report.model_dump_json()) == report


def test_legacy_reason_does_not_supply_evidence():
    finding = DeadweightResult.model_validate(
        {
            "segment_index": 90,
            "reason": "exact duplicate of segment 10",
            "tokens_recoverable": 8,
        }
    )
    advisory = safety_advisories(pair(), [finding])[0]
    assert not advisory["provenance"]["exact_content_verified"]
    assert advisory["duplicate_reference"] is None
    assert HygieneReport.model_validate({"deadweight": [finding]}).safety_advisories == []


@pytest.mark.parametrize("mode", ["digest", "missing", "ambiguous", "role", "order"])
def test_invalid_structured_provenance_fails_closed(mode):
    segments = pair()
    finding = deadweight_fast(segments)[0]
    if mode == "digest":
        finding.duplicate_reference.content_sha256 = "invalid"
    elif mode == "missing":
        finding.duplicate_reference.earlier_index = 999
    elif mode == "ambiguous":
        segments.append(segments[0])
    elif mode == "role":
        segments[1].role = Role.ASSISTANT
    else:
        segments.reverse()
    advisory = safety_advisories(segments, [finding])[0]
    assert not advisory["provenance"]["exact_content_verified"]
    assert advisory["disposition"] == "insufficient_evidence"
    assert advisory["authorized_to_mutate"] is False


@pytest.mark.parametrize("references", [[999], [10, 10]])
def test_unresolved_or_ambiguous_dependency_evidence(references):
    segments = pair()
    finding = deadweight_fast(segments)[0]
    finding.duplicate_reference.referenced_indices = references
    advisory = safety_advisories(segments, [finding])[0]
    assert not advisory["dependencies"]["references_resolved"]
    assert advisory["dependencies"]["review_status"] == "unknown"
    assert advisory["disposition"] == "insufficient_evidence"
    assert advisory["authorized_to_mutate"] is False
