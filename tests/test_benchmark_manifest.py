"""Regression tests for fail-closed cohort manifest validation."""

import hashlib
import json
from pathlib import Path

from scripts.validate_benchmark_manifest import validate_manifest


def _manifest(tmp_path: Path) -> Path:
    records = []
    for i in range(20):
        repo = f"owner{i}/project"
        commit = f"{i + 1:040x}"
        records.append(
            {
                "repository": repo,
                "owner": f"owner{i}",
                "path": "AGENTS.md",
                "source_commit": commit,
                "source_url": f"https://github.com/{repo}/blob/{commit}/AGENTS.md",
                "sha256": f"{i + 1:064x}",
                "bytes": 10,
                "license_spdx": "MIT",
            }
        )
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"status": "pinned_unlabeled_not_frozen", "records": records}))
    return path


def test_valid_manifest_and_exact_checksum(tmp_path):
    path = _manifest(tmp_path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert validate_manifest(path, expected_sha256=digest) == []


def test_rejects_modified_manifest_bytes(tmp_path):
    path = _manifest(tmp_path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    path.write_bytes(path.read_bytes() + b" ")
    errors = validate_manifest(path, expected_sha256=digest)
    assert errors == ["manifest byte-level SHA-256 mismatch"]


def test_rejects_duplicate_owner(tmp_path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text())
    data["records"][1]["owner"] = data["records"][0]["owner"]
    path.write_text(json.dumps(data))
    assert any("invalid repository/owner" in e for e in validate_manifest(path))


def test_rejects_unpinned_source_url(tmp_path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text())
    data["records"][0]["source_url"] = "https://github.com/owner0/project/blob/main/AGENTS.md"
    path.write_text(json.dumps(data))
    assert any("source URL mismatch" in e for e in validate_manifest(path))


def test_rejects_missing_record(tmp_path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text())
    data["records"].pop()
    path.write_text(json.dumps(data))
    assert validate_manifest(path) == ["expected exactly 20 records"]


def test_committed_manifest_is_exact_pinned_artifact():
    manifest = (
        Path(__file__).resolve().parents[1] / "research" / "external-cohort-pinned-v0.1.json"
    )
    expected = "30577f29eba1d99bdcbeababcf01a09bc2c1f26d98a760e306cbb43405379c22"
    assert validate_manifest(manifest, expected_sha256=expected) == []
