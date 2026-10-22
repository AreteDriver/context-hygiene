"""Adapter from production deadweight detector to internal exact-duplicate pair scoring.

This evaluates a deliberately narrow synthetic fixture with at most one earlier
identical segment per duplicate. It does not evaluate external benchmark files.
"""

from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.models import Role, Segment


def predict_exact_duplicate_pairs(source_id: str, texts: list[str]) -> list[dict]:
    """Convert exact-duplicate deadweight findings into unordered pair IDs."""
    segments = [
        Segment(index=i, role=Role.USER, content=text)
        for i, text in enumerate(texts)
    ]
    results = deadweight_fast(segments)
    pairs = []
    for finding in results:
        prefix = "exact duplicate of segment "
        if not finding.reason.startswith(prefix):
            continue
        earlier = int(finding.reason.removeprefix(prefix))
        pairs.append(
            {
                "source_id": source_id,
                "block_a": str(earlier),
                "block_b": str(finding.segment_index),
            }
        )
    return pairs
