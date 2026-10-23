#!/usr/bin/env python3
"""Fail-closed validation of the external cohort eligibility review register."""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

ALLOWED = {"pending", "eligible", "ineligible", "needs_adjudication"}
FINAL = {"eligible", "ineligible"}
REGISTER_STATUSES = {"awaiting_independent_review", "needs_adjudication", "adjudicated"}
FILE_LICENSE_FINAL = {"verified", "ineligible"}
INDEPENDENCE_FINAL = {"independent", "not_independent"}


def _valid_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _validate_reviewer(name: str, slot: str, reviewer: object) -> list[str]:
    prefix = f"{name}: {slot}"
    if not isinstance(reviewer, dict):
        return [f"{prefix} must be a structured review"]
    errors = []
    if not isinstance(reviewer.get("reviewer_id"), str) or not reviewer["reviewer_id"].strip():
        errors.append(f"{prefix} missing reviewer_id")
    if reviewer.get("decision") not in FINAL:
        errors.append(f"{prefix} has invalid decision")
    if not _valid_timestamp(reviewer.get("reviewed_at")):
        errors.append(f"{prefix} missing timezone-aware reviewed_at")
    if not isinstance(reviewer.get("rationale"), str) or not reviewer["rationale"].strip():
        errors.append(f"{prefix} missing rationale")
    evidence = reviewer.get("evidence_urls")
    if (
        not isinstance(evidence, list)
        or not evidence
        or not all(isinstance(url, str) and url.startswith("https://") for url in evidence)
    ):
        errors.append(f"{prefix} requires HTTPS evidence_urls")
    if reviewer.get("source_sha256_verified") is not True:
        errors.append(f"{prefix} did not verify source_sha256")
    return errors


def _validate_adjudication(name: str, entry: dict, reviewer_ids: set[object]) -> list[str]:
    prefix = f"{name}: adjudication"
    adjudication = entry.get("adjudication")
    if not isinstance(adjudication, dict):
        return [f"{prefix} must be a structured record"]
    errors = []
    adjudicator = adjudication.get("adjudicator_id")
    if not isinstance(adjudicator, str) or not adjudicator.strip():
        errors.append(f"{prefix} missing adjudicator_id")
    if not _valid_timestamp(adjudication.get("adjudicated_at")):
        errors.append(f"{prefix} missing timezone-aware adjudicated_at")
    if adjudication.get("decision") not in FINAL:
        errors.append(f"{prefix} has invalid decision")
    if adjudication.get("decision") != entry.get("final_eligibility"):
        errors.append(f"{prefix} decision differs from final_eligibility")
    if not isinstance(adjudication.get("rationale"), str) or not adjudication["rationale"].strip():
        errors.append(f"{prefix} missing rationale")
    first_decision = entry["reviewer_1"].get("decision")
    second_decision = entry["reviewer_2"].get("decision")
    reviews_disagree = first_decision != second_decision
    if adjudication.get("reviewer_disagreement") is not reviews_disagree:
        errors.append(f"{prefix} disagreement flag is incorrect")
    if reviews_disagree and adjudicator in reviewer_ids:
        errors.append(f"{prefix} conflict requires an independent adjudicator")
    if not reviews_disagree and adjudication.get("decision") != first_decision:
        errors.append(f"{prefix} cannot override agreeing independent reviews")
    return errors


def validate_register(
    manifest_path: Path, register_path: Path, *, require_complete: bool = False
) -> list[str]:
    errors = []
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    register = json.loads(register_path.read_bytes())
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    if register.get("manifest_sha256") != digest:
        errors.append("eligibility register references a different manifest")
    status = register.get("status")
    if status not in REGISTER_STATUSES:
        errors.append("eligibility register has invalid status")
    complete = require_complete or status == "adjudicated"
    if require_complete and status != "adjudicated":
        errors.append("eligibility register is not adjudicated")
    sources = {r["repository"]: r for r in manifest["records"]}
    entries = register.get("records")
    if not isinstance(entries, list):
        return errors + ["records must be a list"]
    if len(entries) != len(sources):
        errors.append("register record count does not match manifest")
    seen = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"record {index} must be an object")
            continue
        name = entry.get("repository")
        if name in seen:
            errors.append(f"duplicate repository: {name}")
        seen.add(name)
        source = sources.get(name)
        if source is None:
            errors.append(f"unknown repository: {name}")
            continue
        for key in ("path", "source_commit", "source_url", "source_sha256"):
            source_key = "sha256" if key == "source_sha256" else key
            if entry.get(key) != source[source_key]:
                errors.append(f"{name}: {key} differs from manifest")
        if entry.get("repository_license_spdx") != source["license_spdx"]:
            errors.append(f"{name}: repository license metadata differs")
        decision = entry.get("final_eligibility")
        if decision not in ALLOWED:
            errors.append(f"{name}: invalid final_eligibility")
        if complete and decision not in FINAL:
            errors.append(f"{name}: eligibility review is incomplete")
        if decision in FINAL:
            evidence_url = entry.get("file_license_evidence_url")
            if not isinstance(evidence_url, str) or not evidence_url.startswith("https://"):
                errors.append(f"{name}: finalized without file-license evidence")
            if entry.get("file_license_disposition") not in FILE_LICENSE_FINAL:
                errors.append(f"{name}: file-license disposition is not final")
            if entry.get("content_disposition") not in FINAL:
                errors.append(f"{name}: content disposition is not final")
            if entry.get("source_independence_disposition") not in INDEPENDENCE_FINAL:
                errors.append(f"{name}: source-independence disposition is not final")
            if decision == "eligible" and (
                entry.get("file_license_disposition") != "verified"
                or entry.get("content_disposition") != "eligible"
                or entry.get("source_independence_disposition") != "independent"
            ):
                errors.append(f"{name}: eligible decision conflicts with component dispositions")
            reviewers = [entry.get("reviewer_1"), entry.get("reviewer_2")]
            for slot, reviewer in zip(("reviewer_1", "reviewer_2"), reviewers, strict=True):
                errors.extend(_validate_reviewer(name, slot, reviewer))
            if all(isinstance(reviewer, dict) for reviewer in reviewers):
                reviewer_ids = {reviewer.get("reviewer_id") for reviewer in reviewers}
                if len(reviewer_ids) != 2:
                    errors.append(f"{name}: independent reviewer identities are required")
                errors.extend(_validate_adjudication(name, entry, reviewer_ids))
    if seen != set(sources):
        errors.append("register repository set differs from manifest")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("register", type=Path)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="require every record to be adjudicated and final",
    )
    args = parser.parse_args()
    errors = validate_register(
        args.manifest, args.register, require_complete=args.require_complete
    )
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("Eligibility register structure and manifest binding valid; pending is not approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
