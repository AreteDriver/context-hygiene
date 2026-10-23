#!/usr/bin/env python3
"""Generate synthetic conversation fixtures for benchmarking."""

from __future__ import annotations

import argparse
import random
from pathlib import Path


# Templates for generating realistic conversation content
USER_PROMPTS = [
    "Explain the concept of {topic}.",
    "How do I implement {topic} in Python?",
    "What's the best practice for {topic}?",
    "Can you compare {topic_a} and {topic_b}?",
    "Debug this code: {code_snippet}",
    "Write a function that {requirement}.",
    "Refactor this to use {pattern}.",
    "Explain the difference between {topic_a} and {topic_b}.",
]

ASSISTANT_RESPONSES = [
    "Here's how {topic} works: {explanation}.",
    "You can implement {topic} by following these steps: {steps}.",
    "The best practice for {topic} is to {advice}.",
    "{topic_a} and {topic_b} differ in several ways: {comparison}.",
    "Looking at your code, the issue is {diagnosis}. Here's the fix: {fix}.",
    "Here's a function that {requirement}: {code_block}",
    "Refactored to use {pattern}: {code_block}",
    "The key differences are: {comparison}.",
]

TOPICS = [
    "asyncio", "generators", "decorators", "type hints", "dataclasses",
    "context managers", "metaclasses", "descriptors", "slots",
    "garbage collection", "GIL", "multiprocessing", "threading",
    "coroutines", "event loops", "backpressure", "circuit breakers",
]

PATTERNS = [
    "singleton", "factory", "observer", "strategy", "adapter",
    "decorator", "command", "repository", "unit of work",
]

CODE_SNIPPETS = [
    "def foo(): pass",
    "class Bar: def __init__(self): pass",
    "for i in range(10): print(i)",
    "with open('file.txt') as f: data = f.read()",
    "try:\n    result = risky_operation()\nexcept ValueError:\n    handle_error()",
]


def _render(template: str, topics: list[str]) -> str:
    """Fill in a template with random content."""
    text = template
    if "{topic_a}" in text and "{topic_b}" in text:
        a, b = random.sample(topics, 2)
        text = text.replace("{topic_a}", a).replace("{topic_b}", b)
    elif "{topic}" in text:
        text = text.replace("{topic}", random.choice(topics))
    if "{pattern}" in text:
        text = text.replace("{pattern}", random.choice(PATTERNS))
    if "{code_snippet}" in text:
        text = text.replace("{code_snippet}", random.choice(CODE_SNIPPETS))
    if "{requirement}" in text:
        text = text.replace("{requirement}", "sorts a list of dictionaries by key")
    if "{explanation}" in text:
        text = text.replace("{explanation}", "it provides a way to write concurrent code using the async/await syntax")
    if "{steps}" in text:
        text = text.replace("{steps}", "1. Import asyncio 2. Define an async function 3. Use await to call other async functions")
    if "{advice}" in text:
        text = text.replace("{advice}", "always use context managers for resource cleanup")
    if "{comparison}" in text:
        text = text.replace("{comparison}", "A uses eager evaluation while B uses lazy evaluation")
    if "{diagnosis}" in text:
        text = text.replace("{diagnosis}", "you're modifying a list while iterating over it")
    if "{fix}" in text:
        text = text.replace("{fix}", "iterate over a copy instead: for item in items[:]")
    if "{code_block}" in text:
        text = text.replace("{code_block}", "\n```python\ndef example():\n    return 42\n```\n")
    return text


def generate_conversation(target_tokens: int, output_path: Path) -> int:
    """Generate a markdown conversation file with approximately target_tokens tokens.

    Returns actual token count.
    """
    lines = []
    total_words = 0
    # Rough heuristic: 1 token ≈ 0.75 words
    target_words = int(target_tokens * 0.75)

    while total_words < target_words:
        # User message
        prompt = random.choice(USER_PROMPTS)
        user_text = _render(prompt, TOPICS)
        lines.append(f"## User\n\n{user_text}\n")
        total_words += len(user_text.split())

        # Assistant message
        response = random.choice(ASSISTANT_RESPONSES)
        assistant_text = _render(response, TOPICS)
        lines.append(f"## Assistant\n\n{assistant_text}\n")
        total_words += len(assistant_text.split())

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return total_words


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate benchmark fixtures")
    parser.add_argument("--tokens", type=int, default=10000, help="Target token count")
    parser.add_argument("--output", type=Path, default=Path("benchmarks/fixture_large.md"))
    args = parser.parse_args()

    actual_words = generate_conversation(args.tokens, args.output)
    print(f"Generated {args.output} with ~{actual_words} words (target: {args.tokens} tokens)")


if __name__ == "__main__":
    main()
