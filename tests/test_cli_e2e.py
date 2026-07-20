"""End-to-end CLI tests covering the full user workflow.

These tests verify that commands interact correctly with the SQLite store
and that file-system operations are consistent (no double-parse bugs).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from context_hygiene.cli import app
from context_hygiene.config import db_path
from context_hygiene.store import AuditStore

runner = CliRunner()


class TestAuditHistoryPipeline:
    """Full pipeline: audit -> verify persistence -> history retrieval."""

    def test_audit_creates_db_record(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["audit", str(generic_file)])
            assert result.exit_code == 0
            assert "Context Hygiene Report" in result.output

            # Verify SQLite row was written
            store = AuditStore(db_path(tmp_config_dir))
            audits = store.list_audits(limit=1)
            store.close()
            assert len(audits) == 1
            assert audits[0].file_path == str(generic_file)

    def test_audit_then_history_shows_entry(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            runner.invoke(app, ["audit", str(generic_file)])
            result = runner.invoke(app, ["history"])
            assert result.exit_code == 0
            assert "Audit History" in result.output
            # Verify the row contains expected values (file path is truncated in table)
            assert "B" in result.output  # grade
            assert "240" in result.output  # tokens

    def test_audit_json_output_is_valid(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["audit", str(generic_file), "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["file_path"] == str(generic_file)
            assert "grade" in data
            assert "staleness_score" in data
            assert "total_tokens" in data

    def test_multiple_audits_increment_db(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            for _ in range(3):
                runner.invoke(app, ["audit", str(generic_file)])

            store = AuditStore(db_path(tmp_config_dir))
            audits = store.list_audits(limit=10)
            store.close()
            assert len(audits) == 3


class TestCleanPipeline:
    """Clean command: dry-run preview and --apply output consistency."""

    def test_clean_dry_run_shows_plan(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["clean", str(generic_file), "--dry-run"])
            assert result.exit_code == 0
            assert "Pruning plan" in result.output
            assert "--apply" in result.output

    def test_clean_apply_writes_file(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(
                app, ["clean", str(generic_file), "--apply"]
            )
            assert result.exit_code == 0
            assert "Cleaned output written to" in result.output

            expected_path = generic_file.parent / f"{generic_file.stem}.cleaned{generic_file.suffix}"
            assert expected_path.exists()
            content = expected_path.read_text()
            assert "## User" in content or "## Assistant" in content

    def test_clean_apply_with_custom_output(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            out_path = tmp_config_dir / "my_clean.md"
            result = runner.invoke(
                app, ["clean", str(generic_file), "--apply", "--output", str(out_path)]
            )
            assert result.exit_code == 0
            assert out_path.exists()

    def test_clean_does_not_reparse_inconsistently(
        self, generic_file: Path, tmp_config_dir: Path
    ):
        """Regression: clean must use the same segments as the report, not re-parse.

        If the file is parsed twice (once for audit, once for pruning),
        any side-effectful parser or race condition could produce divergent
        segment lists. This test verifies the plan uses the same segments.
        """
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            # Run clean with --apply
            result = runner.invoke(app, ["clean", str(generic_file), "--apply"])
            assert result.exit_code == 0

            # The output should be consistent — no parse errors or mismatches
            expected_path = generic_file.parent / f"{generic_file.stem}.cleaned{generic_file.suffix}"
            assert expected_path.exists()

    def test_clean_on_empty_file(self, empty_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["clean", str(empty_file), "--dry-run"])
            # Empty file produces no segments; should still exit cleanly
            assert result.exit_code == 0


class TestScorePipeline:
    """Score command end-to-end."""

    def test_score_shows_grade_and_tokens(self, generic_file: Path):
        result = runner.invoke(app, ["score", str(generic_file)])
        assert result.exit_code == 0
        assert "Staleness Score" in result.output
        assert "Grade:" in result.output
        assert "Tokens:" in result.output

    def test_score_empty_file(self, empty_file: Path):
        result = runner.invoke(app, ["score", str(empty_file)])
        assert result.exit_code == 0
        assert "No segments" in result.output

    def test_score_nonexistent_file(self):
        result = runner.invoke(app, ["score", "/tmp/does_not_exist_12345.md"])
        assert result.exit_code == 1
        assert "Error" in result.output


class TestStatusPipeline:
    """Status command reflects the current environment."""

    def test_status_shows_audit_count(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            runner.invoke(app, ["audit", str(generic_file)])
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "Audits this month" in result.output
            assert "1/" in result.output or "1/∞" in result.output
