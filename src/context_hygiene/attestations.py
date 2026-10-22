"""Immutable human-review attestation contract; validation never authorizes mutation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from context_hygiene.evidence import DuplicateEvidence, review_duplicate_evidence
from context_hygiene.models import Segment
from context_hygiene.safety import Actionability


class ReviewOutcome(str, Enum):
    """Review outcome is a record of judgment, not an execution permission."""

    APPROVED_FOR_FURTHER_REVIEW = "approved_for_further_review"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ReviewAttestation:
    """Explicit reviewer judgment bound to the candidate's evidence digest."""

    reviewer_id: str
    evidence_sha256: str
    outcome: ReviewOutcome
    dependency_scope: str
    rationale: str


@dataclass(frozen=True)
class AttestationResult:
    """A verified local review record, never a grant of mutation authority."""

    valid: bool
    reason: str
    authorized_to_mutate: bool = False


def validate_review_attestation(
    segments: list[Segment],
    evidence: DuplicateEvidence,
    attestation: ReviewAttestation,
) -> AttestationResult:
    """Fail closed on mismatched evidence or absent review details.

    A string reviewer ID is not identity authentication, and a declared scope
    does not prove complete downstream dependency discovery. Callers must not
    treat a valid local record as authorization for destructive operations.
    """
    if not attestation.reviewer_id.strip():
        return AttestationResult(False, "Reviewer identity is missing")
    if not attestation.rationale.strip() or not attestation.dependency_scope.strip():
        return AttestationResult(False, "Review rationale and dependency scope are required")
    if attestation.outcome is not ReviewOutcome.APPROVED_FOR_FURTHER_REVIEW:
        return AttestationResult(False, "Review was rejected")
    review = review_duplicate_evidence(segments, evidence)
    if review.decision.disposition is Actionability.PROTECTED:
        return AttestationResult(False, "System instructions are protected")
    if not review.identity_verified or not review.exact_content_verified:
        return AttestationResult(False, "Candidate evidence failed verification")
    if not review.dependencies_resolved:
        return AttestationResult(False, "Supplied dependency references are ambiguous")
    if attestation.evidence_sha256 != evidence.content_sha256:
        return AttestationResult(False, "Attestation is not bound to the content digest")
    return AttestationResult(True, "Local review record verified; no mutation authorization")
