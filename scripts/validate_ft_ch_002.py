"""Reproduce FT-CH-002 on a pinned upstream input with the current analyzer.

This is a field-test fixture, not a representative accuracy benchmark.
Run in an isolated CI job. Do not commit upstream text or raw reports.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

UPSTREAM = "aa093a843da5edbf323c0b4145c9b6a0db3ecde8"
EXPECTED_SHA256 = "a88c42c6635b09b590108a5e1a161886f3dcedab824e69a080d5de8ccd575ab5"
URL = f"https://raw.githubusercontent.com/browser-use/browser-use/{UPSTREAM}/AGENTS.md"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ft-ch-002-") as tmp:
        path = Path(tmp) / "AGENTS.md"
        with urllib.request.urlopen(URL, timeout=45) as response:
            source = response.read()
        digest = hashlib.sha256(source).hexdigest()
        if digest != EXPECTED_SHA256:
            raise AssertionError(f"Unexpected upstream input SHA-256: {digest}")
        path.write_bytes(source)

        env = dict(os.environ, CONTEXT_HYGIENE_TELEMETRY="0")
        env["CONTEXT_HYGIENE_DIR"] = str(Path(tmp) / "state")
        proc = subprocess.run(
            [sys.executable, "-m", "context_hygiene.cli", "audit",
             str(path), "--format", "json"],
            capture_output=True, text=True, env=env, check=True,
        )
        report = json.loads(proc.stdout)
        from context_hygiene.parsers.detect import parse_file

        segments = parse_file(path)
        duplicates = []
        seen: dict[str, int] = {}
        for segment in segments:
            previous = seen.get(segment.content)
            if previous is not None:
                duplicates.append([previous, segment.index])
            else:
                seen[segment.content] = segment.index

        result = {
            "case": "FT-CH-002",
            "upstream_commit": UPSTREAM,
            "input_sha256": digest,
            "analyzer_version": __import__("context_hygiene").__version__,
            "segment_count": len(segments),
            "exact_duplicate_pairs": duplicates,
            "report_total_segments": report["total_segments"],
            "report_total_tokens": report["total_tokens"],
            "report_deadweight_count": len(report["deadweight"]),
            "report_tokens_recoverable": report["tokens_recoverable"],
            "report_grade": report["grade"],
            "report_staleness_score": report["staleness_score"],
        }
        print(json.dumps(result, indent=2))
        assert result["segment_count"] == 82, result
        assert result["report_total_segments"] == 82, result
        assert duplicates == [[24, 26], [25, 27]], duplicates
        assert len(report["deadweight"]) == 2, result
        assert report["tokens_recoverable"] == 277, result

        output = os.environ.get("FT_CH_002_OUTPUT")
        if output:
            Path(output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
