"""Tests for context_hygiene.parsers.claude."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_hygiene.exceptions import ParseError
from context_hygiene.models import Role
from context_hygiene.parsers.claude import ClaudeParser


@pytest.fixture
def parser() -> ClaudeParser:
    return ClaudeParser()


class TestCanParse:
    def test_claude_export(self, parser: ClaudeParser, claude_file: Path):
        assert parser.can_parse(claude_file)

    def test_non_json(self, parser: ClaudeParser, generic_file: Path):
        assert not parser.can_parse(generic_file)

    def test_openai_format(self, parser: ClaudeParser, openai_file: Path):
        assert not parser.can_parse(openai_file)

    def test_invalid_json(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "bad.json"
        f.write_text("{invalid json")
        assert not parser.can_parse(f)

    def test_chat_messages_format(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "claude.json"
        f.write_text(json.dumps({"chat_messages": []}))
        assert parser.can_parse(f)

    def test_messages_format(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "claude.json"
        f.write_text(json.dumps({"messages": []}))
        assert parser.can_parse(f)

    def test_list_with_sender(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "claude.json"
        f.write_text(json.dumps([{"sender": "human", "text": "hi"}]))
        assert parser.can_parse(f)

    def test_list_with_role(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "claude.json"
        f.write_text(json.dumps([{"role": "user", "content": "hi"}]))
        assert parser.can_parse(f)

    def test_empty_list(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "claude.json"
        f.write_text(json.dumps([]))
        assert not parser.can_parse(f)

    def test_plain_dict(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "plain.json"
        f.write_text(json.dumps({"key": "value"}))
        assert not parser.can_parse(f)


class TestParse:
    def test_fixture_file(self, parser: ClaudeParser, claude_file: Path):
        segments = parser.parse(claude_file)
        assert len(segments) == 6
        assert segments[0].role == Role.USER
        assert segments[1].role == Role.ASSISTANT

    def test_content_extracted(self, parser: ClaudeParser, claude_file: Path):
        segments = parser.parse(claude_file)
        assert "fibonacci" in segments[0].content.lower()

    def test_content_blocks_format(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "blocks.json"
        f.write_text(
            json.dumps(
                {
                    "chat_messages": [
                        {
                            "sender": "human",
                            "content": [
                                {"type": "text", "text": "Hello"},
                                {"type": "text", "text": "World"},
                            ],
                        }
                    ]
                }
            )
        )
        segments = parser.parse(f)
        assert len(segments) == 1
        assert "Hello" in segments[0].content
        assert "World" in segments[0].content

    def test_string_content(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "str.json"
        f.write_text(
            json.dumps({"chat_messages": [{"sender": "human", "content": "plain string content"}]})
        )
        segments = parser.parse(f)
        assert segments[0].content == "plain string content"

    def test_mixed_content_blocks(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "mixed.json"
        f.write_text(
            json.dumps(
                {
                    "chat_messages": [
                        {
                            "sender": "assistant",
                            "content": [
                                "string block",
                                {"type": "text", "text": "text block"},
                                {"type": "image", "url": "skip_me"},
                            ],
                        }
                    ]
                }
            )
        )
        segments = parser.parse(f)
        assert "string block" in segments[0].content
        assert "text block" in segments[0].content

    def test_empty_messages(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "empty.json"
        f.write_text(json.dumps({"chat_messages": []}))
        segments = parser.parse(f)
        assert segments == []

    def test_invalid_json(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "bad.json"
        f.write_text("{invalid")
        with pytest.raises(ParseError):
            parser.parse(f)

    def test_role_mapping_assistant(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "role.json"
        f.write_text(json.dumps([{"sender": "assistant", "text": "reply"}]))
        segments = parser.parse(f)
        assert segments[0].role == Role.ASSISTANT

    def test_role_mapping_system(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "role.json"
        f.write_text(json.dumps([{"sender": "system", "text": "instructions"}]))
        segments = parser.parse(f)
        assert segments[0].role == Role.SYSTEM

    def test_unknown_role_defaults_user(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "role.json"
        f.write_text(json.dumps([{"sender": "unknown_sender", "text": "hi"}]))
        segments = parser.parse(f)
        assert segments[0].role == Role.USER

    def test_empty_text_skipped(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "empty_text.json"
        f.write_text(
            json.dumps(
                {
                    "chat_messages": [
                        {"sender": "human", "text": ""},
                        {"sender": "assistant", "text": "real content"},
                    ]
                }
            )
        )
        segments = parser.parse(f)
        assert len(segments) == 1
        assert segments[0].role == Role.ASSISTANT

    def test_no_text_or_content(self, parser: ClaudeParser, tmp_path: Path):
        f = tmp_path / "no_content.json"
        f.write_text(json.dumps({"chat_messages": [{"sender": "human"}]}))
        segments = parser.parse(f)
        assert segments == []
