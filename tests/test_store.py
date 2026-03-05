"""Tests for context_hygiene.store."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from context_hygiene.models import (
    Contradiction,
    DeadweightResult,
    Grade,
    HygieneReport,
)
from context_hygiene.store import AuditStore


@pytest.fixture
def store(tmp_path: Path) -> AuditStore:
    s = AuditStore(tmp_path / "test.db")
    yield s
    s.close()


def _make_report(**kwargs) -> HygieneReport:
    defaults = {
        "file_path": "test.md",
        "total_segments": 10,
        "total_tokens": 500,
        "grade": Grade.B,
        "staleness_score": 0.3,
        "tokens_recoverable": 50,
        "analyzed_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return HygieneReport(**defaults)


class TestAuditStoreInit:
    def test_creates_db(self, tmp_path: Path):
        db = tmp_path / "new.db"
        s = AuditStore(db)
        assert db.exists()
        s.close()

    def test_creates_parent_dir(self, tmp_path: Path):
        db = tmp_path / "sub" / "dir" / "test.db"
        s = AuditStore(db)
        assert db.exists()
        s.close()


class TestSaveAudit:
    def test_saves_and_returns_id(self, store: AuditStore):
        report = _make_report()
        audit_id = store.save_audit(report)
        assert audit_id > 0

    def test_increments_id(self, store: AuditStore):
        id1 = store.save_audit(_make_report())
        id2 = store.save_audit(_make_report(file_path="other.md"))
        assert id2 > id1

    def test_saves_with_contradictions(self, store: AuditStore):
        report = _make_report(
            contradictions=[Contradiction(segment_a=0, segment_b=1, description="conflict")]
        )
        audit_id = store.save_audit(report)
        assert audit_id > 0

    def test_saves_with_deadweight(self, store: AuditStore):
        report = _make_report(
            deadweight=[DeadweightResult(segment_index=2, reason="ack", tokens_recoverable=5)]
        )
        audit_id = store.save_audit(report)
        assert audit_id > 0


class TestGetAudit:
    def test_existing(self, store: AuditStore):
        report = _make_report()
        audit_id = store.save_audit(report)
        loaded = store.get_audit(audit_id)
        assert loaded is not None
        assert loaded.file_path == "test.md"
        assert loaded.total_tokens == 500

    def test_nonexistent(self, store: AuditStore):
        assert store.get_audit(999) is None


class TestListAudits:
    def test_empty(self, store: AuditStore):
        assert store.list_audits() == []

    def test_returns_summaries(self, store: AuditStore):
        store.save_audit(_make_report())
        store.save_audit(_make_report(file_path="other.md", grade=Grade.A))
        audits = store.list_audits()
        assert len(audits) == 2

    def test_limit(self, store: AuditStore):
        for i in range(5):
            store.save_audit(_make_report(file_path=f"file{i}.md"))
        audits = store.list_audits(limit=3)
        assert len(audits) == 3

    def test_most_recent_first(self, store: AuditStore):
        store.save_audit(_make_report(file_path="old.md"))
        store.save_audit(_make_report(file_path="new.md"))
        audits = store.list_audits()
        assert audits[0].file_path == "new.md"

    def test_summary_fields(self, store: AuditStore):
        store.save_audit(
            _make_report(
                grade=Grade.C,
                total_tokens=1000,
                tokens_recoverable=200,
                contradictions=[Contradiction(segment_a=0, segment_b=1, description="x")],
                deadweight=[DeadweightResult(segment_index=0, reason="y", tokens_recoverable=10)],
            )
        )
        summary = store.list_audits()[0]
        assert summary.grade == Grade.C
        assert summary.total_tokens == 1000
        assert summary.contradiction_count == 1
        assert summary.deadweight_count == 1


class TestCountAuditsThisMonth:
    def test_empty(self, store: AuditStore):
        assert store.count_audits_this_month() == 0

    def test_counts_current(self, store: AuditStore):
        store.save_audit(_make_report())
        store.save_audit(_make_report())
        assert store.count_audits_this_month() == 2


class TestReset:
    def test_clears_all(self, store: AuditStore):
        store.save_audit(_make_report())
        store.save_audit(_make_report())
        store.reset()
        assert store.list_audits() == []
        assert store.count_audits_this_month() == 0
