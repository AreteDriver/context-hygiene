"""Tests for read-only cohort readiness reporting."""

import json
from pathlib import Path

from scripts.cohort_readiness import build_report

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "external-cohort-pinned-v0.1.json"
REGISTER = ROOT / "research" / "external-cohort-eligibility-register-v0.1.json"


def test_live_register_is_blocked_without_mutation():
    before = REGISTER.read_bytes()
    report = build_report(MANIFEST, REGISTER)
    assert report["status"] == "blocked"
    assert report["detector_evaluation_authorized"] is False
    assert report["source_count"] == 20
    assert len(report["sources"]) == 20
    assert all("reviewer_1" in row["missing"] for row in report["sources"])
    assert all("reviewer_2" in row["missing"] for row in report["sources"])
    assert REGISTER.read_bytes() == before


def test_readiness_is_deterministic():
    assert json.dumps(build_report(MANIFEST, REGISTER), sort_keys=True) == json.dumps(
        build_report(MANIFEST, REGISTER), sort_keys=True
    )


def test_incomplete_record_reports_missing_fields(tmp_path):
    data = json.loads(REGISTER.read_text(encoding="utf-8"))
    data["records"][0]["file_license_evidence_url"] = "https://example.test/evidence"
    path = tmp_path / "register.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    report = build_report(MANIFEST, path)
    row = next(r for r in report["sources"] if r["repository"] == data["records"][0]["repository"])
    assert "file_license_evidence_url" not in row["missing"]
    assert "final_eligibility" in row["missing"]
    assert report["status"] == "blocked"


def test_nested_reviewer_gaps_are_visible(tmp_path):
    data = json.loads(REGISTER.read_text(encoding="utf-8"))
    data["records"][0]["reviewer_1"] = {
        "reviewer_id": "synthetic-test-reviewer",
        "decision": "eligible",
        "source_sha256_verified": False,
    }
    path = tmp_path / "register.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    report = build_report(MANIFEST, path)
    row = next(r for r in report["sources"] if r["repository"] == data["records"][0]["repository"])
    assert "reviewer_1.reviewed_at" in row["missing"]
    assert "reviewer_1.source_sha256_verified" in row["missing"]
    assert report["status"] == "blocked"


def test_cli_malformed_json_fails_closed(tmp_path, monkeypatch, capsys):
    from scripts.cohort_readiness import main

    path = tmp_path / "broken.json"
    path.write_text("{invalid", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv", ["cohort_readiness", str(MANIFEST), str(path)]
    )
    assert main() == 1
    assert '"status": "blocked"' in capsys.readouterr().out
