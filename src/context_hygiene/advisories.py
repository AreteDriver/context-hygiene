"""Build advisory safety records from detector findings without authorizing changes."""

from __future__ import annotations

from context_hygiene.models import DeadweightResult, Segment
from context_hygiene.safety import classify_duplicate


def safety_advisories(
    segments: list[Segment], findings: list[DeadweightResult]
) -> list[dict[str, str | int | bool]]:
    """Emit one fail-closed advisory per finding, preserving detector order.

    Duplicate segment IDs are ambiguous; no role is trusted in that case.
    Neither provenance nor dependency review is inferred from detection.
    """
    by_id: dict[int, list[Segment]] = {}
    for segment in segments:
        by_id.setdefault(segment.index, []).append(segment)

    records: list[dict[str, str | int | bool]] = []
    for finding in findings:
        candidates = by_id.get(finding.segment_index, [])
        role = candidates[0].role.value if len(candidates) == 1 else None
        decision = classify_duplicate(
            segment_index=finding.segment_index,
            role=role,
            exact_match=finding.reason.startswith("exact duplicate of segment "),
        )
        records.append(
            {
                "segment_index": decision.segment_index,
                "finding_reason": finding.reason,
                "disposition": decision.disposition.value,
                "rationale": decision.rationale,
                "authorized_to_mutate": decision.authorized_to_mutate,
            }
        )
    return records
