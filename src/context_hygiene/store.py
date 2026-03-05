"""SQLite WAL storage for audit history."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from context_hygiene.exceptions import StoreError
from context_hygiene.models import AuditSummary, Grade, HygieneReport

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    grade TEXT NOT NULL,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    tokens_recoverable INTEGER NOT NULL DEFAULT 0,
    contradiction_count INTEGER NOT NULL DEFAULT 0,
    deadweight_count INTEGER NOT NULL DEFAULT 0,
    report_json TEXT NOT NULL DEFAULT '{}',
    audited_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audits_file ON audits(file_path);
CREATE INDEX IF NOT EXISTS idx_audits_date ON audits(audited_at);
"""


class AuditStore:
    """SQLite WAL store for audit history."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._conn = sqlite3.connect(str(db_path))
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(_SCHEMA)
        except sqlite3.Error as e:
            raise StoreError(f"Failed to initialize database: {e}") from e

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def save_audit(self, report: HygieneReport) -> int:
        """Save an audit report. Returns the audit ID."""
        try:
            cur = self._conn.execute(
                """INSERT INTO audits
                   (file_path, grade, total_tokens, tokens_recoverable,
                    contradiction_count, deadweight_count, report_json, audited_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    report.file_path,
                    report.grade.value,
                    report.total_tokens,
                    report.tokens_recoverable,
                    len(report.contradictions),
                    len(report.deadweight),
                    report.model_dump_json(),
                    (report.analyzed_at or datetime.now(timezone.utc)).isoformat(),
                ),
            )
            self._conn.commit()
            return cur.lastrowid or 0
        except sqlite3.Error as e:
            raise StoreError(f"Failed to save audit: {e}") from e

    def get_audit(self, audit_id: int) -> HygieneReport | None:
        """Get a full audit report by ID."""
        row = self._conn.execute("SELECT * FROM audits WHERE id = ?", (audit_id,)).fetchone()
        if row is None:
            return None
        return HygieneReport.model_validate_json(row["report_json"])

    def list_audits(self, limit: int = 20) -> list[AuditSummary]:
        """List recent audit summaries."""
        rows = self._conn.execute(
            """SELECT id, file_path, grade, total_tokens, tokens_recoverable,
                      contradiction_count, deadweight_count, audited_at
               FROM audits ORDER BY audited_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            AuditSummary(
                audit_id=r["id"],
                file_path=r["file_path"],
                grade=Grade(r["grade"]),
                total_tokens=r["total_tokens"],
                tokens_recoverable=r["tokens_recoverable"],
                contradiction_count=r["contradiction_count"],
                deadweight_count=r["deadweight_count"],
                audited_at=datetime.fromisoformat(r["audited_at"]),
            )
            for r in rows
        ]

    def count_audits_this_month(self) -> int:
        """Count audits in the current calendar month."""
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM audits WHERE audited_at >= ?",
            (month_start.isoformat(),),
        ).fetchone()
        return row["cnt"] if row else 0

    def reset(self) -> None:
        """Delete all data (for testing)."""
        self._conn.execute("DELETE FROM audits")
        self._conn.commit()
