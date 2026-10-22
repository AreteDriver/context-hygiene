"""Tests for eligibility register integrity and premature approval prevention."""

import json
from pathlib import Path

from scripts.validate_eligibility_register import validate_register


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "external-cohort-pinned-v0.1.json"
REGISTER = ROOT / "research" / "external-cohort-eligibility-register-v0.1.json"


def test_current_pending_register_validates():
    assert validate_register(MANIFEST, REGISTER) == []


def test_rejects_unsubstantiated_final_eligibility(tmp_path):
    register = json.loads(REGISTER.read_text())
    register["records"][0]["final_eligibility"] = "eligible"
    path = tmp_path / "register.json"
    path.write_text(json.dumps(register))
    errors = validate_register(MANIFEST, path)
    assert any("finalized without file-license evidence" in error for error in errors)
    assert any("finalized without two reviewer identities" in error for error in errors)
    assert any("finalized without adjudication record" in error for error in errors)


def test_rejects_modified_source_commit(tmp_path):
    register = json.loads(REGISTER.read_text())
    register["records"][0]["source_commit"] = "0" * 40
    path = tmp_path / "register.json"
    path.write_text(json.dumps(register))
    assert any("source_commit differs" in e for e in validate_register(MANIFEST, path))


def test_rejects_missing_record(tmp_path):
    register = json.loads(REGISTER.read_text())
    register["records"].pop()
    path = tmp_path / "register.json"
    path.write_text(json.dumps(register))
    assert any("record count" in e for e in validate_register(MANIFEST, path))
