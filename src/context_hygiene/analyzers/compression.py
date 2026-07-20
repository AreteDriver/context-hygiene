"""Compression analyzer — finds compressible segments."""

from __future__ import annotations

import re

from context_hygiene.models import CompressionCandidate, Role, Segment

_CODE_BLOCK = re.compile(r"```[\s\S]*?```")
_LARGE_CODE_THRESHOLD = 500  # tokens


def compression_fast(segments: list[Segment]) -> list[CompressionCandidate]:
    """Heuristic compression analysis. Finds groups that can be summarized."""
    candidates: list[CompressionCandidate] = []

    # 1. Consecutive same-role segments (can be merged)
    candidates.extend(_find_consecutive_same_role(segments))

    # 2. Large code blocks that could be summarized
    candidates.extend(_find_large_code_blocks(segments))

    # 3. Long assistant explanations that could be condensed
    candidates.extend(_find_verbose_explanations(segments))

    return candidates


def _find_consecutive_same_role(segments: list[Segment]) -> list[CompressionCandidate]:
    """Find runs of consecutive messages from the same role."""
    candidates: list[CompressionCandidate] = []
    if len(segments) < 2:
        return candidates

    run_start = 0
    for i in range(1, len(segments)):
        if segments[i].role != segments[run_start].role:
            run_len = i - run_start
            if run_len >= 3:
                candidate = _make_consecutive_candidate(segments, run_start, i)
                if candidate:
                    candidates.append(candidate)
            run_start = i

    # Check final run
    run_len = len(segments) - run_start
    if run_len >= 3:
        candidate = _make_consecutive_candidate(segments, run_start, len(segments))
        if candidate:
            candidates.append(candidate)

    return candidates


def _make_consecutive_candidate(
    segments: list[Segment], start: int, end: int
) -> CompressionCandidate | None:
    """Build a candidate for a run of same-role segments.

    Returns None if the run covers the entire file and all segments are SYSTEM,
    to avoid penalizing structured instruction files (CLAUDE.md, AGENTS.md).
    """
    run_segments = segments[start:end]
    run_len = len(run_segments)
    total_tokens = sum(s.token_estimate for s in run_segments)

    # Skip if this run covers the entire file — it's likely an instruction file,
    # not a compressible conversation transcript.
    if start == 0 and end == len(segments):
        return None

    return CompressionCandidate(
        segment_indices=[s.index for s in run_segments],
        current_tokens=total_tokens,
        estimated_compressed_tokens=max(total_tokens // 3, 10),
        reason=f"{run_len} consecutive {segments[start].role.value} messages",
    )


def _find_large_code_blocks(segments: list[Segment]) -> list[CompressionCandidate]:
    """Find segments with large code blocks that could be referenced instead."""
    candidates: list[CompressionCandidate] = []

    for seg in segments:
        blocks = _CODE_BLOCK.findall(seg.content)
        for block in blocks:
            block_tokens = len(block.split())
            if block_tokens >= _LARGE_CODE_THRESHOLD:
                candidates.append(
                    CompressionCandidate(
                        segment_indices=[seg.index],
                        current_tokens=seg.token_estimate,
                        estimated_compressed_tokens=max(seg.token_estimate // 4, 20),
                        reason="large code block could be summarized/referenced",
                    )
                )
                break  # One candidate per segment

    return candidates


def _find_verbose_explanations(segments: list[Segment]) -> list[CompressionCandidate]:
    """Find long assistant responses that could be condensed."""
    candidates: list[CompressionCandidate] = []
    threshold = 800  # tokens

    for seg in segments:
        if seg.role == Role.ASSISTANT and seg.token_estimate > threshold:
            # Skip if mostly code
            code_blocks = _CODE_BLOCK.findall(seg.content)
            code_tokens = sum(len(b.split()) for b in code_blocks)
            prose_tokens = seg.token_estimate - code_tokens
            if prose_tokens > threshold:
                candidates.append(
                    CompressionCandidate(
                        segment_indices=[seg.index],
                        current_tokens=seg.token_estimate,
                        estimated_compressed_tokens=max(seg.token_estimate // 3, 50),
                        reason="verbose assistant explanation could be condensed",
                    )
                )

    return candidates
