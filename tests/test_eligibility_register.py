"""Tests for eligibility register integrity and premature approval prevention."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "external-cohort-pinned-v0.1.json"
REGISTER = ROOT / "research" / "external-cohort-eligibility-register-v0.1.json"


def validate_register(manifest, register, **kwargs):
    from scripts.validate_eligibility_register import validate_register as validate

    return validate(manifest, register, **kwargs)


def complete_register(*, disagreement=False):
    register = json.loads(REGISTER.read_text())
    register["status"] = "adjudicated"
    for record in register["records"]:
        first = "eligible"
        second = "ineligible" if disagreement else first
        record["file_license_evidence_url"] = "https://example.test/license-evidence"
        record["file_license_disposition"] = "verified"
        record["content_disposition"] = "eligible"
        record["source_independence_disposition"] = "independent"
        record["reviewer_1"] = {
            "reviewer_id": "reviewer-a",
            "reviewed_at": "2026-10-23T10:00:00Z",
            "decision": first,
            "rationale": "Pinned source and eligibility criteria reviewed.",
            "evidence_urls": ["https://example.test/review-a"],
            "source_sha256_verified": True,
        }
        record["reviewer_2"] = {
            "reviewer_id": "reviewer-b",
            "reviewed_at": "2026-10-23T11:00:00Z",
            "decision": second,
            "rationale": "Independent review of the pinned source completed.",
            "evidence_urls": ["https://example.test/review-b"],
            "source_sha256_verified": True,
        }
        record["adjudication"] = {
            "adjudicator_id": "adjudicator-c",
            "adjudicated_at": "2026-10-23T12:00:00Z",
            "decision": "eligible",
            "rationale": "Eligibility criteria are satisfied.",
            "reviewer_disagreement": disagreement,
        }
        record["final_eligibility"] = "eligible"
    return register


def write_register(tmp_path, register):
    path = tmp_path / "register.json"
    path.write_text(json.dumps(register))
    return path


def test_current_pending_register_validates():
    assert validate_register(MANIFEST, REGISTER) == []


def test_rejects_unsubstantiated_final_eligibility(tmp_path):
    register = json.loads(REGISTER.read_text())
    register["records"][0]["final_eligibility"] = "eligible"
    path = write_register(tmp_path, register)
    errors = validate_register(MANIFEST, path)
    assert any("finalized without file-license evidence" in error for error in errors)
    assert any("reviewer_1 must be a structured review" in error for error in errors)
    assert any("reviewer_2 must be a structured review" in error for error in errors)


def test_rejects_modified_source_commit(tmp_path):
    register = json.loads(REGISTER.read_text())
    register["records"][0]["source_commit"] = "0" * 40
    path = write_register(tmp_path, register)
    assert any("source_commit differs" in e for e in validate_register(MANIFEST, path))


def test_rejects_missing_record(tmp_path):
    register = json.loads(REGISTER.read_text())
    register["records"].pop()
    path = write_register(tmp_path, register)
    assert any("record count" in e for e in validate_register(MANIFEST, path))


def test_complete_register_requires_all_records_and_adjudicated_status():
    errors = validate_register(MANIFEST, REGISTER, require_complete=True)
    assert any("register is not adjudicated" in error for error in errors)
    assert sum("eligibility review is incomplete" in error for error in errors) == 20


def test_accepts_structured_independent_reviews_and_adjudication(tmp_path):
    path = write_register(tmp_path, complete_register())
    assert validate_register(MANIFEST, path, require_complete=True) == []


def test_conflict_requires_independent_adjudicator(tmp_path):
    register = complete_register(disagreement=True)
    register["records"][0]["adjudication"]["adjudicator_id"] = "reviewer-a"
    path = write_register(tmp_path, register)
    errors = validate_register(MANIFEST, path, require_complete=True)
    assert any("conflict requires an independent adjudicator" in error for error in errors)


def test_rejects_duplicate_reviewer_identity(tmp_path):
    register = complete_register()
    register["records"][0]["reviewer_2"]["reviewer_id"] = "reviewer-a"
    path = write_register(tmp_path, register)
    errors = validate_register(MANIFEST, path, require_complete=True)
    assert any("independent reviewer identities are required" in error for error in errors)


def test_rejects_invalid_review_provenance(tmp_path):
    register = complete_register()
    review = register["records"][0]["reviewer_1"]
    review["reviewed_at"] = "2026-10-23"
    review["evidence_urls"] = []
    review["source_sha256_verified"] = False
    path = write_register(tmp_path, register)
    errors = validate_register(MANIFEST, path, require_complete=True)
    assert any("timezone-aware reviewed_at" in error for error in errors)
    assert any("requires HTTPS evidence_urls" in error for error in errors)
    assert any("did not verify source_sha256" in error for error in errors)


def test_rejects_incomplete_component_dispositions(tmp_path):
    register = complete_register()
    record = register["records"][0]
    record["file_license_disposition"] = "pending"
    record["content_disposition"] = "preliminary_instructions_present"
    record["source_independence_disposition"] = "pending"
    path = write_register(tmp_path, register)
    errors = validate_register(MANIFEST, path, require_complete=True)
    assert any("file-license disposition is not final" in error for error in errors)
    assert any("content disposition is not final" in error for error in errors)
    assert any("source-independence disposition is not final" in error for error in errors)


def test_malformed_review_reports_errors_without_crashing(tmp_path):
    register = complete_register()
    register["records"][0]["reviewer_1"].pop("decision")
    path = write_register(tmp_path, register)
    errors = validate_register(MANIFEST, path, require_complete=True)
    assert any("reviewer_1 has invalid decision" in error for error in errors)
    assert any("disagreement flag is incorrect" in error for error in errors)


def test_freeze_is_deterministic_and_remains_unlabeled(tmp_path):
    from scripts.freeze_eligible_cohort import build_freeze

    register = complete_register()
    register["records"][0]["reviewer_1"]["decision"] = "ineligible"
    register["records"][0]["reviewer_2"]["decision"] = "ineligible"
    register["records"][0]["adjudication"].update(
        decision="ineligible",
        rationale="The file does not meet the preregistered content criterion.",
    )
    register["records"][0]["final_eligibility"] = "ineligible"
    path = write_register(tmp_path, register)
    freeze = build_freeze(MANIFEST, path)
    assert freeze == build_freeze(MANIFEST, path)
    assert freeze["status"] == "frozen_unlabeled"
    assert freeze["detector_evaluation_authorized"] is False
    assert len(freeze["eligible_records"]) == 19
    assert len(freeze["excluded_records"]) == 1
    assert freeze["eligibility_register_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_freeze_refuses_current_pending_register():
    from scripts.freeze_eligible_cohort import build_freeze

    with pytest.raises(ValueError, match="eligibility register is not adjudicated"):
        build_freeze(MANIFEST, REGISTER)
