"""Shared fixtures for context-hygiene tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_hygiene.models import Role, Segment

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def generic_file(fixtures_dir: Path) -> Path:
    return fixtures_dir / "generic_conversation.md"


@pytest.fixture
def claude_file(fixtures_dir: Path) -> Path:
    return fixtures_dir / "claude_export.json"


@pytest.fixture
def openai_file(fixtures_dir: Path) -> Path:
    return fixtures_dir / "openai_export.json"


@pytest.fixture
def empty_file(fixtures_dir: Path) -> Path:
    return fixtures_dir / "empty.md"


@pytest.fixture
def sample_segments() -> list[Segment]:
    """A simple conversation for testing analyzers."""
    return [
        Segment(index=0, role=Role.USER, content="How do I use pip?"),
        Segment(index=1, role=Role.ASSISTANT, content="Use pip install <package>."),
        Segment(index=2, role=Role.USER, content="ok"),
        Segment(
            index=3,
            role=Role.USER,
            content="Actually, scratch that. Use poetry instead.",
        ),
        Segment(
            index=4,
            role=Role.ASSISTANT,
            content="Sure, let me show you poetry.",
        ),
        Segment(index=5, role=Role.USER, content="Use pip for everything"),
        Segment(index=6, role=Role.USER, content="Don't use pip, use poetry"),
    ]


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Temporary config directory."""
    config_dir = tmp_path / ".context-hygiene"
    config_dir.mkdir()
    return config_dir
