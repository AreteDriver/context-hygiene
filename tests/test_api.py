"""Tests for context_hygiene.api — programmatic interface."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_hygiene.api import ScoreResult, audit_file, score_file
from context_hygiene.exceptions import ParseError
from context_hygiene.models import Grade


class TestAuditFile:
    def test_audit_generic_file(self, generic_file: Path):
        report = audit_file(generic_file)
        assert report.file_path == str(generic_file)
        assert report.total_segments > 0
        assert report.total_tokens > 0
        assert report.grade in {Grade.A, Grade.B, Grade.C, Grade.D, Grade.F}
        assert report.analyzed_at is not None

    def test_audit_returns_staleness_results(self, generic_file: Path):
        report = audit_file(generic_file)
        assert len(report.staleness_results) == report.total_segments
        for sr in report.staleness_results:
            assert 0.0 <= sr.score <= 1.0

    def test_audit_empty_file(self, empty_file: Path):
        report = audit_file(empty_file)
        assert report.total_segments == 0
        assert report.total_tokens == 0
        assert report.grade == Grade.A

    def test_audit_nonexistent_file_raises(self):
        with pytest.raises(ParseError):
            audit_file("/tmp/does_not_exist_12345.md")

    def test_audit_str_path(self, generic_file: Path):
        report = audit_file(str(generic_file))
        assert report.file_path == str(generic_file)


class TestScoreFile:
    def test_score_generic_file(self, generic_file: Path):
        score = score_file(generic_file)
        assert score.grade in {Grade.A, Grade.B, Grade.C, Grade.D, Grade.F}
        assert 0.0 <= score.staleness <= 1.0
        assert score.segments > 0
        assert score.tokens > 0

    def test_score_empty_file(self, empty_file: Path):
        score = score_file(empty_file)
        assert score.grade == Grade.A
        assert score.staleness == 0.0
        assert score.segments == 0
        assert score.tokens == 0

    def test_score_nonexistent_file_raises(self):
        with pytest.raises(ParseError):
            score_file("/tmp/does_not_exist_12345.md")

    def test_score_result_repr(self):
        result = ScoreResult(grade=Grade.B, staleness=0.25, segments=5, tokens=100)
        repr_str = repr(result)
        assert "ScoreResult" in repr_str
        assert "B" in repr_str
        assert "0.25" in repr_str
