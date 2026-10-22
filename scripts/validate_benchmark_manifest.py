"""Validate the durable external-cohort manifest before any evaluation.

No network calls, no upstream execution, no analyzer invocation.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def validate_manifest(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    records = data.get("records")
    if not isinstance(records, list) or len(records) != 20:
        return ["expected exactly 20 records"]
    if data.get("status") != "pinned_unlabeled_not_frozen":
        errors.append("unexpected manifest status")
    seen_repos: set[str] = set()
    seen_owners: set[str] = set()
    for i, record in enumerate(records):
        repo = record.get("repository", "")
        owner = record.get("owner", "")
        commit = record.get("source_commit", "")
        digest = record.get("sha256", "")
        file_path = record.get("path", "")
        if repo in seen_repos or owner in seen_owners:
            errors.append(f"record {i}: repeated repository or owner")
        seen_repos.add(repo)
        seen_owners.add(owner)
        if file_path not in {"AGENTS.md", "CLAUDE.md"}:
            errors.append(f"record {i}: invalid root file")
        if not _HEX40.fullmatch(commit):
            errors.append(f"record {i}: invalid commit")
        if not _HEX64.fullmatch(digest):
            errors.append(f"record {i}: invalid SHA-256")
        if record.get("source_url") != f"https://github.com/{repo}/blob/{commit}/{file_path}":
            errors.append(f"record {i}: source URL mismatch")
        if not isinstance(record.get("bytes"), int) or record["bytes"] <= 0:
            errors.append(f"record {i}: invalid byte length")
        if not record.get("license_spdx"):
            errors.append(f"record {i}: license metadata missing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors = validate_manifest(args.manifest)
    for error in errors:
        print(error)
    if errors:
        return 1
    print("Manifest shape and source links validated; file licenses and independence still require review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
