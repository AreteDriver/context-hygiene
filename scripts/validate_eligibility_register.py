#!/usr/bin/env python3
"""Fail-closed validation of the external cohort eligibility review register."""

import argparse
import hashlib
import json
from pathlib import Path

ALLOWED = {"pending", "eligible", "ineligible", "needs_adjudication"}


def validate_register(manifest_path: Path, register_path: Path) -> list[str]:
    errors = []
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    register = json.loads(register_path.read_bytes())
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    if register.get("manifest_sha256") != digest:
        errors.append("eligibility register references a different manifest")
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
        if decision in {"eligible", "ineligible"}:
            if not entry.get("file_license_evidence_url"):
                errors.append(f"{name}: finalized without file-license evidence")
            if not entry.get("reviewer_1") or not entry.get("reviewer_2"):
                errors.append(f"{name}: finalized without two reviewer identities")
            if entry.get("adjudication") in (None, "pending"):
                errors.append(f"{name}: finalized without adjudication record")
    if seen != set(sources):
        errors.append("register repository set differs from manifest")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("register", type=Path)
    args = parser.parse_args()
    errors = validate_register(args.manifest, args.register)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("Eligibility register structure and manifest binding valid; pending is not approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
