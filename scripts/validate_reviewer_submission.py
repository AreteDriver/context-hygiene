#!/usr/bin/env python3
"""Fail-closed validation for blind external-cohort reviewer submissions."""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

SCHEMA = "context-hygiene.eligibility-review-submission.v0.1"
SLOTS = {"reviewer_1", "reviewer_2"}
FINAL = {"eligible", "ineligible"}
LICENSE_DISPOSITIONS = {"verified", "ineligible"}
INDEPENDENCE_DISPOSITIONS = {"independent", "not_independent"}


def _valid_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _load_inputs(manifest_path: Path, pilot_path: Path) -> tuple[dict, dict, str]:
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    pilot = json.loads(pilot_path.read_bytes())
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    return manifest, pilot, digest


def _selected_sources(
    manifest: dict, pilot: dict, digest: str
) -> tuple[dict[str, dict], list[str]]:
    errors = []
    if pilot.get("manifest_sha256") != digest:
        errors.append("pilot selection references a different manifest")
    repositories = pilot.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        return {}, errors + ["pilot repositories must be a nonempty list"]
    if not all(isinstance(name, str) and name.strip() for name in repositories):
        errors.append("pilot repositories must contain nonempty strings")
    if len(set(repositories)) != len(repositories):
        errors.append("pilot repositories must be unique")
    manifest_sources = {record["repository"]: record for record in manifest["records"]}
    unknown = sorted(set(repositories) - set(manifest_sources))
    if unknown:
        errors.append(f"pilot contains unknown repositories: {', '.join(unknown)}")
    return {
        name: manifest_sources[name]
        for name in repositories
        if name in manifest_sources
    }, errors


def validate_submission(
    manifest_path: Path,
    pilot_path: Path,
    submission_path: Path,
) -> tuple[list[str], dict | None]:
    """Validate one complete review submission against its exact pinned sources."""
    try:
        manifest, pilot, digest = _load_inputs(manifest_path, pilot_path)
        sources, errors = _selected_sources(manifest, pilot, digest)
        submission = json.loads(submission_path.read_bytes())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"could not load review inputs: {exc}"], None

    if submission.get("schema") != SCHEMA:
        errors.append("submission has an unsupported schema")
    if submission.get("manifest_sha256") != digest:
        errors.append("submission references a different manifest")
    if submission.get("pilot_schema") != pilot.get("schema"):
        errors.append("submission references a different pilot selection")
    if submission.get("reviewer_slot") not in SLOTS:
        errors.append("submission has an invalid reviewer_slot")
    reviewer_id = submission.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        errors.append("submission is missing reviewer_id")
    if not _valid_timestamp(submission.get("reviewed_at")):
        errors.append("submission is missing a timezone-aware reviewed_at")

    attestation = submission.get("blindness_attestation")
    if not isinstance(attestation, dict):
        errors.append("submission is missing the blindness attestation")
    else:
        if attestation.get("detector_outputs_viewed") is not False:
            errors.append("reviewer must attest that detector outputs were not viewed")
        if attestation.get("other_reviewer_decisions_viewed") is not False:
            errors.append("reviewer must attest that the other review was not viewed")
        if attestation.get("pinned_sources_treated_as_untrusted_data") is not True:
            errors.append("reviewer must attest that source instructions were treated as data")

    records = submission.get("records")
    if not isinstance(records, list):
        return errors + ["submission records must be a list"], submission
    if len(records) != len(sources):
        errors.append("submission record count does not match the pilot")
    seen = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} must be an object")
            continue
        name = record.get("repository")
        if name in seen:
            errors.append(f"duplicate repository: {name}")
        seen.add(name)
        source = sources.get(name)
        if source is None:
            errors.append(f"unknown pilot repository: {name}")
            continue
        for key, source_key in (
            ("path", "path"),
            ("source_commit", "source_commit"),
            ("source_url", "source_url"),
            ("source_sha256", "sha256"),
        ):
            if record.get(key) != source[source_key]:
                errors.append(f"{name}: {key} differs from manifest")
        if record.get("source_sha256_verified") is not True:
            errors.append(f"{name}: source SHA-256 was not verified")
        if not _https_url(record.get("file_license_evidence_url")):
            errors.append(f"{name}: file-license evidence must be an HTTPS URL")
        license_disposition = record.get("file_license_disposition")
        if license_disposition not in LICENSE_DISPOSITIONS:
            errors.append(f"{name}: file-license disposition is not final")
        content_disposition = record.get("content_disposition")
        if content_disposition not in FINAL:
            errors.append(f"{name}: content disposition is not final")
        block_count = record.get("semantic_block_count")
        if not isinstance(block_count, int) or isinstance(block_count, bool) or block_count < 0:
            errors.append(f"{name}: semantic_block_count must be a nonnegative integer")
        elif content_disposition == "eligible" and block_count < 2:
            errors.append(f"{name}: eligible content requires at least two semantic blocks")
        independence = record.get("source_independence_disposition")
        if independence not in INDEPENDENCE_DISPOSITIONS:
            errors.append(f"{name}: source-independence disposition is not final")
        for field in (
            "file_license_rationale",
            "content_rationale",
            "source_independence_rationale",
            "decision_rationale",
        ):
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"{name}: {field} is required")
        evidence_urls = record.get("evidence_urls")
        if (
            not isinstance(evidence_urls, list)
            or not evidence_urls
            or not all(_https_url(url) for url in evidence_urls)
        ):
            errors.append(f"{name}: evidence_urls must be a nonempty HTTPS URL list")
        decision = record.get("decision")
        if decision not in FINAL:
            errors.append(f"{name}: decision is not final")
        positive = (
            license_disposition == "verified"
            and content_disposition == "eligible"
            and independence == "independent"
        )
        if decision == "eligible" and not positive:
            errors.append(f"{name}: eligible decision conflicts with component dispositions")
        if decision == "ineligible" and positive:
            errors.append(f"{name}: ineligible decision lacks an ineligible component")
    if seen != set(sources):
        errors.append("submission repository set differs from the pilot")
    return errors, submission


def validate_pair(
    manifest_path: Path,
    pilot_path: Path,
    first_path: Path,
    second_path: Path,
) -> list[str]:
    """Validate a blind pair and its reviewer independence fields."""
    errors = []
    submissions = []
    for path in (first_path, second_path):
        item_errors, submission = validate_submission(manifest_path, pilot_path, path)
        errors.extend(f"{path.name}: {error}" for error in item_errors)
        if submission is not None:
            submissions.append(submission)
    if len(submissions) == 2:
        slots = {submission.get("reviewer_slot") for submission in submissions}
        if slots != SLOTS:
            errors.append("review pair must contain reviewer_1 and reviewer_2 slots")
        reviewer_ids = {
            str(submission.get("reviewer_id", "")).strip().casefold()
            for submission in submissions
        }
        if len(reviewer_ids) != 2:
            errors.append("review pair requires two distinct reviewer identities")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("pilot", type=Path)
    parser.add_argument("submissions", type=Path, nargs="+")
    args = parser.parse_args()
    if len(args.submissions) not in {1, 2}:
        parser.error("provide one submission or a reviewer pair")
    if len(args.submissions) == 1:
        errors, _ = validate_submission(args.manifest, args.pilot, args.submissions[0])
    else:
        errors = validate_pair(args.manifest, args.pilot, *args.submissions)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("Reviewer submission evidence and exact source bindings are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
