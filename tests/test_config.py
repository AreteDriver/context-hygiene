"""Tests for context_hygiene.config."""

from __future__ import annotations

import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from context_hygiene.config import (
    config_path,
    db_path,
    get_config_dir,
    load_config,
    save_config,
)
from context_hygiene.exceptions import ConfigError


class TestGetConfigDir:
    def test_default(self):
        with patch.dict("os.environ", {}, clear=True):
            d = get_config_dir()
            assert str(d).endswith(".context-hygiene")

    def test_env_override(self):
        with patch.dict("os.environ", {"CONTEXT_HYGIENE_DIR": "/tmp/test"}):
            d = get_config_dir()
            assert str(d) == "/tmp/test"


class TestPaths:
    def test_config_path(self, tmp_config_dir: Path):
        p = config_path(tmp_config_dir)
        assert p.name == "config.yaml"
        assert p.parent == tmp_config_dir

    def test_db_path(self, tmp_config_dir: Path):
        p = db_path(tmp_config_dir)
        assert p.name == "hygiene.db"
        assert p.parent == tmp_config_dir


class TestLoadConfig:
    def test_no_file(self, tmp_config_dir: Path):
        cfg = load_config(tmp_config_dir)
        assert "llm_provider" in cfg

    def test_valid_yaml(self, tmp_config_dir: Path):
        (tmp_config_dir / "config.yaml").write_text("llm_provider: anthropic\n")
        cfg = load_config(tmp_config_dir)
        assert cfg["llm_provider"] == "anthropic"

    def test_invalid_yaml(self, tmp_config_dir: Path):
        (tmp_config_dir / "config.yaml").write_text(": invalid: [\n")
        with pytest.raises(ConfigError):
            load_config(tmp_config_dir)

    def test_non_dict_yaml(self, tmp_config_dir: Path):
        (tmp_config_dir / "config.yaml").write_text("- list\n- item\n")
        cfg = load_config(tmp_config_dir)
        assert "llm_provider" in cfg

    def test_empty_file(self, tmp_config_dir: Path):
        (tmp_config_dir / "config.yaml").write_text("")
        cfg = load_config(tmp_config_dir)
        assert "llm_provider" in cfg


class TestSaveConfig:
    def test_saves_yaml(self, tmp_config_dir: Path):
        save_config({"llm_provider": "ollama"}, tmp_config_dir)
        p = tmp_config_dir / "config.yaml"
        assert p.exists()
        text = p.read_text()
        assert "ollama" in text

    def test_permissions(self, tmp_config_dir: Path):
        save_config({"test": True}, tmp_config_dir)
        p = tmp_config_dir / "config.yaml"
        mode = p.stat().st_mode
        assert mode & stat.S_IRUSR
        assert mode & stat.S_IWUSR
        assert not (mode & stat.S_IRGRP)

    def test_creates_dir(self, tmp_path: Path):
        new_dir = tmp_path / "new" / "dir"
        save_config({"test": True}, new_dir)
        assert (new_dir / "config.yaml").exists()

    def test_write_error(self, tmp_config_dir: Path):
        # Make dir read-only
        ro_dir = tmp_config_dir / "readonly"
        ro_dir.mkdir()
        ro_file = ro_dir / "config.yaml"
        ro_file.write_text("test")
        ro_file.chmod(0)
        with pytest.raises(ConfigError):
            save_config({"test": True}, ro_dir)
        ro_file.chmod(stat.S_IRUSR | stat.S_IWUSR)  # cleanup
