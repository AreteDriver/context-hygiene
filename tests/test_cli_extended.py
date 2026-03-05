"""Tests for extended CLI commands: clean, watch, --deep."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from context_hygiene.cli import app
from context_hygiene.models import AnalysisMode, HygieneReport

runner = CliRunner()


class TestCleanCommand:
    def test_dry_run_default(self, generic_file):
        result = runner.invoke(app, ["clean", str(generic_file)])
        assert result.exit_code == 0
        assert "Pruning plan" in result.output or "remove" in result.output.lower()
        assert "--apply" in result.output

    def test_apply_writes_file(self, generic_file, tmp_path):
        out = tmp_path / "cleaned.md"
        result = runner.invoke(app, ["clean", str(generic_file), "--apply", "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text()
        assert len(content) > 0

    def test_apply_default_output_path(self, generic_file):
        result = runner.invoke(app, ["clean", str(generic_file), "--apply"])
        assert result.exit_code == 0
        # Should create file.cleaned.md
        from pathlib import Path

        p = Path(str(generic_file))
        expected = p.parent / f"{p.stem}.cleaned{p.suffix}"
        assert expected.exists()
        expected.unlink()  # cleanup

    def test_nonexistent_file(self, tmp_path):
        result = runner.invoke(app, ["clean", str(tmp_path / "nope.md")])
        assert result.exit_code == 1


class TestWatchCommand:
    def test_requires_pro(self):
        result = runner.invoke(app, ["watch", "/tmp"])
        assert result.exit_code == 1
        assert "Pro" in result.output or "license" in result.output.lower()


class TestDeepFlag:
    def test_deep_requires_pro(self, generic_file):
        result = runner.invoke(app, ["audit", str(generic_file), "--deep"])
        assert result.exit_code == 1
        assert "Pro" in result.output or "license" in result.output.lower()

    @patch("context_hygiene.cli._run_deep_analysis")
    @patch("context_hygiene.cli._check_audit_quota")
    def test_deep_with_pro(self, mock_quota, mock_deep, generic_file, tmp_path):
        from datetime import datetime, timezone

        mock_deep.return_value = HygieneReport(
            file_path=str(generic_file),
            analyzed_at=datetime.now(timezone.utc),
            mode=AnalysisMode.DEEP,
        )

        with patch("context_hygiene.cli._get_store") as mock_store:
            store = MagicMock()
            mock_store.return_value = store
            result = runner.invoke(app, ["audit", str(generic_file), "--deep"])

        assert result.exit_code == 0


class TestGetLlmProvider:
    @patch("context_hygiene.cli.load_config")
    def test_default_ollama(self, mock_config):
        from context_hygiene.cli import _get_llm_provider

        mock_config.return_value = {}
        provider = _get_llm_provider()
        assert "Ollama" in type(provider).__name__

    def test_anthropic_provider(self):
        from context_hygiene.cli import _get_llm_provider

        mock_cls = MagicMock()
        fake_module = MagicMock(AnthropicProvider=mock_cls)
        with (
            patch(
                "context_hygiene.config.load_config",
                return_value={"llm_provider": "anthropic"},
            ),
            patch.dict("sys.modules", {"context_hygiene.llm.anthropic": fake_module}),
        ):
            _get_llm_provider()
        mock_cls.assert_called_once()


class TestDefaultOutputPath:
    def test_generates_cleaned_path(self):
        from context_hygiene.cli import _default_output_path

        assert _default_output_path("/tmp/conv.md") == "/tmp/conv.cleaned.md"
        assert _default_output_path("test.json") == "test.cleaned.json"
