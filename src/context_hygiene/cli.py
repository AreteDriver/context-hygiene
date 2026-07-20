"""CLI for context-hygiene."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
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
from context_hygiene.models import AnalysisMode, Grade, HygieneReport, Segment
from context_hygiene.parsers.detect import parse_file
from context_hygiene.reporter import (
    format_report_json,
    format_report_rich,
    format_report_sarif,
)
from context_hygiene.store import AuditStore
from context_hygiene.telemetry import track_command, track_pro_gate

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


def _get_llm_provider():
    """Get the configured LLM provider."""
    from context_hygiene.config import load_config

    config = load_config()
    provider_name = config.get("llm_provider", "ollama")

    if provider_name == "anthropic":
        from context_hygiene.llm.anthropic import AnthropicProvider

        return AnthropicProvider(model=config.get("anthropic_model", "claude-sonnet-4-6"))

    from context_hygiene.llm.ollama import OllamaProvider

    return OllamaProvider(
        model=config.get("ollama_model", "llama3.2"),
        base_url=config.get("ollama_url", "http://localhost:11434"),
    )


def _run_deep_analysis(file_path: str) -> HygieneReport:
    """Run LLM-powered deep analysis (Pro feature)."""
    from context_hygiene.analyzers.deep import (
        compression_deep,
        contradictions_deep,
        deadweight_deep,
        staleness_deep,
    )

    info = get_license()
    if not info.is_pro:
        track_pro_gate("deep analysis")
        raise LicenseError(
            "'deep analysis' requires a Pro license. "
            "Set CONTEXT_HYGIENE_LICENSE environment variable."
        )

    provider = _get_llm_provider()
    segments = parse_file(Path(file_path))
    if not segments:
        return HygieneReport(
            file_path=file_path,
            analyzed_at=datetime.now(timezone.utc),
            mode=AnalysisMode.DEEP,
        )

    staleness = staleness_deep(segments, provider)
    contras = contradictions_deep(segments, provider)
    dead = deadweight_deep(segments, provider)
    comp = compression_deep(segments, provider)

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
        mode=AnalysisMode.DEEP,
    )
    report.grade = report.compute_grade()
    return report


def _run_analysis(file_path: str, segments: list[Segment] | None = None) -> HygieneReport:
    """Run full fast analysis on a file."""
    if segments is None:
        segments = parse_file(Path(file_path))
    if not segments:
        return HygieneReport(
            file_path=file_path,
            analyzed_at=datetime.now(timezone.utc),
        )

    total_tokens = sum(s.token_estimate for s in segments)
    show_progress = len(segments) >= 20

    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing...", total=4)
            staleness = staleness_fast(segments)
            progress.update(task, advance=1, description="Staleness...")
            contras = contradictions_fast(segments)
            progress.update(task, advance=1, description="Contradictions...")
            dead = deadweight_fast(segments)
            progress.update(task, advance=1, description="Deadweight...")
            comp = compression_fast(segments)
            progress.update(task, advance=1, description="Compression...")
    else:
        staleness = staleness_fast(segments)
        contras = contradictions_fast(segments)
        dead = deadweight_fast(segments)
        comp = compression_fast(segments)

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
    output_json: bool = typer.Option(False, "--json", help="Output as JSON (deprecated, use --format)"),
    deep: bool = typer.Option(False, "--deep", help="Use LLM for deep analysis (Pro)"),
    fail_under: str = typer.Option(
        None,
        "--fail-under",
        help="Exit with error if grade is below threshold (A/B/C/D/F)",
    ),
    watch: bool = typer.Option(False, "--watch", "-w", help="Re-run when file changes"),
    fmt: str = typer.Option("rich", "--format", help="Output format: rich, json, sarif"),
) -> None:
    """Full hygiene audit: staleness + contradictions + deadweight + compression."""
    track_command("audit")

    # Validate --fail-under early
    threshold: Grade | None = None
    if fail_under is not None:
        fail_upper = fail_under.strip().upper()
        if fail_upper not in Grade.__members__:
            console.print(
                f"[red]Error:[/red] --fail-under must be one of A, B, C, D, F (got '{fail_under}')"
            )
            raise typer.Exit(2)
        threshold = Grade(fail_upper)

    def _audit_once() -> HygieneReport:
        _check_audit_quota()
        return _run_deep_analysis(file) if deep else _run_analysis(file)

    def _render(report: HygieneReport) -> None:
        output_fmt = "json" if output_json else fmt.lower()
        if output_fmt == "json":
            print(format_report_json(report))
        elif output_fmt == "sarif":
            print(format_report_sarif(report))
        else:
            format_report_rich(report, console)

    def _enforce(report: HygieneReport) -> None:
        if threshold is None:
            return
        grade_order = [Grade.F, Grade.D, Grade.C, Grade.B, Grade.A]
        report_idx = grade_order.index(report.grade)
        threshold_idx = grade_order.index(threshold)
        if report_idx < threshold_idx:
            console.print(
                f"\n[red]FAILED:[/red] Grade {report.grade.value} "
                f"is below threshold {threshold.value}"
            )
            raise typer.Exit(1)
        console.print(
            f"\n[green]PASS:[/green] Grade {report.grade.value} meets threshold {threshold.value}"
        )

    try:
        report = _audit_once()
        store = _get_store()
        try:
            store.save_audit(report)
        finally:
            store.close()

        _render(report)
        _enforce(report)

        if watch:
            file_path = Path(file)
            last_mtime = file_path.stat().st_mtime
            console.print(f"\n[dim]Watching {file} for changes... (Ctrl+C to stop)[/dim]")
            try:
                import time

                while True:
                    time.sleep(1.0)
                    try:
                        mtime = file_path.stat().st_mtime
                    except FileNotFoundError:
                        continue
                    if mtime != last_mtime:
                        last_mtime = mtime
                        console.print("\n[dim]File changed. Re-auditing...[/dim]")
                        report = _audit_once()
                        store = _get_store()
                        try:
                            store.save_audit(report)
                        finally:
                            store.close()
                        _render(report)
                        _enforce(report)
            except KeyboardInterrupt:
                console.print("\n[dim]Stopped watching.[/dim]")
    except ContextHygieneError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def score(
    file: str = typer.Argument(..., help="Conversation file to score"),
) -> None:
    """Quick staleness score (heuristic, no LLM, unlimited)."""
    track_command("score")
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
    track_command("history")
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
    track_command("status")
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
def clean(
    file: str = typer.Argument(..., help="Conversation file to clean"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview only"),
) -> None:
    """Auto-prune deadweight and stale segments."""
    track_command("clean")
    try:
        from context_hygiene.cleaner import (
            build_pruning_plan,
            segments_to_markdown,
        )

        segments = parse_file(Path(file))
        report = _run_analysis(file, segments)
        plan = build_pruning_plan(report, segments)

        console.print(plan.summary())

        if dry_run:
            console.print("\n[dim]Use --apply to write cleaned output.[/dim]")
            return

        cleaned = plan.apply()
        md = segments_to_markdown(cleaned)

        out_path = output or _default_output_path(file)
        Path(out_path).write_text(md, encoding="utf-8")
        console.print(f"\n[green]Cleaned output written to {out_path}[/green]")
    except ContextHygieneError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def watch(
    directory: str = typer.Argument(".", help="Directory to watch"),
) -> None:
    """Live file monitoring with auto-scoring (Pro)."""
    track_command("watch")
    try:
        from context_hygiene.watcher import watch_directory

        watch_directory(directory)
    except ContextHygieneError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def version() -> None:
    """Show version."""
    track_command("version")
    console.print(f"ctx-hygiene {__version__}")


@app.command()
def stats(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show local usage telemetry (requires CONTEXT_HYGIENE_TELEMETRY=1)."""
    from context_hygiene.telemetry import TelemetryStore, is_enabled

    if not is_enabled():
        console.print(
            "[dim]Telemetry is disabled. "
            "Set CONTEXT_HYGIENE_TELEMETRY=1 to enable local usage tracking.[/dim]"
        )
        return

    db_file = get_config_dir() / "telemetry.db"
    if not db_file.exists():
        console.print("[dim]No telemetry data yet.[/dim]")
        return

    ts = TelemetryStore(db_file)
    try:
        commands = ts.get_command_counts()
        pro_gates = ts.get_pro_gate_counts()
        total = ts.get_total_events()
        first = ts.get_first_event_time()
        last = ts.get_last_event_time()
        activity = ts.get_daily_activity()

        if json_output:
            import json

            data = {
                "total_events": total,
                "first_event": first,
                "last_event": last,
                "commands": commands,
                "pro_gate_hits": pro_gates,
                "daily_activity": [{"date": d, "count": c} for d, c in activity],
            }
            console.print(json.dumps(data, indent=2))
        else:
            overview = Table(title="Telemetry Overview")
            overview.add_column("Metric", style="cyan")
            overview.add_column("Value", style="green")
            overview.add_row("Total Events", str(total))
            overview.add_row("First Event", first or "n/a")
            overview.add_row("Last Event", last or "n/a")
            console.print(overview)

            if commands:
                cmd_table = Table(title="Command Usage")
                cmd_table.add_column("Command", style="cyan")
                cmd_table.add_column("Count", style="green", justify="right")
                for name, count in commands.items():
                    cmd_table.add_row(name, str(count))
                console.print(cmd_table)

            if pro_gates:
                gate_table = Table(title="Pro Feature Gate Hits")
                gate_table.add_column("Feature", style="cyan")
                gate_table.add_column("Attempts", style="yellow", justify="right")
                for name, count in pro_gates.items():
                    gate_table.add_row(name, str(count))
                console.print(gate_table)

            if activity:
                act_table = Table(title="Daily Activity (Last 7 Days)")
                act_table.add_column("Date", style="cyan")
                act_table.add_column("Events", style="green", justify="right")
                for day, count in activity:
                    act_table.add_row(day, str(count))
                console.print(act_table)
    finally:
        ts.close()


_BASH_COMPLETION = """
_ctx_hygiene_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="audit score history status clean watch version stats completion --help"

    case "${prev}" in
        audit|score|clean)
            _filedir '@(md|txt|json|jsonl)'
            return 0
            ;;
        --fail-under)
            COMPREPLY=( $(compgen -W 'A B C D F' -- "${cur}") )
            return 0
            ;;
    esac

    COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
    return 0
}
complete -F _ctx_hygiene_completion ctx-hygiene
"""

_ZSH_COMPLETION = """
#compdef ctx-hygiene

_ctx-hygiene() {
  local curcontext="$curcontext" state line
  typeset -A opt_args

  _arguments -C \\
    '1: :->command' \\
    '*: :->args'

  case "$state" in
    command)
      _values 'commands' \\
        'audit[Full hygiene audit]' \\
        'score[Quick staleness score]' \\
        'history[Show past audits]' \\
        'status[Show license and config]' \\
        'clean[Auto-prune deadweight]' \\
        'watch[Live file monitoring]' \\
        'version[Show version]' \\
        'stats[Show telemetry]' \\
        'completion[Generate shell completions]'
      ;;
    args)
      case "$line[1]" in
        audit|score|clean)
          _files -g '*.(md|txt|json|jsonl)'
          ;;
      esac
      ;;
  esac
}

compdef _ctx-hygiene ctx-hygiene
"""

_FISH_COMPLETION = """
complete -c ctx-hygiene -f
complete -c ctx-hygiene -n "__fish_use_subcommand" -a "audit" -d "Full hygiene audit"
complete -c ctx-hygiene -n "__fish_use_subcommand" -a "score" -d "Quick staleness score"
complete -c ctx-hygiene -n "__fish_use_subcommand" -a "history" -d "Show past audits"
complete -c ctx-hygiene -n "__fish_use_subcommand" -a "status" -d "Show license and config"
complete -c ctx-hygiene -n "__fish_use_subcommand" -a "clean" -d "Auto-prune deadweight"
complete -c ctx-hygiene -n "__fish_use_subcommand" -a "watch" -d "Live file monitoring"
complete -c ctx-hygiene -n "__fish_use_subcommand" -a "version" -d "Show version"
complete -c ctx-hygiene -n "__fish_use_subcommand" -a "stats" -d "Show telemetry"
complete -c ctx-hygiene -n "__fish_use_subcommand" -a "completion" -d "Generate shell completions"
complete -c ctx-hygiene -n "__fish_seen_subcommand_from audit" -s j -l json -d "Output as JSON"
complete -c ctx-hygiene -n "__fish_seen_subcommand_from audit" -l deep \
    -d "Use LLM for deep analysis"
complete -c ctx-hygiene -n "__fish_seen_subcommand_from audit" -l fail-under \
    -d "Minimum grade threshold" -xa "A B C D F"
complete -c ctx-hygiene -n "__fish_seen_subcommand_from audit" -s w -l watch \
    -d "Re-run when file changes"
complete -c ctx-hygiene -n "__fish_seen_subcommand_from clean" -s o -l output \
    -d "Output file path"
complete -c ctx-hygiene -n "__fish_seen_subcommand_from clean" -l apply \
    -d "Apply changes"
complete -c ctx-hygiene -n "__fish_seen_subcommand_from history" -s n -l limit \
    -d "Number of entries"
complete -c ctx-hygiene -n "__fish_seen_subcommand_from stats" -l json -d "Output as JSON"
"""


@app.command()
def completion(
    shell: str = typer.Argument(..., help="Shell: bash, zsh, fish"),
) -> None:
    """Generate shell completion script."""
    shell = shell.lower().strip()
    scripts = {
        "bash": _BASH_COMPLETION,
        "zsh": _ZSH_COMPLETION,
        "fish": _FISH_COMPLETION,
    }
    if shell not in scripts:
        console.print(
            f"[red]Error:[/red] Unsupported shell '{shell}'. Choose from: bash, zsh, fish"
        )
        raise typer.Exit(1)
    console.print(scripts[shell].strip())
    console.print(f"\n[dim]Add to your {shell}rc:[/dim]")
    if shell == "bash":
        console.print('  eval "$(ctx-hygiene completion bash)"')
    elif shell == "zsh":
        console.print('  eval "$(ctx-hygiene completion zsh)"')
    elif shell == "fish":
        console.print("  ctx-hygiene completion fish | source")


def _default_output_path(file_path: str) -> str:
    """Generate default output path: file.cleaned.md."""
    p = Path(file_path)
    return str(p.parent / f"{p.stem}.cleaned{p.suffix}")
