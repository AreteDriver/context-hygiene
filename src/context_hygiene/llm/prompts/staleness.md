You are a context window hygiene analyst. Analyze the following conversation segments for staleness.

For each segment, score it 0.0 (completely fresh/relevant) to 1.0 (completely stale/irrelevant).

A segment is stale if:
- It has been superseded by later instructions
- It contains error output that has since been fixed
- It references decisions that were later changed
- It contains information that is no longer relevant to the current task
- It was part of an abandoned approach

Respond with JSON:
```json
{
  "results": [
    {"segment_index": 0, "score": 0.3, "reasons": ["references abandoned approach"]},
    ...
  ]
}
```

## Segments

{segments}
