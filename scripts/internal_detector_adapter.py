"""Internal pairwise scoring adapter for production duplicate findings.

Expand each production-flagged repeated message into all eligible earlier
same-role exact matches for synthetic pairwise evaluation only. Production
deadweight findings remain one actionable finding per repeated message.
This does not establish accuracy on external benchmark files.
"""

from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.models import Role, Segment


def predict_exact_duplicate_pairs(source_id: str, texts: list[str]) -> list[dict]:
    """Expand production-flagged duplicates to all matching earlier pairs."""
    segments = [
        Segment(index=i, role=Role.USER, content=text)
        for i, text in enumerate(texts)
    ]
    flagged = {
        finding.segment_index
        for finding in deadweight_fast(segments)
        if finding.reason.startswith("exact duplicate of segment ")
    }
    pairs = []
    for position, segment in enumerate(segments):
        if segment.index not in flagged:
            continue
        for earlier in segments[:position]:
            if earlier.role == segment.role and earlier.content == segment.content:
                pairs.append(
                    {
                        "source_id": source_id,
                        "block_a": str(earlier.index),
                        "block_b": str(segment.index),
                    }
                )
    return pairs
