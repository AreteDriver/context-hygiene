"""Conservative classification of context findings; no mutation capability.

Detection is evidence, not authorization to remove, rewrite, or archive content.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Actionability(str, Enum):
    """Allowed advisory dispositions; none perform an action."""

    PROTECTED = "protected"
    REVIEW_REQUIRED = "review_required"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class SafetyDecision:
    """Immutable, advisory safety result for one detected segment."""

    segment_index: int
    disposition: Actionability
    rationale: str
    authorized_to_mutate: bool = False

    def __post_init__(self) -> None:
        if self.authorized_to_mutate:
            raise ValueError("Context mutation authorization is not supported")
        if not self.rationale.strip():
            raise ValueError("A nonempty rationale is required")


def classify_duplicate(
    *,
    segment_index: int,
    role: str | None,
    exact_match: bool,
    provenance_verified: bool = False,
    dependency_reviewed: bool = False,
) -> SafetyDecision:
    """Classify a candidate conservatively, never authorizing mutation.

    Verified provenance and dependency review are necessary but not sufficient
    for any future consolidation authorization.
    """
    if role is None or role not in {"system", "user", "assistant"}:
        return SafetyDecision(
            segment_index,
            Actionability.INSUFFICIENT_EVIDENCE,
            "Unknown or missing role; cannot assess instruction boundaries",
        )
    if role == "system":
        return SafetyDecision(
            segment_index,
            Actionability.PROTECTED,
            "System-level instructions are protected regardless of exact matching",
        )
    if not exact_match:
        return SafetyDecision(
            segment_index,
            Actionability.INSUFFICIENT_EVIDENCE,
            "No verified exact duplicate evidence",
        )
    if not provenance_verified or not dependency_reviewed:
        return SafetyDecision(
            segment_index,
            Actionability.INSUFFICIENT_EVIDENCE,
            "Provenance and downstream dependency review are required",
        )
    return SafetyDecision(
        segment_index,
        Actionability.REVIEW_REQUIRED,
        "Exact-match evidence is eligible for human review only",
    )
