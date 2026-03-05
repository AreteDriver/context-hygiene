"""Deadweight detector — identifies zero-influence messages."""

from __future__ import annotations

import re

from context_hygiene.models import DeadweightResult, Role, Segment

_I = re.IGNORECASE

# Patterns indicating low-value messages
_ACK_RE = re.compile(
    r"^(ok|okay|sure|thanks|thank you|got it|understood"
    r"|yes|no|right|exactly|perfect|great|good|nice|cool|alright)\.?$",
    _I,
)
_FILLER_RE = re.compile(r"^(hmm|hm|ah|oh|well|so|um|uh)\.?\.?\.?$", _I)
_ELLIPSIS_RE = re.compile(r"^\.{2,}$")

_DEADWEIGHT_PATTERNS = [
    (_ACK_RE, "acknowledgment-only message"),
    (_FILLER_RE, "filler/thinking word"),
    (_ELLIPSIS_RE, "ellipsis-only"),
]

# Assistant messages that are just confirmations
_CONFIRM_RE = re.compile(
    r"^(sure|of course|certainly|absolutely"
    r"|I'?d be happy to|I can|let me)\b.*[.!]?$",
    _I,
)
_ASSISTANT_DEADWEIGHT = [
    (_CONFIRM_RE, "assistant confirmation preamble"),
]


def deadweight_fast(segments: list[Segment]) -> list[DeadweightResult]:
    """Heuristic deadweight detection. Identifies messages with zero influence."""
    results: list[DeadweightResult] = []

    for seg in segments:
        content = seg.content.strip()

        # Check user deadweight patterns
        if seg.role == Role.USER:
            for pattern, reason in _DEADWEIGHT_PATTERNS:
                if pattern.match(content):
                    results.append(
                        DeadweightResult(
                            segment_index=seg.index,
                            reason=reason,
                            tokens_recoverable=seg.token_estimate,
                        )
                    )
                    break

        # Check assistant preamble patterns (only for short messages)
        if seg.role == Role.ASSISTANT and seg.token_estimate < 30:
            for pattern, reason in _ASSISTANT_DEADWEIGHT:
                if pattern.match(content):
                    results.append(
                        DeadweightResult(
                            segment_index=seg.index,
                            reason=reason,
                            tokens_recoverable=seg.token_estimate,
                        )
                    )
                    break

        # Duplicate content detection — exact match to earlier segment
        if seg.index > 0:
            for earlier in segments[: seg.index]:
                if earlier.content == seg.content and seg.token_estimate > 5:
                    results.append(
                        DeadweightResult(
                            segment_index=seg.index,
                            reason=f"exact duplicate of segment {earlier.index}",
                            tokens_recoverable=seg.token_estimate,
                        )
                    )
                    break

        # Empty or whitespace-only
        if not content:
            results.append(
                DeadweightResult(
                    segment_index=seg.index,
                    reason="empty message",
                    tokens_recoverable=seg.token_estimate,
                )
            )

    return results
