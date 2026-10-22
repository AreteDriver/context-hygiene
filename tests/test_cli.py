"""Tests for context_hygiene.cli."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from context_hygiene import __version__
from context_hygiene.cli import app
from context_hygiene.licensing import _ENV_VAR, generate_key

runner = CliRunner()


class TestVersion:
    def test_version_output(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestScore:
    def test_generic_file(self, generic_file: Path):
        result = runner.invoke(app, ["score", str(generic_file)])
        assert result.exit_code == 0
        assert "Staleness Score" in result.output
        assert "Grade" in result.output

    def test_empty_file(self, empty_file: Path):
        result = runner.invoke(app, ["score", str(empty_file)])
        assert result.exit_code == 0
        assert "No segments" in result.output

    def test_nonexistent_file(self):
        result = runner.invoke(app, ["score", "/tmp/nonexistent_file.md"])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_claude_file(self, claude_file: Path):
        result = runner.invoke(app, ["score", str(claude_file)])
        assert result.exit_code == 0
        assert "Grade" in result.output


class TestAudit:
    def test_audit_generic(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["audit", str(generic_file)])
            assert result.exit_code == 0
            assert "Context Hygiene Report" in result.output

    def test_audit_json_output(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["audit", str(generic_file), "--json"])
            assert result.exit_code == 0
            assert "file_path" in result.output

    def test_audit_sarif_output(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["audit", str(generic_file), "--format", "sarif"])
            assert result.exit_code == 0
            assert "$schema" in result.output
            assert "context-hygiene" in result.output

    def test_audit_nonexistent(self, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["audit", "/tmp/nope.md"])
            assert result.exit_code == 1

    def test_audit_saves_to_store(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            runner.invoke(app, ["audit", str(generic_file)])
            result = runner.invoke(app, ["history"])
            assert result.exit_code == 0

    def test_audit_fail_under_pass(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["audit", str(generic_file), "--fail-under", "C"])
            assert result.exit_code == 0
            assert "PASS" in result.output

    def test_audit_fail_under_fail(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["audit", str(generic_file), "--fail-under", "A"])
            assert result.exit_code == 1
            assert "FAILED" in result.output

    def test_audit_fail_under_invalid(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["audit", str(generic_file), "--fail-under", "Z"])
            assert result.exit_code == 2
            assert "must be one of" in result.output

    def test_free_tier_limit(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}, clear=True):
            # Run 10 audits (free limit)
            for _ in range(10):
                runner.invoke(app, ["audit", str(generic_file)])

            # 11th should fail
            result = runner.invoke(app, ["audit", str(generic_file)])
            assert result.exit_code == 1
            assert "limit" in result.output.lower()

    def test_pro_unlimited(self, generic_file: Path, tmp_config_dir: Path):
        key = generate_key()
        with patch.dict(
            "os.environ",
            {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir), _ENV_VAR: key},
        ):
            for _ in range(12):
                result = runner.invoke(app, ["audit", str(generic_file)])
                assert result.exit_code == 0


class TestHistory:
    def test_empty_history(self, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["history"])
            assert result.exit_code == 0
            assert "No audit history" in result.output

    def test_with_entries(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            runner.invoke(app, ["audit", str(generic_file)])
            result = runner.invoke(app, ["history"])
            assert result.exit_code == 0
            assert "Audit History" in result.output

    def test_limit_option(self, generic_file: Path, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            for _ in range(3):
                runner.invoke(app, ["audit", str(generic_file)])
            result = runner.invoke(app, ["history", "--limit", "2"])
            assert result.exit_code == 0


class TestStatus:
    def test_free_tier(self, tmp_config_dir: Path):
        with patch.dict(
            "os.environ",
            {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)},
            clear=True,
        ):
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "free" in result.output.lower()

    def test_pro_tier(self, tmp_config_dir: Path):
        key = generate_key()
        with patch.dict(
            "os.environ",
            {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir), _ENV_VAR: key},
        ):
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "pro" in result.output.lower()

    def test_shows_version(self, tmp_config_dir: Path):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": str(tmp_config_dir)}):
            result = runner.invoke(app, ["status"])
            assert __version__ in result.output


class TestStats:
    def test_disabled(self):
        with patch.dict("os.environ", {}, clear=True):
            result = runner.invoke(app, ["stats"])
            assert result.exit_code == 0
            assert "disabled" in result.output.lower()

    def test_no_data(self, tmp_config_dir: Path):
        with patch.dict(
            "os.environ",
            {"CONTEXT_HYGIENE_TELEMETRY": "1", "CONTEXT_HYGIENE_DIR": str(tmp_config_dir)},
        ):
            result = runner.invoke(app, ["stats"])
            assert result.exit_code == 0
            assert "No telemetry data" in result.output

    def test_with_data_table(self, tmp_config_dir: Path):
        from context_hygiene.telemetry import TelemetryStore

        db = tmp_config_dir / "telemetry.db"
        store = TelemetryStore(db)
        store.record("command", "audit")
        store.record("pro_gate", "deep analysis")
        store.close()
        with patch.dict(
            "os.environ",
            {"CONTEXT_HYGIENE_TELEMETRY": "1", "CONTEXT_HYGIENE_DIR": str(tmp_config_dir)},
        ):
            result = runner.invoke(app, ["stats"])
            assert result.exit_code == 0
            assert "Telemetry Overview" in result.output
            assert "audit" in result.output

    def test_with_data_json(self, tmp_config_dir: Path):
        from context_hygiene.telemetry import TelemetryStore

        db = tmp_config_dir / "telemetry.db"
        store = TelemetryStore(db)
        store.record("command", "audit")
        store.close()
        with patch.dict(
            "os.environ",
            {"CONTEXT_HYGIENE_TELEMETRY": "1", "CONTEXT_HYGIENE_DIR": str(tmp_config_dir)},
        ):
            result = runner.invoke(app, ["stats", "--json"])
            assert result.exit_code == 0
            assert "total_events" in result.output


class TestCompletion:
    def test_bash(self):
        result = runner.invoke(app, ["completion", "bash"])
        assert result.exit_code == 0
        assert "_ctx_hygiene_completion" in result.output

    def test_zsh(self):
        result = runner.invoke(app, ["completion", "zsh"])
        assert result.exit_code == 0
        assert "_ctx-hygiene" in result.output

    def test_fish(self):
        result = runner.invoke(app, ["completion", "fish"])
        assert result.exit_code == 0
        assert "ctx-hygiene" in result.output

    def test_invalid_shell(self):
        result = runner.invoke(app, ["completion", "powershell"])
        assert result.exit_code == 1
        assert "Unsupported shell" in result.output


class TestNoArgs:
    def test_help_shown(self):
        result = runner.invoke(app, [])
        # no_args_is_help=True causes exit code 0 on newer typer, 2 on older
        assert result.exit_code in (0, 2)
        assert "Usage" in result.output or "ctx-hygiene" in result.output
