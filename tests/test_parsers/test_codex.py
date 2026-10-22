"""Tests for context_hygiene.parsers.codex."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_hygiene.exceptions import ParseError
from context_hygiene.models import Role
from context_hygiene.parsers.codex import CodexParser


@pytest.fixture
def parser() -> CodexParser:
    return CodexParser()


class TestCanParse:
    def test_jsonl_extension(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        f.write_text(json.dumps({"type": "response_item"}) + "\n")
        assert parser.can_parse(f)

    def test_jsonl_with_session_meta(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        f.write_text(json.dumps({"type": "session_meta"}) + "\n")
        assert parser.can_parse(f)

    def test_json_not_jsonl(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"type": "response_item"}) + "\n")
        assert not parser.can_parse(f)

    def test_md_not_supported(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("## User\nHello\n")
        assert not parser.can_parse(f)

    def test_empty_file(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        assert not parser.can_parse(f)

    def test_invalid_json(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "bad.jsonl"
        f.write_text("not json")
        assert not parser.can_parse(f)

    def test_non_codex_jsonl(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "other.jsonl"
        f.write_text(json.dumps({"foo": "bar"}) + "\n")
        assert not parser.can_parse(f)


class TestParse:
    def test_single_message(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        f.write_text(
            json.dumps(
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "Hello world"}],
                    },
                }
            )
            + "\n"
        )
        segments = parser.parse(f)
        assert len(segments) == 1
        assert segments[0].role == Role.USER
        assert segments[0].content == "Hello world"

    def test_developer_role_maps_to_assistant(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        f.write_text(
            json.dumps(
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "developer",
                        "content": [{"type": "input_text", "text": "I'll help you"}],
                    },
                }
            )
            + "\n"
        )
        segments = parser.parse(f)
        assert len(segments) == 1
        assert segments[0].role == Role.ASSISTANT

    def test_multiple_messages(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        lines = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "First"}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "developer",
                    "content": [{"type": "input_text", "text": "Reply"}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Second"}],
                },
            },
        ]
        f.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
        segments = parser.parse(f)
        assert len(segments) == 3
        assert segments[0].role == Role.USER
        assert segments[1].role == Role.ASSISTANT
        assert segments[2].role == Role.USER
        assert segments[0].index == 0
        assert segments[1].index == 1
        assert segments[2].index == 2

    def test_skips_session_meta(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        lines = [
            {"type": "session_meta", "payload": {"id": "test"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Hello"}],
                },
            },
        ]
        f.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
        segments = parser.parse(f)
        assert len(segments) == 1
        assert segments[0].content == "Hello"

    def test_skips_non_message_payloads(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        lines = [
            {
                "type": "response_item",
                "payload": {
                    "type": "tool_call",
                    "role": "developer",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Hello"}],
                },
            },
        ]
        f.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
        segments = parser.parse(f)
        assert len(segments) == 1
        assert segments[0].content == "Hello"

    def test_string_content(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        f.write_text(
            json.dumps(
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": "Plain string content",
                    },
                }
            )
            + "\n"
        )
        segments = parser.parse(f)
        assert len(segments) == 1
        assert "Plain string content" in segments[0].content

    def test_empty_content_skipped(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        lines = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": ""}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Real"}],
                },
            },
        ]
        f.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
        segments = parser.parse(f)
        assert len(segments) == 1
        assert segments[0].content == "Real"

    def test_multiline_text(self, parser: CodexParser, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        f.write_text(
            json.dumps(
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "Line 1\nLine 2"}],
                    },
                }
            )
            + "\n"
        )
        segments = parser.parse(f)
        assert "Line 1\nLine 2" in segments[0].content

    def test_nonexistent_file(self, parser: CodexParser, tmp_path: Path):
        with pytest.raises(ParseError):
            parser.parse(tmp_path / "missing.jsonl")
