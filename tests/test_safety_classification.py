"""Fail-closed tests for advisory-only context safety classification."""

import pytest

from context_hygiene.safety import Actionability, SafetyDecision, classify_duplicate


@pytest.mark.parametrize("role", [None, "", "developer", "tool", "SYSTEM"])
def test_unknown_role_fails_closed(role):
    decision = classify_duplicate(
        segment_index=1,
        role=role,
        exact_match=True,
        provenance_verified=True,
        dependency_reviewed=True,
    )
    assert decision.disposition is Actionability.INSUFFICIENT_EVIDENCE
    assert not decision.authorized_to_mutate


def test_system_role_is_protected_even_with_complete_evidence():
    decision = classify_duplicate(
        segment_index=1,
        role="system",
        exact_match=True,
        provenance_verified=True,
        dependency_reviewed=True,
    )
    assert decision.disposition is Actionability.PROTECTED
    assert not decision.authorized_to_mutate


@pytest.mark.parametrize(
    ("exact", "provenance", "dependencies"),
    [
        (False, True, True),
        (True, False, True),
        (True, True, False),
        (True, False, False),
    ],
)
def test_missing_evidence_never_becomes_actionable(exact, provenance, dependencies):
    decision = classify_duplicate(
        segment_index=8,
        role="user",
        exact_match=exact,
        provenance_verified=provenance,
        dependency_reviewed=dependencies,
    )
    assert decision.disposition is Actionability.INSUFFICIENT_EVIDENCE
    assert not decision.authorized_to_mutate


@pytest.mark.parametrize("role", ["user", "assistant"])
def test_complete_evidence_still_requires_human_review(role):
    decision = classify_duplicate(
        segment_index=5,
        role=role,
        exact_match=True,
        provenance_verified=True,
        dependency_reviewed=True,
    )
    assert decision.disposition is Actionability.REVIEW_REQUIRED
    assert not decision.authorized_to_mutate


def test_mutation_authorization_cannot_be_constructed():
    with pytest.raises(ValueError, match="not supported"):
        SafetyDecision(
            segment_index=1,
            disposition=Actionability.REVIEW_REQUIRED,
            rationale="test",
            authorized_to_mutate=True,
        )


def test_empty_rationale_rejected():
    with pytest.raises(ValueError, match="nonempty rationale"):
        SafetyDecision(
            segment_index=1,
            disposition=Actionability.PROTECTED,
            rationale=" ",
        )
