#!/usr/bin/env python3
"""Create a deterministic unlabeled cohort freeze after eligibility adjudication."""

import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .validate_eligibility_register import validate_register
else:
    from validate_eligibility_register import validate_register


def build_freeze(manifest_path: Path, register_path: Path) -> dict:
    """Return frozen metadata or fail closed while any eligibility gate is unresolved."""
    errors = validate_register(manifest_path, register_path, require_complete=True)
    if errors:
        raise ValueError("eligibility freeze blocked:\n" + "\n".join(errors))

    manifest_bytes = manifest_path.read_bytes()
    register_bytes = register_path.read_bytes()
    register = json.loads(register_bytes)
    eligible = []
    excluded = []
    for record in register["records"]:
        identity = {
            key: record[key]
            for key in ("repository", "path", "source_commit", "source_url", "source_sha256")
        }
        if record["final_eligibility"] == "eligible":
            eligible.append(identity)
        else:
            excluded.append(
                {
                    **identity,
                    "reason": record["adjudication"]["rationale"],
                }
            )

    eligible.sort(key=lambda record: record["repository"])
    excluded.sort(key=lambda record: record["repository"])

    return {
        "schema": "context-hygiene.eligible-cohort-freeze.v0.1",
        "status": "frozen_unlabeled",
        "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "eligibility_register_sha256": hashlib.sha256(register_bytes).hexdigest(),
        "eligible_records": eligible,
        "excluded_records": excluded,
        "detector_evaluation_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("register", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite existing freeze: {args.output}")
    try:
        freeze = build_freeze(args.manifest, args.register)
    except ValueError as error:
        parser.error(str(error))
    encoded = (json.dumps(freeze, indent=2, sort_keys=True) + "\n").encode()
    args.output.write_bytes(encoded)
    print(f"Wrote frozen unlabeled cohort: {args.output}")
    print(f"SHA-256: {hashlib.sha256(encoded).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
