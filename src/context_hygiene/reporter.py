"""Rich table + JSON report formatting."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from context_hygiene.models import HygieneReport

_GRADE_COLORS = {
    "A": "green",
    "B": "cyan",
    "C": "yellow",
    "D": "red",
    "F": "bold red",
}


def format_report_rich(report: HygieneReport, console: Console | None = None) -> None:
    """Print a formatted report to the terminal."""
    c = console or Console()

    grade_color = _GRADE_COLORS.get(report.grade.value, "white")
    header = (
        f"[bold]Context Hygiene Report[/bold]\n"
        f"File: {report.file_path}\n"
        f"Grade: [{grade_color}]{report.grade.value}[/{grade_color}]  |  "
        f"Tokens: {report.total_tokens:,}  |  "
        f"Recoverable: {report.tokens_recoverable:,}"
    )
    c.print(Panel(header, expand=False))

    # Staleness summary
    if report.staleness_results:
        stale = [s for s in report.staleness_results if s.score > 0.3]
        if stale:
            table = Table(title="Stale Segments", show_lines=True)
            table.add_column("Segment", style="dim", width=8)
            table.add_column("Score", width=8)
            table.add_column("Reasons")
            for s in stale:
                color = "red" if s.score > 0.6 else "yellow"
                table.add_row(
                    str(s.segment_index),
                    f"[{color}]{s.score:.2f}[/{color}]",
                    ", ".join(s.reasons),
                )
            c.print(table)

    # Contradictions
    if report.contradictions:
        table = Table(title="Contradictions", show_lines=True)
        table.add_column("Segments", width=12)
        table.add_column("Confidence", width=10)
        table.add_column("Description")
        for ct in report.contradictions:
            table.add_row(
                f"{ct.segment_a} vs {ct.segment_b}",
                f"{ct.confidence:.1%}",
                ct.description,
            )
        c.print(table)

    # Deadweight
    if report.deadweight:
        table = Table(title="Deadweight Messages", show_lines=True)
        table.add_column("Segment", width=8)
        table.add_column("Tokens", width=8)
        table.add_column("Reason")
        for dw in report.deadweight:
            table.add_row(
                str(dw.segment_index),
                str(dw.tokens_recoverable),
                dw.reason,
            )
        c.print(table)

    # Compression
    if report.compression_candidates:
        table = Table(title="Compression Opportunities", show_lines=True)
        table.add_column("Segments", width=15)
        table.add_column("Current", width=10)
        table.add_column("Savings", width=10)
        table.add_column("Reason")
        for cc in report.compression_candidates:
            indices = ", ".join(str(i) for i in cc.segment_indices[:5])
            if len(cc.segment_indices) > 5:
                indices += "..."
            table.add_row(
                indices,
                f"{cc.current_tokens:,}",
                f"{cc.savings_pct:.0f}%",
                cc.reason,
            )
        c.print(table)


def format_report_json(report: HygieneReport) -> str:
    """Format report as JSON string."""
    return report.model_dump_json(indent=2)
