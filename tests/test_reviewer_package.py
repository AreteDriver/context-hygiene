"""Tests for deterministic blind-review packets and fail-closed submissions."""

import json
from copy import deepcopy
from pathlib import Path

from scripts.build_reviewer_package import check_package, render_package, write_package
from scripts.validate_reviewer_submission import validate_pair, validate_submission

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "external-cohort-pinned-v0.1.json"
PILOT = ROOT / "research" / "external-cohort-pilot-v0.1.json"
PACKAGE = ROOT / "research" / "external-cohort-pilot-review-package-v0.1"


def _template(slot: str) -> dict:
    label = "a" if slot == "reviewer_1" else "b"
    return json.loads((PACKAGE / f"reviewer-{label}" / "submission.json").read_text())


def _complete_submission(slot: str, reviewer_id: str) -> dict:
    submission = _template(slot)
    submission["reviewer_id"] = reviewer_id
    submission["reviewed_at"] = "2026-10-27T12:00:00-07:00"
    submission["blindness_attestation"] = {
        "detector_outputs_viewed": False,
        "other_reviewer_decisions_viewed": False,
        "pinned_sources_treated_as_untrusted_data": True,
    }
    for record in submission["records"]:
        license_url = f"https://example.test/licenses/{record['repository']}"
        record.update(
            {
                "source_sha256_verified": True,
                "file_license_evidence_url": license_url,
                "file_license_disposition": "verified",
                "file_license_rationale": "Synthetic test evidence covers the pinned file.",
                "content_disposition": "eligible",
                "semantic_block_count": 2,
                "content_rationale": "Synthetic test review found two instruction blocks.",
                "source_independence_disposition": "independent",
                "source_independence_rationale": "Synthetic test found no shared provenance.",
                "evidence_urls": [record["source_url"], license_url],
                "decision": "eligible",
                "decision_rationale": "All synthetic test components are positive.",
            }
        )
    return submission


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_committed_package_matches_pinned_pilot_metadata():
    files = render_package(MANIFEST, PILOT)
    assert check_package(files, PACKAGE) == []
    assert len(files) == 6
    assert len(_template("reviewer_1")["records"]) == 3
    assert len(_template("reviewer_2")["records"]) == 3


def test_generated_packets_are_separate_and_blind(tmp_path):
    files = render_package(MANIFEST, PILOT)
    write_package(files, tmp_path)
    reviewer_a = (tmp_path / "reviewer-a" / "INSTRUCTIONS.md").read_text()
    reviewer_b = (tmp_path / "reviewer-b" / "INSTRUCTIONS.md").read_text()
    assert "reviewer_1" in reviewer_a
    assert "reviewer_2" in reviewer_b
    assert "Do not run the context-hygiene analyzer" in reviewer_a
    assert _template("reviewer_1")["reviewer_slot"] == "reviewer_1"
    assert _template("reviewer_2")["reviewer_slot"] == "reviewer_2"


def test_unfilled_template_fails_closed():
    errors, _ = validate_submission(
        MANIFEST,
        PILOT,
        PACKAGE / "reviewer-a" / "submission.json",
    )
    assert "submission is missing reviewer_id" in errors
    assert any("decision is not final" in error for error in errors)
    assert any("source SHA-256 was not verified" in error for error in errors)


def test_complete_submission_passes(tmp_path):
    path = _write(tmp_path / "review.json", _complete_submission("reviewer_1", "human-a"))
    errors, submission = validate_submission(MANIFEST, PILOT, path)
    assert errors == []
    assert submission is not None


def test_manifest_tamper_and_ambiguous_evidence_fail_closed(tmp_path):
    submission = _complete_submission("reviewer_1", "human-a")
    submission["records"][0]["source_sha256"] = "0" * 64
    submission["records"][1]["file_license_disposition"] = "unknown"
    submission["records"][2]["semantic_block_count"] = 1
    path = _write(tmp_path / "review.json", submission)
    errors, _ = validate_submission(MANIFEST, PILOT, path)
    assert any("source_sha256 differs from manifest" in error for error in errors)
    assert any("file-license disposition is not final" in error for error in errors)
    assert any("requires at least two semantic blocks" in error for error in errors)


def test_blindness_attestation_is_required(tmp_path):
    submission = _complete_submission("reviewer_1", "human-a")
    submission["blindness_attestation"]["detector_outputs_viewed"] = True
    path = _write(tmp_path / "review.json", submission)
    errors, _ = validate_submission(MANIFEST, PILOT, path)
    assert "reviewer must attest that detector outputs were not viewed" in errors


def test_https_evidence_requires_a_host(tmp_path):
    submission = _complete_submission("reviewer_1", "human-a")
    submission["records"][0]["file_license_evidence_url"] = "https://"
    path = _write(tmp_path / "review.json", submission)
    errors, _ = validate_submission(MANIFEST, PILOT, path)
    assert any("file-license evidence must be an HTTPS URL" in error for error in errors)


def test_review_pair_requires_distinct_slots_and_identities(tmp_path):
    first = _write(
        tmp_path / "first.json",
        _complete_submission("reviewer_1", "same-human"),
    )
    second_data = deepcopy(_complete_submission("reviewer_1", " SAME-HUMAN "))
    second = _write(tmp_path / "second.json", second_data)
    errors = validate_pair(MANIFEST, PILOT, first, second)
    assert "review pair must contain reviewer_1 and reviewer_2 slots" in errors
    assert "review pair requires two distinct reviewer identities" in errors


def test_valid_review_pair_passes(tmp_path):
    first = _write(
        tmp_path / "first.json",
        _complete_submission("reviewer_1", "human-a"),
    )
    second = _write(
        tmp_path / "second.json",
        _complete_submission("reviewer_2", "human-b"),
    )
    assert validate_pair(MANIFEST, PILOT, first, second) == []
