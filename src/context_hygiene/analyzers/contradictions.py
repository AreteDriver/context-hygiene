"""Contradiction detector — finds conflicting instructions."""

from __future__ import annotations

import re

from context_hygiene.models import Contradiction, Role, Segment

_I = re.IGNORECASE

# Patterns that indicate instruction/directive content
_INSTRUCTION_PATTERNS = [
    re.compile(r"\b(always|never|must|should|don't|do not|make sure)\b", _I),
    re.compile(r"\b(use|avoid|prefer|ensure|require)\b", _I),
    re.compile(r"\b(enable|disable|include|exclude)\b", _I),
]

# Negation pairs
_NEGATION_PAIRS = [
    (
        re.compile(r"\buse\s+(\w+)", _I),
        re.compile(r"\b(?:don't|do not|avoid|never)\s+use\s+(\w+)", _I),
    ),
    (
        re.compile(r"\balways\s+(\w+)", _I),
        re.compile(r"\bnever\s+(\w+)", _I),
    ),
    (
        re.compile(r"\benable\s+(\w+)", _I),
        re.compile(r"\bdisable\s+(\w+)", _I),
    ),
    (
        re.compile(r"\binclude\s+(\w+)", _I),
        re.compile(r"\bexclude\s+(\w+)", _I),
    ),
]


def contradictions_fast(segments: list[Segment]) -> list[Contradiction]:
    """Heuristic contradiction detection between user/system segments."""
    # Only check instruction-bearing segments
    instruction_segments = [
        s
        for s in segments
        if s.role in (Role.USER, Role.SYSTEM)
        and any(p.search(s.content) for p in _INSTRUCTION_PATTERNS)
    ]

    contradictions: list[Contradiction] = []

    for i, seg_a in enumerate(instruction_segments):
        for seg_b in instruction_segments[i + 1 :]:
            for pos_pattern, neg_pattern in _NEGATION_PAIRS:
                pos_matches_a = pos_pattern.findall(seg_a.content)
                neg_matches_b = neg_pattern.findall(seg_b.content)

                for pa in pos_matches_a:
                    for nb in neg_matches_b:
                        if pa.lower() == nb.lower():
                            contradictions.append(
                                Contradiction(
                                    segment_a=seg_a.index,
                                    segment_b=seg_b.index,
                                    description=(
                                        f"Conflicting about '{pa}': "
                                        f"positive in {seg_a.index}, "
                                        f"negative in {seg_b.index}"
                                    ),
                                    confidence=0.7,
                                )
                            )

                # Check reverse direction
                pos_matches_b = pos_pattern.findall(seg_b.content)
                neg_matches_a = neg_pattern.findall(seg_a.content)

                for nb_a in neg_matches_a:
                    for pb in pos_matches_b:
                        if nb_a.lower() == pb.lower():
                            contradictions.append(
                                Contradiction(
                                    segment_a=seg_a.index,
                                    segment_b=seg_b.index,
                                    description=(
                                        f"Conflicting about '{pb}': "
                                        f"negative in {seg_a.index}, "
                                        f"positive in {seg_b.index}"
                                    ),
                                    confidence=0.7,
                                )
                            )

    return contradictions
