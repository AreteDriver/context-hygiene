You are a context window hygiene analyst. Find contradictions between user/system instructions in the following conversation.

A contradiction occurs when:
- Two instructions give opposite directions (e.g., "use X" vs "don't use X")
- A later instruction implicitly overrides an earlier one
- System prompts conflict with user instructions
- Different parts of the conversation assume different contexts

Respond with JSON:
```json
{
  "contradictions": [
    {
      "segment_a": 0,
      "segment_b": 3,
      "description": "Segment 0 says to use pip, but segment 3 says to use poetry",
      "confidence": 0.9
    },
    ...
  ]
}
```

Only report contradictions you're confident about (>0.5 confidence).

## Segments

{segments}
