"""Attestations are review records, never deletion authorization."""

import hashlib

from context_hygiene.attestations import (
    ReviewAttestation,
    ReviewOutcome,
    validate_review_attestation,
)
from context_hygiene.evidence import DuplicateEvidence
from context_hygiene.models import Role, Segment

TEXT = "Keep these instructions and their citations intact."
DIGEST = hashlib.sha256(TEXT.encode("utf-8")).hexdigest()


def fixture(role=Role.USER):
    segments = [
        Segment(index=1, role=role, content=TEXT),
        Segment(index=2, role=role, content=TEXT),
    ]
    evidence = DuplicateEvidence(2, 1, role.value, DIGEST)
    attestation = ReviewAttestation(
        "reviewer-1",
        DIGEST,
        ReviewOutcome.APPROVED_FOR_FURTHER_REVIEW,
        "Synthetic document references only",
        "Candidate exact duplicate requires further human assessment",
    )
    return segments, evidence, attestation


def test_valid_local_attestation_is_not_mutation_authority():
    result = validate_review_attestation(*fixture())
    assert result.valid
    assert result.authorized_to_mutate is False


def test_protected_system_instruction_rejected():
    result = validate_review_attestation(*fixture(Role.SYSTEM))
    assert not result.valid
    assert not result.authorized_to_mutate


def test_mismatched_digest_rejected():
    segments, evidence, attestation = fixture()
    changed = ReviewAttestation(
        attestation.reviewer_id,
        "0" * 64,
        attestation.outcome,
        attestation.dependency_scope,
        attestation.rationale,
    )
    assert not validate_review_attestation(segments, evidence, changed).valid


def test_missing_reviewer_rejected():
    segments, evidence, attestation = fixture()
    changed = ReviewAttestation(
        "", DIGEST, attestation.outcome, attestation.dependency_scope, attestation.rationale
    )
    assert not validate_review_attestation(segments, evidence, changed).valid


def test_rejection_is_not_approval():
    segments, evidence, attestation = fixture()
    changed = ReviewAttestation(
        attestation.reviewer_id,
        DIGEST,
        ReviewOutcome.REJECTED,
        attestation.dependency_scope,
        attestation.rationale,
    )
    assert not validate_review_attestation(segments, evidence, changed).valid


def test_unresolved_reference_rejected():
    segments, evidence, attestation = fixture()
    changed = DuplicateEvidence(2, 1, "user", DIGEST, (999,))
    assert not validate_review_attestation(segments, changed, attestation).valid
