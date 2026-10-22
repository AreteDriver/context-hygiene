"""Synthetic tests for structured, non-authorizing duplicate evidence."""

import hashlib

from context_hygiene.evidence import DuplicateEvidence, review_duplicate_evidence
from context_hygiene.models import Role, Segment
from context_hygiene.safety import Actionability

TEXT = "Retain the original citations and references when summarizing this document."


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def pair(role=Role.USER):
    return [
        Segment(index=40, role=role, content=TEXT),
        Segment(index=5, role=role, content=TEXT),
    ]


def evidence(**changes):
    values = {
        "candidate_index": 5,
        "earlier_index": 40,
        "role": "user",
        "content_sha256": digest(TEXT),
    }
    values.update(changes)
    return DuplicateEvidence(**values)


def test_verified_pair_still_cannot_mutate():
    result = review_duplicate_evidence(pair(), evidence())
    assert result.identity_verified
    assert result.exact_content_verified
    assert result.dependencies_resolved
    assert result.decision.disposition is Actionability.INSUFFICIENT_EVIDENCE
    assert result.decision.authorized_to_mutate is False


def test_wrong_digest_fails_closed():
    result = review_duplicate_evidence(pair(), evidence(content_sha256=digest("other")))
    assert not result.exact_content_verified
    assert result.decision.disposition is Actionability.INSUFFICIENT_EVIDENCE


def test_reversed_order_fails_closed():
    result = review_duplicate_evidence(pair(), evidence(candidate_index=40, earlier_index=5))
    assert not result.identity_verified


def test_duplicate_segment_ids_fail_closed():
    segments = pair() + [Segment(index=5, role=Role.USER, content=TEXT)]
    result = review_duplicate_evidence(segments, evidence())
    assert not result.identity_verified
    assert not result.exact_content_verified


def test_cross_role_echo_fails_closed():
    segments = pair()
    segments[1] = Segment(index=5, role=Role.ASSISTANT, content=TEXT)
    result = review_duplicate_evidence(segments, evidence())
    assert not result.exact_content_verified


def test_system_role_remains_protected():
    result = review_duplicate_evidence(
        pair(Role.SYSTEM), evidence(role="system")
    )
    assert result.exact_content_verified
    assert result.decision.disposition is Actionability.PROTECTED


def test_unresolved_or_ambiguous_reference_is_not_resolved():
    result = review_duplicate_evidence(pair(), evidence(referenced_indices=(999,)))
    assert not result.dependencies_resolved
    assert not result.decision.authorized_to_mutate


def test_supplied_reference_list_does_not_prove_dependency_review():
    result = review_duplicate_evidence(pair(), evidence(referenced_indices=(40,)))
    assert result.dependencies_resolved
    assert result.decision.disposition is Actionability.INSUFFICIENT_EVIDENCE
