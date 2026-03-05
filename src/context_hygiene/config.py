"""YAML config for context-hygiene."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import yaml

from context_hygiene.exceptions import ConfigError

_DEFAULT_DIR = Path.home() / ".context-hygiene"
_CONFIG_FILE = "config.yaml"
_DB_FILE = "hygiene.db"


def get_config_dir() -> Path:
    """Get the config directory path (respects CONTEXT_HYGIENE_DIR env var)."""
    return Path(os.environ.get("CONTEXT_HYGIENE_DIR", str(_DEFAULT_DIR)))


def _ensure_config_dir(config_dir: Path) -> None:
    """Create config dir with secure permissions if it doesn't exist."""
    config_dir.mkdir(parents=True, exist_ok=True)


def config_path(config_dir: Path | None = None) -> Path:
    d = config_dir or get_config_dir()
    return d / _CONFIG_FILE


def db_path(config_dir: Path | None = None) -> Path:
    d = config_dir or get_config_dir()
    return d / _DB_FILE


def load_config(config_dir: Path | None = None) -> dict:
    """Load YAML config from disk."""
    path = config_path(config_dir)
    if not path.exists():
        return {"llm_provider": "ollama", "ollama_model": "llama3.2"}
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {"llm_provider": "ollama"}
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to read config: {e}") from e


def save_config(data: dict, config_dir: Path | None = None) -> None:
    """Save YAML config to disk with 0o600 permissions."""
    d = config_dir or get_config_dir()
    _ensure_config_dir(d)
    path = d / _CONFIG_FILE
    try:
        with open(path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError as e:
        raise ConfigError(f"Failed to write config: {e}") from e
