"""Advisory reporting never upgrades detector findings to removal permission."""

from context_hygiene.advisories import safety_advisories
from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.cli import _run_analysis
from context_hygiene.models import Role, Segment

TEXT = "Preserve all original citations and reference identifiers in the final report."


def test_report_contains_fail_closed_duplicate_advisory():
    segments = [
        Segment(index=10, role=Role.USER, content=TEXT),
        Segment(index=90, role=Role.USER, content=TEXT),
    ]
    report = _run_analysis("synthetic.md", segments)
    matches = [
        item
        for item in report.safety_advisories
        if item["finding_reason"].startswith("exact duplicate")
    ]
    assert len(matches) == 1
    assert matches[0]["segment_index"] == 90
    assert matches[0]["disposition"] == "insufficient_evidence"
    assert matches[0]["authorized_to_mutate"] is False
    assert "safety_advisories" in report.model_dump(mode="json")


def test_system_instruction_is_protected():
    segments = [
        Segment(index=1, role=Role.SYSTEM, content=TEXT),
        Segment(index=2, role=Role.SYSTEM, content=TEXT),
    ]
    advisories = safety_advisories(segments, deadweight_fast(segments))
    assert len(advisories) == 1
    assert advisories[0]["disposition"] == "protected"
    assert advisories[0]["authorized_to_mutate"] is False


def test_ambiguous_ids_fail_closed():
    segments = [
        Segment(index=5, role=Role.SYSTEM, content=TEXT),
        Segment(index=5, role=Role.USER, content=TEXT),
    ]
    advisories = safety_advisories(segments, deadweight_fast(segments))
    assert all(item["disposition"] == "insufficient_evidence" for item in advisories)
    assert all(item["authorized_to_mutate"] is False for item in advisories)


def test_nonduplicate_finding_is_not_exact_match():
    segments = [Segment(index=7, role=Role.USER, content="okay")]
    advisories = safety_advisories(segments, deadweight_fast(segments))
    assert len(advisories) == 1
    assert advisories[0]["disposition"] == "insufficient_evidence"
