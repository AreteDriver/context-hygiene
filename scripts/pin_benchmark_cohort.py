"""Pin external benchmark candidates to immutable source commits and SHA-256.

Reads a reviewed candidate list (JSON); writes a manifest without source content.
Uses GitHub REST with stdlib only. Never runs repository code or the analyzer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def api_json(url: str, token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "context-hygiene-benchmark"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def api_bytes(url: str, token: str | None) -> bytes:
    headers = {"Accept": "application/vnd.github.raw+json", "User-Agent": "context-hygiene-benchmark"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def pin_one(item: dict, token: str | None) -> dict:
    repo = item["repository"]
    path = item["path"]
    if len(repo.split("/")) != 2 or path not in ("AGENTS.md", "CLAUDE.md"):
        raise ValueError(f"invalid repository or root file: {repo} {path}")
    base = f"https://api.github.com/repos/{repo}"
    metadata = api_json(base, token)
    if metadata.get("private") or metadata.get("archived") or metadata.get("fork"):
        raise ValueError(f"private, archived or fork repository: {repo}")
    default_branch = metadata["default_branch"]
    branch = api_json(f"{base}/branches/{urllib.parse.quote(default_branch, safe='')}", token)
    commit = branch["commit"]["sha"]
    quoted_path = urllib.parse.quote(path, safe="")
    blob = api_bytes(f"{base}/contents/{quoted_path}?ref={commit}", token)
    # GitHub raw content is bytes, so hash the exact analyzed input.
    return {
        "repository": repo,
        "path": path,
        "source_commit": commit,
        "source_url": f"https://github.com/{repo}/blob/{commit}/{path}",
        "sha256": hashlib.sha256(blob).hexdigest(),
        "bytes": len(blob),
        "lines": len(blob.splitlines()),
        "license_spdx": (metadata.get("license") or {}).get("spdx_id"),
        "owner": metadata["owner"]["login"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pinned_unlabeled",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", type=Path, help="JSON list of reviewed repository/path pairs")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    if not isinstance(candidates, list):
        parser.error("candidates must be a JSON list")
    seen: set[str] = set()
    records = []
    token = os.environ.get("GITHUB_TOKEN")
    for item in candidates:
        repo = item["repository"]
        if repo in seen:
            raise ValueError(f"duplicate repository: {repo}")
        seen.add(repo)
        try:
            records.append(pin_one(item, token))
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError, ValueError) as exc:
            print(f"pin failed for {repo}: {exc}", file=sys.stderr)
            return 1  # Fail closed: never emit a partial frozen manifest.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "schema": "context-hygiene.external-cohort.v0.1",
        "status": "pinned_unlabeled_not_frozen",
        "records": records,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Pinned {len(records)} files; labels and evaluation remain pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
