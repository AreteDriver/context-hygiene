"""Deep (LLM-powered) analyzer variants."""

from __future__ import annotations

from pathlib import Path

from context_hygiene.exceptions import AnalysisError
from context_hygiene.llm.base import BaseLLMProvider
from context_hygiene.llm.ollama import extract_json
from context_hygiene.models import (
    CompressionCandidate,
    Contradiction,
    DeadweightResult,
    Segment,
    StalenessResult,
)

_PROMPTS_DIR = Path(__file__).parent.parent / "llm" / "prompts"


def _load_prompt(name: str) -> str:
    """Load a prompt template by name."""
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise AnalysisError(f"Prompt template not found: {name}")
    return path.read_text(encoding="utf-8")


def _format_segments(segments: list[Segment]) -> str:
    """Format segments for LLM prompt injection."""
    lines: list[str] = []
    for seg in segments:
        lines.append(
            f"[Segment {seg.index}] ({seg.role.value}, ~{seg.token_estimate} tokens)\n"
            f"{seg.content[:500]}"
        )
        if len(seg.content) > 500:
            lines.append(f"... ({len(seg.content) - 500} chars truncated)")
        lines.append("")
    return "\n".join(lines)


def staleness_deep(segments: list[Segment], provider: BaseLLMProvider) -> list[StalenessResult]:
    """LLM-powered staleness analysis."""
    prompt = _load_prompt("staleness")
    prompt = prompt.replace("{segments}", _format_segments(segments))

    response = provider.generate(prompt)
    data = extract_json(response)
    if not data or "results" not in data:
        raise AnalysisError("Failed to parse staleness response from LLM")

    results: list[StalenessResult] = []
    for item in data["results"]:
        results.append(
            StalenessResult(
                segment_index=item.get("segment_index", 0),
                score=float(item.get("score", 0.0)),
                reasons=item.get("reasons", []),
            )
        )
    return results


def contradictions_deep(segments: list[Segment], provider: BaseLLMProvider) -> list[Contradiction]:
    """LLM-powered contradiction detection."""
    prompt = _load_prompt("contradictions")
    prompt = prompt.replace("{segments}", _format_segments(segments))

    response = provider.generate(prompt)
    data = extract_json(response)
    if not data or "contradictions" not in data:
        raise AnalysisError("Failed to parse contradictions response from LLM")

    results: list[Contradiction] = []
    for item in data["contradictions"]:
        results.append(
            Contradiction(
                segment_a=item.get("segment_a", 0),
                segment_b=item.get("segment_b", 0),
                description=item.get("description", ""),
                confidence=float(item.get("confidence", 0.0)),
            )
        )
    return results


def deadweight_deep(segments: list[Segment], provider: BaseLLMProvider) -> list[DeadweightResult]:
    """LLM-powered deadweight detection."""
    prompt = _load_prompt("deadweight")
    prompt = prompt.replace("{segments}", _format_segments(segments))

    response = provider.generate(prompt)
    data = extract_json(response)
    if not data or "deadweight" not in data:
        raise AnalysisError("Failed to parse deadweight response from LLM")

    results: list[DeadweightResult] = []
    for item in data["deadweight"]:
        results.append(
            DeadweightResult(
                segment_index=item.get("segment_index", 0),
                reason=item.get("reason", ""),
                tokens_recoverable=int(item.get("tokens_recoverable", 0)),
            )
        )
    return results


def compression_deep(
    segments: list[Segment], provider: BaseLLMProvider
) -> list[CompressionCandidate]:
    """LLM-powered compression analysis."""
    prompt = _load_prompt("compression")
    prompt = prompt.replace("{segments}", _format_segments(segments))

    response = provider.generate(prompt)
    data = extract_json(response)
    if not data or "candidates" not in data:
        raise AnalysisError("Failed to parse compression response from LLM")

    results: list[CompressionCandidate] = []
    for item in data["candidates"]:
        results.append(
            CompressionCandidate(
                segment_indices=item.get("segment_indices", []),
                current_tokens=int(item.get("current_tokens", 0)),
                estimated_compressed_tokens=int(item.get("estimated_compressed_tokens", 0)),
                reason=item.get("reason", ""),
            )
        )
    return results
