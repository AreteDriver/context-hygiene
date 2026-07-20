"""Programmatic API for context-hygiene.

Use these functions to integrate context-hygiene into your own Python scripts
without shelling out to the CLI.

Examples:
    from context_hygiene import audit_file, score_file

    report = audit_file("CLAUDE.md")
    print(report.grade, report.tokens_recoverable)

    score = score_file("conversation.json")
    print(score.staleness, score.grade)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from context_hygiene.analyzers.compression import compression_fast
from context_hygiene.analyzers.contradictions import contradictions_fast
from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.analyzers.staleness import staleness_fast
from context_hygiene.exceptions import ContextHygieneError
from context_hygiene.models import (
    Grade,
    HygieneReport,
    Segment,
)
from context_hygiene.parsers.detect import parse_file


def audit_file(
    file_path: str | Path,
) -> HygieneReport:
    """Run a full fast-mode hygiene audit on a conversation file.

    Args:
        file_path: Path to the conversation file (JSON export, markdown, etc.)

    Returns:
        A complete HygieneReport with staleness, contradictions,
        deadweight, and compression analysis.

    Raises:
        ContextHygieneError: If the file cannot be parsed or analyzed.
    """
    path = Path(file_path)
    segments = parse_file(path)
    return _run_analysis(path, segments)


def score_file(
    file_path: str | Path,
) -> "ScoreResult":
    """Run a quick staleness score on a conversation file.

    Args:
        file_path: Path to the conversation file.

    Returns:
        A lightweight ScoreResult with grade and token stats.

    Raises:
        ContextHygieneError: If the file cannot be parsed.
    """
    path = Path(file_path)
    segments = parse_file(path)
    if not segments:
        return ScoreResult(
            grade=Grade.A,
            staleness=0.0,
            segments=0,
            tokens=0,
        )

    staleness = staleness_fast(segments)
    avg = sum(s.score for s in staleness) / len(staleness)
    total_tokens = sum(s.token_estimate for s in segments)

    if avg < 0.1:
        grade = Grade.A
    elif avg < 0.25:
        grade = Grade.B
    elif avg < 0.4:
        grade = Grade.C
    elif avg < 0.6:
        grade = Grade.D
    else:
        grade = Grade.F

    return ScoreResult(
        grade=grade,
        staleness=round(avg, 3),
        segments=len(segments),
        tokens=total_tokens,
    )


def _run_analysis(path: Path, segments: list[Segment]) -> HygieneReport:
    """Internal: run all fast analyzers and build a report."""
    if not segments:
        return HygieneReport(
            file_path=str(path),
            analyzed_at=datetime.now(timezone.utc),
        )

    staleness = staleness_fast(segments)
    contras = contradictions_fast(segments)
    dead = deadweight_fast(segments)
    comp = compression_fast(segments)

    total_tokens = sum(s.token_estimate for s in segments)
    tokens_recoverable = sum(d.tokens_recoverable for d in dead)
    tokens_recoverable += sum(c.savings_tokens for c in comp)

    avg_staleness = sum(s.score for s in staleness) / len(staleness) if staleness else 0.0

    report = HygieneReport(
        file_path=str(path),
        total_segments=len(segments),
        total_tokens=total_tokens,
        staleness_score=round(avg_staleness, 3),
        staleness_results=staleness,
        contradictions=contras,
        deadweight=dead,
        compression_candidates=comp,
        tokens_recoverable=tokens_recoverable,
        analyzed_at=datetime.now(timezone.utc),
    )
    report.grade = report.compute_grade()
    return report


class ScoreResult:
    """Lightweight result from ``score_file()``.

    Attributes:
        grade: Overall hygiene grade (A–F).
        staleness: Average staleness score (0.0–1.0).
        segments: Total number of conversation segments.
        tokens: Estimated total token count.
    """

    def __init__(
        self,
        grade: Grade,
        staleness: float,
        segments: int,
        tokens: int,
    ) -> None:
        self.grade = grade
        self.staleness = staleness
        self.segments = segments
        self.tokens = tokens

    def __repr__(self) -> str:
        return (
            f"ScoreResult(grade={self.grade.value!r}, "
            f"staleness={self.staleness:.2f}, "
            f"segments={self.segments}, tokens={self.tokens})"
        )
