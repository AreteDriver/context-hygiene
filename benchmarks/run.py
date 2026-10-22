#!/usr/bin/env python3
"""Benchmark suite for context-hygiene analysis pipeline.

Usage:
    python benchmarks/run.py           # Run all benchmarks
    python benchmarks/run.py --quick   # Run only small fixtures
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from pathlib import Path

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_hygiene.analyzers.compression import compression_fast
from context_hygiene.analyzers.contradictions import contradictions_fast
from context_hygiene.analyzers.deadweight import deadweight_fast
from context_hygiene.analyzers.staleness import staleness_fast
from context_hygiene.parsers.detect import parse_file


BENCHMARKS_DIR = Path(__file__).parent
FIXTURES_DIR = BENCHMARKS_DIR / "fixtures"


class BenchmarkResult:
    def __init__(
        self,
        name: str,
        total_tokens: int,
        segments: int,
        parse_ms: float,
        staleness_ms: float,
        contradiction_ms: float,
        deadweight_ms: float,
        compression_ms: float,
        total_ms: float,
        peak_memory_kb: int,
    ):
        self.name = name
        self.total_tokens = total_tokens
        self.segments = segments
        self.parse_ms = parse_ms
        self.staleness_ms = staleness_ms
        self.contradiction_ms = contradiction_ms
        self.deadweight_ms = deadweight_ms
        self.compression_ms = compression_ms
        self.total_ms = total_ms
        self.peak_memory_kb = peak_memory_kb


def run_benchmark(fixture_path: Path) -> BenchmarkResult:
    """Run full analysis pipeline on a fixture and measure performance."""
    name = fixture_path.stem

    # Parse
    start = time.perf_counter()
    segments = parse_file(fixture_path)
    parse_ms = (time.perf_counter() - start) * 1000
    total_tokens = sum(s.token_estimate for s in segments)

    # Staleness
    start = time.perf_counter()
    staleness_fast(segments)
    staleness_ms = (time.perf_counter() - start) * 1000

    # Contradictions
    start = time.perf_counter()
    contradictions_fast(segments)
    contradiction_ms = (time.perf_counter() - start) * 1000

    # Deadweight
    start = time.perf_counter()
    deadweight_fast(segments)
    deadweight_ms = (time.perf_counter() - start) * 1000

    # Compression
    start = time.perf_counter()
    compression_fast(segments)
    compression_ms = (time.perf_counter() - start) * 1000

    total_ms = parse_ms + staleness_ms + contradiction_ms + deadweight_ms + compression_ms

    # Memory: run full pipeline under tracemalloc
    tracemalloc.start()
    _ = parse_file(fixture_path)
    staleness_fast(segments)
    contradictions_fast(segments)
    deadweight_fast(segments)
    compression_fast(segments)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_kb = int(peak / 1024)

    return BenchmarkResult(
        name=name,
        total_tokens=total_tokens,
        segments=len(segments),
        parse_ms=parse_ms,
        staleness_ms=staleness_ms,
        contradiction_ms=contradiction_ms,
        deadweight_ms=deadweight_ms,
        compression_ms=compression_ms,
        total_ms=total_ms,
        peak_memory_kb=peak_kb,
    )


def _ensure_fixtures(quick: bool) -> list[Path]:
    """Generate fixtures if they don't exist."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    specs = [
        ("small_1k", 1000),
        ("medium_5k", 5000),
        ("large_10k", 10000),
    ]
    if not quick:
        specs.extend([
            ("xlarge_50k", 50000),
            ("huge_100k", 100000),
        ])

    fixtures = []
    for name, tokens in specs:
        path = FIXTURES_DIR / f"{name}.md"
        if not path.exists():
            print(f"Generating fixture: {name} ({tokens} tokens)...")
            import subprocess

            subprocess.run(
                [sys.executable, str(BENCHMARKS_DIR / "generate_fixture.py"), "--tokens", str(tokens), "--output", str(path)],
                check=True,
            )
        fixtures.append(path)

    return fixtures


def _print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results as a formatted table."""
    header = (
        f"{'Fixture':<15} {'Tokens':>8} {'Segs':>6} {'Parse':>8} {'Stale':>8} "
        f"{'Contra':>8} {'Dead':>8} {'Comp':>8} {'Total':>8} {'Mem KB':>10}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        print(
            f"{r.name:<15} {r.total_tokens:>8,} {r.segments:>6} "
            f"{r.parse_ms:>7.1f}ms {r.staleness_ms:>7.1f}ms "
            f"{r.contradiction_ms:>7.1f}ms {r.deadweight_ms:>7.1f}ms "
            f"{r.compression_ms:>7.1f}ms {r.total_ms:>7.1f}ms "
            f"{r.peak_memory_kb:>10,}"
        )

    print()
    print("Summary:")
    total_time = sum(r.total_ms for r in results)
    total_tokens = sum(r.total_tokens for r in results)
    print(f"  Total time: {total_time:.0f}ms")
    print(f"  Total tokens: {total_tokens:,}")
    if total_time > 0:
        print(f"  Throughput: {total_tokens / (total_time / 1000):,.0f} tokens/sec")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark context-hygiene analysis pipeline")
    parser.add_argument("--quick", action="store_true", help="Run only small fixtures")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", type=Path, help="Write JSON results to file")
    args = parser.parse_args()

    fixtures = _ensure_fixtures(quick=args.quick)
    results = []

    for fixture in fixtures:
        print(f"Benchmarking {fixture.name}...", file=sys.stderr)
        result = run_benchmark(fixture)
        results.append(result)

    if args.json or args.output:
        data = [
            {
                "fixture": r.name,
                "total_tokens": r.total_tokens,
                "segments": r.segments,
                "parse_ms": r.parse_ms,
                "staleness_ms": r.staleness_ms,
                "contradiction_ms": r.contradiction_ms,
                "deadweight_ms": r.deadweight_ms,
                "compression_ms": r.compression_ms,
                "total_ms": r.total_ms,
                "peak_memory_kb": r.peak_memory_kb,
            }
            for r in results
        ]
        json_text = json.dumps(data, indent=2)
        if args.output:
            args.output.write_text(json_text, encoding="utf-8")
        else:
            print(json_text)
    else:
        _print_results(results)


if __name__ == "__main__":
    main()
