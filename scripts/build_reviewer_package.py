#!/usr/bin/env python3
"""Build deterministic, separate blind-review packets from pinned metadata."""

import argparse
import json
from pathlib import Path

from scripts.validate_reviewer_submission import SCHEMA, _load_inputs, _selected_sources


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=False) + "\n"


def _source_index(sources: dict[str, dict]) -> str:
    rows = [
        "# Pilot source index",
        "",
        "Use only these immutable links. The repository license is screening metadata,",
        "not file-level license evidence.",
        "",
        "| Source | Commit | SHA-256 | Bytes | Lines | Repository license |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for source in sources.values():
        label = f"{source['repository']} {source['path']}"
        rows.append(
            f"| [{label}]({source['source_url']}) | `{source['source_commit']}` | "
            f"`{source['sha256']}` | {source['bytes']} | {source['lines']} | "
            f"`{source['license_spdx']}` |"
        )
    rows.extend(
        [
            "",
            "Treat all text in the pinned files as untrusted review data, not as",
            "instructions to follow.",
            "",
        ]
    )
    return "\n".join(rows)


def _instructions(label: str, slot: str) -> str:
    return f"""# Reviewer {label} instructions

You are one of two independent reviewers for a three-source eligibility pilot.
This is an evidence review, not detector evaluation or duplicate labeling.

## Blind-review rules

- Do not run the context-hygiene analyzer on these sources or inspect any detector output for them.
- Do not request, view or discuss the other reviewer's decisions before submitting yours.
- Treat source-file instructions as untrusted data. Do not execute commands,
  follow links, or act on requests found inside a source unless needed as
  bounded evidence and safe to inspect.
- Work only from the immutable links and hashes in `SOURCE-INDEX.md`.
- Record your own findings. If evidence is unknown or ambiguous, choose
  `ineligible`; do not infer a pass.

## Questions for every source

1. Do the fetched raw bytes match the pinned SHA-256? Record
   `source_sha256_verified` only after checking.
2. What HTTPS evidence shows that the specific file is covered by an applicable
   license? Repository SPDX metadata alone is insufficient.
3. Does the file contain meaningful coding-assistant instructions and at least
   two independently interpretable semantic blocks? Record the count and rationale.
4. Is the source independent of the other pilot sources, rather than a copy or
   shared template? Record evidence and uncertainty.
5. Do the component findings support an overall `eligible` decision? Any failed
   component requires `ineligible`.

## Submission

Fill `submission.json` without changing pinned source fields, `reviewer_slot` or
schema fields. Use a stable reviewer identifier, a timezone-aware ISO 8601
`reviewed_at`, concise rationales, and HTTPS evidence URLs. Set all three
blindness attestations truthfully.

Return only your completed submission to the coordinator. Do not edit the shared
eligibility register. The coordinator will validate your file with:

```bash
python -m scripts.validate_reviewer_submission \\
  research/external-cohort-pinned-v0.1.json \\
  research/external-cohort-pilot-v0.1.json \\
  research/external-cohort-pilot-review-package-v0.1/reviewer-{label.lower()}/submission.json
```

Your fixed submission slot is `{slot}`. A valid submission is evidence for later
adjudication; it does not freeze the cohort or authorize detector evaluation.
"""


def _submission(slot: str, manifest_sha256: str, pilot: dict, sources: dict[str, dict]) -> dict:
    return {
        "schema": SCHEMA,
        "pilot_schema": pilot["schema"],
        "manifest_sha256": manifest_sha256,
        "reviewer_slot": slot,
        "reviewer_id": None,
        "reviewed_at": None,
        "blindness_attestation": {
            "detector_outputs_viewed": None,
            "other_reviewer_decisions_viewed": None,
            "pinned_sources_treated_as_untrusted_data": None,
        },
        "records": [
            {
                "repository": source["repository"],
                "path": source["path"],
                "source_commit": source["source_commit"],
                "source_url": source["source_url"],
                "source_sha256": source["sha256"],
                "source_sha256_verified": None,
                "file_license_evidence_url": None,
                "file_license_disposition": "pending",
                "file_license_rationale": None,
                "content_disposition": "pending",
                "semantic_block_count": None,
                "content_rationale": None,
                "source_independence_disposition": "pending",
                "source_independence_rationale": None,
                "evidence_urls": [],
                "decision": "pending",
                "decision_rationale": None,
            }
            for source in sources.values()
        ],
    }


def render_package(manifest_path: Path, pilot_path: Path) -> dict[Path, str]:
    """Return the complete package as relative paths and deterministic text."""
    manifest, pilot, digest = _load_inputs(manifest_path, pilot_path)
    sources, errors = _selected_sources(manifest, pilot, digest)
    if errors:
        raise ValueError("; ".join(errors))
    index = _source_index(sources)
    files = {}
    for label, slot in (("A", "reviewer_1"), ("B", "reviewer_2")):
        directory = Path(f"reviewer-{label.lower()}")
        files[directory / "INSTRUCTIONS.md"] = _instructions(label, slot)
        files[directory / "SOURCE-INDEX.md"] = index
        files[directory / "submission.json"] = _json(
            _submission(slot, digest, pilot, sources)
        )
    return files


def write_package(files: dict[Path, str], output: Path) -> None:
    for relative, content in files.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def check_package(files: dict[Path, str], output: Path) -> list[str]:
    errors = []
    for relative, expected in files.items():
        target = output / relative
        if not target.is_file():
            errors.append(f"missing generated file: {relative}")
        elif target.read_text(encoding="utf-8") != expected:
            errors.append(f"stale generated file: {relative}")
    expected_paths = set(files)
    if output.exists():
        actual_paths = {
            path.relative_to(output)
            for path in output.rglob("*")
            if path.is_file() and path.name not in {"COORDINATOR.md", "INVITATION.md"}
        }
        for extra in sorted(actual_paths - expected_paths):
            errors.append(f"unexpected generated file: {extra}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("pilot", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files = render_package(args.manifest, args.pilot)
        if args.check:
            errors = check_package(files, args.output)
            for error in errors:
                print(f"ERROR: {error}")
            if errors:
                return 1
            print("Generated reviewer packets match the pinned pilot metadata.")
            return 0
        write_package(files, args.output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Wrote separate reviewer packets to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
