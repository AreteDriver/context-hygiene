"""Build advisory safety records from detector findings without authorizing changes."""

from __future__ import annotations

from typing import Any

from context_hygiene.evidence import DuplicateEvidence, review_duplicate_evidence
from context_hygiene.models import (
    DeadweightResult,
    DependencyEvidence,
    ProvenanceEvidence,
    Segment,
)
from context_hygiene.safety import classify_duplicate


def safety_advisories(
    segments: list[Segment], findings: list[DeadweightResult]
) -> list[dict[str, Any]]:
    """Emit one fail-closed advisory per finding, preserving detector order.

    Duplicate segment IDs are ambiguous; no role is trusted in that case.
    Neither provenance nor dependency review is inferred from detection.
    """
    by_id: dict[int, list[Segment]] = {}
    for segment in segments:
        by_id.setdefault(segment.index, []).append(segment)

    records: list[dict[str, Any]] = []
    for finding in findings:
        candidates = by_id.get(finding.segment_index, [])
        role = candidates[0].role.value if len(candidates) == 1 else None
        provenance = ProvenanceEvidence()
        dependencies = DependencyEvidence()
        decision = classify_duplicate(
            segment_index=finding.segment_index,
            role=role,
            exact_match=False,
        )
        reference = finding.duplicate_reference
        if reference is not None:
            review = review_duplicate_evidence(
                segments,
                DuplicateEvidence(
                    candidate_index=finding.segment_index,
                    earlier_index=reference.earlier_index,
                    role=reference.role.value,
                    content_sha256=reference.content_sha256,
                    referenced_indices=tuple(reference.referenced_indices),
                ),
            )
            decision = review.decision
            provenance = ProvenanceEvidence(
                identity_verified=review.identity_verified,
                exact_content_verified=review.exact_content_verified,
            )
            dependencies = DependencyEvidence(
                referenced_indices=reference.referenced_indices,
                references_resolved=review.dependencies_resolved,
            )
        records.append(
            {
                "segment_index": decision.segment_index,
                "finding_reason": finding.reason,
                "disposition": decision.disposition.value,
                "rationale": decision.rationale,
                "authorized_to_mutate": decision.authorized_to_mutate,
                "duplicate_reference": reference.model_dump(mode="json") if reference else None,
                "provenance": provenance.model_dump(mode="json"),
                "dependencies": dependencies.model_dump(mode="json"),
            }
        )
    return records
