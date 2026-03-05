"""Staleness analyzer — scores how stale each segment is."""

from __future__ import annotations

import re

from context_hygiene.models import Segment, StalenessResult

_I = re.IGNORECASE

# Patterns indicating potentially stale content
_STALE_PATTERNS = [
    (re.compile(r"\b(previously|earlier|before|above)\b", _I), 0.1, "references earlier context"),
    (re.compile(r"\b(scratch that|never\s?mind|ignore|disregard)\b", _I), 0.4, "superseded"),
    (re.compile(r"\b(actually|instead|correction|update)\b", _I), 0.2, "correction/update"),
    (re.compile(r"\b(let me (start|try) (over|again)|from scratch)\b", _I), 0.5, "restart"),
    (re.compile(r"\b(old|outdated|deprecated|obsolete)\b", _I), 0.3, "explicitly stale"),
]

# Error/traceback patterns — often stale after fix
_ERROR_PATTERNS = [
    (re.compile(r"(Traceback|Error|Exception|Failed|error:)", _I), 0.15, "error output"),
    (re.compile(r"```[\s\S]{500,}```", re.DOTALL), 0.1, "large code block"),
]


def staleness_fast(segments: list[Segment]) -> list[StalenessResult]:
    """Heuristic staleness scoring. No LLM needed."""
    results: list[StalenessResult] = []
    total = len(segments)

    for seg in segments:
        score = 0.0
        reasons: list[str] = []

        # Position decay — earlier segments are more likely stale
        if total > 1:
            position_score = (1 - seg.index / (total - 1)) * 0.2
            score += position_score
            if position_score > 0.1:
                reasons.append(f"early position ({seg.index + 1}/{total})")

        # Pattern matching
        for pattern, weight, reason in _STALE_PATTERNS:
            if pattern.search(seg.content):
                score += weight
                reasons.append(reason)

        for pattern, weight, reason in _ERROR_PATTERNS:
            if pattern.search(seg.content):
                score += weight
                reasons.append(reason)

        # Very short messages in middle of conversation are often stale
        if seg.token_estimate < 10 and 0 < seg.index < total - 1:
            score += 0.1
            reasons.append("very short mid-conversation message")

        # Cap at 1.0
        score = min(score, 1.0)
        results.append(
            StalenessResult(
                segment_index=seg.index,
                score=round(score, 3),
                reasons=reasons,
            )
        )

    return results
