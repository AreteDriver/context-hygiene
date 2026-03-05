"""CLI for context-hygiene."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from context_hygiene import __version__
from context_hygiene.analyzers.compression import compression_fast
from context_hygiene.analyzers.contradictions import contradictions_fast
from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.analyzers.staleness import staleness_fast
from context_hygiene.config import db_path, get_config_dir, load_config
from context_hygiene.exceptions import ContextHygieneError, LicenseError
from context_hygiene.licensing import (
    MAX_FREE_AUDITS_PER_MONTH,
    get_license,
)
from context_hygiene.models import AnalysisMode, HygieneReport
from context_hygiene.parsers.detect import parse_file
from context_hygiene.reporter import format_report_json, format_report_rich
from context_hygiene.store import AuditStore

app = typer.Typer(
    name="ctx-hygiene",
    help="Context window hygiene analyzer for LLM conversations.",
    no_args_is_help=True,
)
console = Console()


def _get_store() -> AuditStore:
    return AuditStore(db_path())


def _check_audit_quota() -> None:
    """Check free tier audit quota."""
    info = get_license()
    if info.is_pro:
        return
    store = _get_store()
    try:
        count = store.count_audits_this_month()
        if count >= MAX_FREE_AUDITS_PER_MONTH:
            raise LicenseError(
                f"Free tier limit reached ({MAX_FREE_AUDITS_PER_MONTH} audits/month). "
                "Upgrade to Pro for unlimited audits."
            )
    finally:
        store.close()


def _run_analysis(file_path: str) -> HygieneReport:
    """Run full fast analysis on a file."""
    segments = parse_file(Path(file_path))
    if not segments:
        return HygieneReport(
            file_path=file_path,
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
        file_path=file_path,
        total_segments=len(segments),
        total_tokens=total_tokens,
        staleness_score=round(avg_staleness, 3),
        staleness_results=staleness,
        contradictions=contras,
        deadweight=dead,
        compression_candidates=comp,
        tokens_recoverable=tokens_recoverable,
        analyzed_at=datetime.now(timezone.utc),
        mode=AnalysisMode.FAST,
    )
    report.grade = report.compute_grade()
    return report


@app.command()
def audit(
    file: str = typer.Argument(..., help="Conversation file to audit"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Full hygiene audit: staleness + contradictions + deadweight + compression."""
    try:
        _check_audit_quota()
        report = _run_analysis(file)

        # Save to store
        store = _get_store()
        try:
            store.save_audit(report)
        finally:
            store.close()

        if output_json:
            console.print(format_report_json(report))
        else:
            format_report_rich(report, console)
    except ContextHygieneError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def score(
    file: str = typer.Argument(..., help="Conversation file to score"),
) -> None:
    """Quick staleness score (heuristic, no LLM, unlimited)."""
    try:
        segments = parse_file(Path(file))
        if not segments:
            console.print("[yellow]No segments found.[/yellow]")
            raise typer.Exit(0)

        staleness = staleness_fast(segments)
        avg = sum(s.score for s in staleness) / len(staleness)
        total_tokens = sum(s.token_estimate for s in segments)

        # Simple grade
        if avg < 0.1:
            grade, color = "A", "green"
        elif avg < 0.25:
            grade, color = "B", "cyan"
        elif avg < 0.4:
            grade, color = "C", "yellow"
        elif avg < 0.6:
            grade, color = "D", "red"
        else:
            grade, color = "F", "bold red"

        console.print(
            f"[bold]Staleness Score:[/bold] [{color}]{avg:.2f}[/{color}]  "
            f"Grade: [{color}]{grade}[/{color}]  "
            f"Segments: {len(segments)}  "
            f"Tokens: {total_tokens:,}"
        )
    except ContextHygieneError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def history(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of entries"),
) -> None:
    """Show past audit summaries."""
    store = _get_store()
    try:
        audits = store.list_audits(limit)
    finally:
        store.close()

    if not audits:
        console.print("[dim]No audit history yet.[/dim]")
        return

    table = Table(title="Audit History")
    table.add_column("ID", width=5)
    table.add_column("File", max_width=40)
    table.add_column("Grade", width=6)
    table.add_column("Tokens", width=10)
    table.add_column("Recoverable", width=12)
    table.add_column("Date", width=20)

    for a in audits:
        color = {"A": "green", "B": "cyan", "C": "yellow", "D": "red", "F": "bold red"}.get(
            a.grade.value, "white"
        )
        table.add_row(
            str(a.audit_id),
            a.file_path,
            f"[{color}]{a.grade.value}[/{color}]",
            f"{a.total_tokens:,}",
            f"{a.tokens_recoverable:,}",
            a.audited_at.strftime("%Y-%m-%d %H:%M") if a.audited_at else "—",
        )

    console.print(table)


@app.command()
def status() -> None:
    """Show license, provider config, and audit count."""
    info = get_license()
    config = load_config()
    store = _get_store()
    try:
        month_count = store.count_audits_this_month()
    finally:
        store.close()

    tier_color = "green" if info.is_pro else "yellow"
    console.print(f"[bold]ctx-hygiene[/bold] v{__version__}")
    console.print(f"Tier: [{tier_color}]{info.tier.value}[/{tier_color}]")
    console.print(f"LLM Provider: {config.get('llm_provider', 'none')}")
    limit = "∞" if info.is_pro else str(MAX_FREE_AUDITS_PER_MONTH)
    console.print(f"Audits this month: {month_count}/{limit}")
    console.print(f"Config: {get_config_dir()}")


@app.command()
def version() -> None:
    """Show version."""
    console.print(f"ctx-hygiene {__version__}")
