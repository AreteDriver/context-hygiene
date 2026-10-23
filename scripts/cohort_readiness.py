"""Read-only status for external cohort eligibility reviews."""

import argparse
import json
from pathlib import Path

from scripts.validate_eligibility_register import validate_register


def build_report(manifest: Path, register: Path) -> dict:
    """Return missing review evidence without modifying source files."""
    errors = validate_register(manifest, register, require_complete=True)
    records = json.loads(register.read_text(encoding="utf-8"))["records"]
    rows = []
    for record in records:
        missing = [
            key
            for key in (
                "reviewer_1", "reviewer_2", "file_license_evidence_url",
                "file_license_disposition", "content_disposition",
                "source_independence_disposition", "adjudication", "final_eligibility",
            )
            if record.get(key) in (None, "pending", "needs_adjudication")
        ]
        rows.append({"repository": record["repository"], "missing": missing})
    rows.sort(key=lambda row: row["repository"])
    return {
        "status": "blocked" if errors else "ready_for_freeze",
        "detector_evaluation_authorized": False,
        "source_count": len(rows),
        "validation_errors": errors,
        "sources": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("register", type=Path)
    args = parser.parse_args()
    report = build_report(args.manifest, args.register)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
