"""Structured, read-only evidence for reviewing exact duplicate candidates.

This module verifies local evidence consistency, not whether removal is safe.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from context_hygiene.models import Segment
from context_hygiene.safety import Actionability, SafetyDecision, classify_duplicate


@dataclass(frozen=True)
class DuplicateEvidence:
    """Candidate/earlier identities and a digest bound to their exact contents."""

    candidate_index: int
    earlier_index: int
    role: str
    content_sha256: str
    referenced_indices: tuple[int, ...] = ()


@dataclass(frozen=True)
class EvidenceReview:
    """Conservative verification outcome; never authorizes context mutation."""

    decision: SafetyDecision
    exact_content_verified: bool
    identity_verified: bool
    dependencies_resolved: bool


def review_duplicate_evidence(
    segments: list[Segment], evidence: DuplicateEvidence
) -> EvidenceReview:
    """Check pair order, unique identities, roles, digest and referenced IDs.

    The reference list is caller-supplied and cannot prove that all downstream
    dependencies were discovered. Therefore even fully consistent evidence
    requires separate dependency review and human authorization.
    """
    positions: dict[int, list[int]] = {}
    for position, segment in enumerate(segments):
        positions.setdefault(segment.index, []).append(position)

    candidate_positions = positions.get(evidence.candidate_index, [])
    earlier_positions = positions.get(evidence.earlier_index, [])
    identity_verified = (
        evidence.candidate_index != evidence.earlier_index
        and len(candidate_positions) == 1
        and len(earlier_positions) == 1
        and earlier_positions[0] < candidate_positions[0]
    )
    exact_verified = False
    role = None
    if identity_verified:
        candidate = segments[candidate_positions[0]]
        earlier = segments[earlier_positions[0]]
        role = candidate.role.value
        exact_verified = (
            role == evidence.role
            and earlier.role == candidate.role
            and candidate.content == earlier.content
            and hashlib.sha256(candidate.content.encode("utf-8")).hexdigest()
            == evidence.content_sha256
        )

    dependencies_resolved = (
        len(set(evidence.referenced_indices)) == len(evidence.referenced_indices)
        and all(len(positions.get(index, [])) == 1 for index in evidence.referenced_indices)
    )
    decision = classify_duplicate(
        segment_index=evidence.candidate_index,
        role=role,
        exact_match=exact_verified,
        provenance_verified=identity_verified and exact_verified,
        dependency_reviewed=False,
    )
    return EvidenceReview(
        decision=decision,
        exact_content_verified=exact_verified,
        identity_verified=identity_verified,
        dependencies_resolved=dependencies_resolved,
    )
