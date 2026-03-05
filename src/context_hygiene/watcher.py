"""File watcher for live hygiene monitoring (Pro feature)."""

from __future__ import annotations

import time
from pathlib import Path

from context_hygiene.analyzers.staleness import staleness_fast
from context_hygiene.exceptions import ContextHygieneError
from context_hygiene.gates import require_pro
from context_hygiene.parsers.detect import parse_file


@require_pro("watch")
def watch_directory(
    directory: str,
    callback: object | None = None,
    interval: float = 2.0,
) -> None:
    """Watch a directory for file changes and auto-score.

    Uses watchdog if available, falls back to polling.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise ContextHygieneError(f"Not a directory: {directory}")

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        _watch_with_watchdog(dir_path, callback, Observer, FileSystemEventHandler)
    except ImportError:
        _watch_with_polling(dir_path, callback, interval)


def _watch_with_watchdog(
    dir_path: Path,
    callback: object | None,
    observer_cls: type,
    handler_cls: type,
) -> None:
    """Watch using watchdog library."""
    from rich.console import Console

    console = Console()

    class HygieneHandler(handler_cls):  # type: ignore[misc]
        def on_modified(self, event):
            if event.is_directory:
                return
            path = Path(event.src_path)
            if path.suffix.lower() in {".md", ".txt", ".json"}:
                _score_file(str(path), console)

    observer = observer_cls()
    observer.schedule(HygieneHandler(), str(dir_path), recursive=True)
    observer.start()
    console.print(f"[green]Watching[/green] {dir_path} for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def _watch_with_polling(
    dir_path: Path,
    callback: object | None,
    interval: float,
) -> None:
    """Fallback polling watcher."""
    from rich.console import Console

    console = Console()
    console.print(
        f"[yellow]watchdog not installed, using polling[/yellow] (interval: {interval}s)"
    )
    console.print(f"[green]Watching[/green] {dir_path} for changes...")

    mtimes: dict[str, float] = {}
    # Initial scan
    for f in dir_path.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".md", ".txt", ".json"}:
            mtimes[str(f)] = f.stat().st_mtime

    try:
        while True:
            time.sleep(interval)
            for f in dir_path.rglob("*"):
                if not f.is_file():
                    continue
                if f.suffix.lower() not in {".md", ".txt", ".json"}:
                    continue
                key = str(f)
                mtime = f.stat().st_mtime
                if key not in mtimes or mtimes[key] < mtime:
                    mtimes[key] = mtime
                    _score_file(key, console)
    except KeyboardInterrupt:
        pass


def _score_file(file_path: str, console: object) -> None:
    """Score a single file and print result."""
    try:
        segments = parse_file(Path(file_path))
        if not segments:
            return
        staleness = staleness_fast(segments)
        avg = sum(s.score for s in staleness) / len(staleness)
        total_tokens = sum(s.token_estimate for s in segments)

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

        console.print(  # type: ignore[union-attr]
            f"[dim]{file_path}[/dim] → "
            f"[{color}]{grade}[/{color}] "
            f"({avg:.2f}, {total_tokens:,} tokens)"
        )
    except ContextHygieneError:
        pass
