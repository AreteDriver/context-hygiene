"""Pruning engine — applies audit results to produce cleaned output."""

from __future__ import annotations

from pathlib import Path

from context_hygiene.models import HygieneReport, Segment
from context_hygiene.parsers.detect import parse_file


class PruningPlan:
    """Plan for cleaning a conversation file."""

    def __init__(self, report: HygieneReport, segments: list[Segment]) -> None:
        self.report = report
        self.segments = segments
        self._remove_indices: set[int] = set()
        self._build()

    def _build(self) -> None:
        """Build removal set from report."""
        # Remove deadweight segments
        for dw in self.report.deadweight:
            self._remove_indices.add(dw.segment_index)

        # Remove highly stale segments (score > 0.6)
        for sr in self.report.staleness_results:
            if sr.score > 0.6:
                self._remove_indices.add(sr.segment_index)

    @property
    def segments_to_remove(self) -> int:
        return len(self._remove_indices)

    @property
    def segments_to_keep(self) -> int:
        return len(self.segments) - self.segments_to_remove

    @property
    def tokens_before(self) -> int:
        return sum(s.token_estimate for s in self.segments)

    @property
    def tokens_after(self) -> int:
        return sum(s.token_estimate for s in self.segments if s.index not in self._remove_indices)

    @property
    def tokens_saved(self) -> int:
        return self.tokens_before - self.tokens_after

    def apply(self) -> list[Segment]:
        """Return the cleaned segment list."""
        return [s for s in self.segments if s.index not in self._remove_indices]

    def summary(self) -> str:
        """Human-readable summary of what will be removed."""
        lines = [
            f"Pruning plan: remove {self.segments_to_remove}/{len(self.segments)} segments",
            f"Tokens: {self.tokens_before:,} → {self.tokens_after:,} (save {self.tokens_saved:,})",
        ]
        if self._remove_indices:
            lines.append(f"Remove indices: {sorted(self._remove_indices)}")
        return "\n".join(lines)


def build_pruning_plan(report: HygieneReport, file_path: str) -> PruningPlan:
    """Build a pruning plan from an audit report."""
    segments = parse_file(Path(file_path))
    return PruningPlan(report, segments)


def segments_to_markdown(segments: list[Segment]) -> str:
    """Convert segments back to markdown format."""
    lines: list[str] = []
    for seg in segments:
        role_label = seg.role.value.capitalize()
        lines.append(f"## {role_label}\n")
        lines.append(seg.content)
        lines.append("")
    return "\n".join(lines)
