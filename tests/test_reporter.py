"""Tests for context_hygiene.reporter."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from context_hygiene.models import (
    CompressionCandidate,
    Contradiction,
    DeadweightResult,
    Grade,
    HygieneReport,
    StalenessResult,
)
from context_hygiene.reporter import format_report_json, format_report_rich


def _make_console() -> Console:
    return Console(file=StringIO(), force_terminal=True)


class TestFormatReportRich:
    def test_empty_report(self):
        console = _make_console()
        report = HygieneReport(file_path="test.md", grade=Grade.A)
        format_report_rich(report, console)
        output = console.file.getvalue()
        assert "test.md" in output

    def test_with_staleness(self):
        console = _make_console()
        report = HygieneReport(
            file_path="test.md",
            grade=Grade.C,
            staleness_results=[
                StalenessResult(segment_index=0, score=0.8, reasons=["old"]),
                StalenessResult(segment_index=1, score=0.1, reasons=[]),
            ],
        )
        format_report_rich(report, console)
        output = console.file.getvalue()
        assert "Stale" in output

    def test_with_contradictions(self):
        console = _make_console()
        report = HygieneReport(
            file_path="test.md",
            grade=Grade.D,
            contradictions=[
                Contradiction(
                    segment_a=0,
                    segment_b=1,
                    description="conflict",
                    confidence=0.8,
                )
            ],
        )
        format_report_rich(report, console)
        output = console.file.getvalue()
        assert "Contradiction" in output

    def test_with_deadweight(self):
        console = _make_console()
        report = HygieneReport(
            file_path="test.md",
            grade=Grade.B,
            deadweight=[DeadweightResult(segment_index=2, reason="ack", tokens_recoverable=5)],
        )
        format_report_rich(report, console)
        output = console.file.getvalue()
        assert "Deadweight" in output

    def test_with_compression(self):
        console = _make_console()
        report = HygieneReport(
            file_path="test.md",
            grade=Grade.B,
            compression_candidates=[
                CompressionCandidate(
                    segment_indices=[0, 1, 2],
                    current_tokens=300,
                    estimated_compressed_tokens=100,
                    reason="consecutive",
                )
            ],
        )
        format_report_rich(report, console)
        output = console.file.getvalue()
        assert "Compression" in output

    def test_grade_colors(self):
        for grade in Grade:
            console = _make_console()
            report = HygieneReport(file_path="t.md", grade=grade)
            format_report_rich(report, console)
            # Should not raise

    def test_default_console(self):
        report = HygieneReport(file_path="test.md")
        # Should use default console without error
        format_report_rich(report)

    def test_many_compression_indices(self):
        console = _make_console()
        report = HygieneReport(
            file_path="test.md",
            compression_candidates=[
                CompressionCandidate(
                    segment_indices=list(range(10)),
                    current_tokens=1000,
                    estimated_compressed_tokens=300,
                    reason="many",
                )
            ],
        )
        format_report_rich(report, console)
        output = console.file.getvalue()
        assert "..." in output

    def test_low_staleness_not_shown(self):
        console = _make_console()
        report = HygieneReport(
            file_path="test.md",
            staleness_results=[
                StalenessResult(segment_index=0, score=0.1, reasons=["minor"]),
            ],
        )
        format_report_rich(report, console)
        # Low score (< 0.3) should not appear in stale table


class TestFormatReportJson:
    def test_valid_json(self):
        report = HygieneReport(file_path="test.md", total_tokens=500)
        result = format_report_json(report)
        assert '"file_path": "test.md"' in result
        assert '"total_tokens": 500' in result

    def test_indented(self):
        report = HygieneReport()
        result = format_report_json(report)
        assert "\n" in result  # Indented output has newlines
