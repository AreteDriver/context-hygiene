"""Tests for context_hygiene.parsers.generic."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_hygiene.exceptions import ParseError
from context_hygiene.models import Role
from context_hygiene.parsers.generic import GenericParser


@pytest.fixture
def parser() -> GenericParser:
    return GenericParser()


class TestCanParse:
    def test_markdown(self, parser: GenericParser):
        assert parser.can_parse(Path("test.md"))

    def test_txt(self, parser: GenericParser):
        assert parser.can_parse(Path("test.txt"))

    def test_text(self, parser: GenericParser):
        assert parser.can_parse(Path("test.text"))

    def test_no_extension(self, parser: GenericParser):
        assert parser.can_parse(Path("Makefile"))

    def test_json_not_supported(self, parser: GenericParser):
        assert not parser.can_parse(Path("test.json"))

    def test_py_not_supported(self, parser: GenericParser):
        assert not parser.can_parse(Path("test.py"))


class TestParse:
    def test_fixture_file(self, parser: GenericParser, generic_file: Path):
        segments = parser.parse(generic_file)
        assert len(segments) > 0
        roles = {s.role for s in segments}
        assert Role.USER in roles
        assert Role.ASSISTANT in roles

    def test_empty_file(self, parser: GenericParser, empty_file: Path):
        segments = parser.parse(empty_file)
        assert segments == []

    def test_hash_headers(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## User\nHello\n## Assistant\nHi there\n")
        segments = parser.parse(f)
        assert len(segments) == 2
        assert segments[0].role == Role.USER
        assert segments[0].content == "Hello"
        assert segments[1].role == Role.ASSISTANT

    def test_bold_headers(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("**User**\nHello\n**Assistant**\nHi\n")
        segments = parser.parse(f)
        assert len(segments) == 2

    def test_colon_format(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("User: Hello world\nAssistant: Hi\n")
        segments = parser.parse(f)
        assert len(segments) == 2

    def test_system_role(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## System\nYou are helpful.\n## User\nHi\n")
        segments = parser.parse(f)
        assert segments[0].role == Role.SYSTEM

    def test_pre_role_content(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("Some preamble text\n## User\nHello\n")
        segments = parser.parse(f)
        assert segments[0].role == Role.SYSTEM

    def test_ai_alias(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## AI\nHello\n")
        segments = parser.parse(f)
        assert segments[0].role == Role.ASSISTANT

    def test_claude_alias(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## Claude\nHello\n")
        segments = parser.parse(f)
        assert segments[0].role == Role.ASSISTANT

    def test_chatgpt_alias(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## ChatGPT\nHello\n")
        segments = parser.parse(f)
        assert segments[0].role == Role.ASSISTANT

    def test_human_alias(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## Human\nHello\n")
        segments = parser.parse(f)
        assert segments[0].role == Role.USER

    def test_inline_content(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("User: Hello there\nAssistant: Hi\n")
        segments = parser.parse(f)
        assert "Hello there" in segments[0].content

    def test_multiline_content(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## User\nLine 1\nLine 2\nLine 3\n## Assistant\nReply\n")
        segments = parser.parse(f)
        assert "Line 1" in segments[0].content
        assert "Line 3" in segments[0].content

    def test_nonexistent_file(self, parser: GenericParser, tmp_path: Path):
        with pytest.raises(ParseError):
            parser.parse(tmp_path / "nonexistent.md")

    def test_token_estimates(self, parser: GenericParser, generic_file: Path):
        segments = parser.parse(generic_file)
        for seg in segments:
            assert seg.token_estimate > 0

    def test_case_insensitive(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## USER\nHello\n## ASSISTANT\nHi\n")
        segments = parser.parse(f)
        assert len(segments) == 2

    def test_gpt_alias(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## GPT\nResponse\n")
        segments = parser.parse(f)
        assert segments[0].role == Role.ASSISTANT

    def test_empty_content_between_markers(self, parser: GenericParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## User\n\n## Assistant\nHi\n")
        segments = parser.parse(f)
        # Empty user message should be skipped
        assert all(s.content.strip() for s in segments)
