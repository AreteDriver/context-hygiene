"""Tests for context_hygiene.parsers.openai."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_hygiene.exceptions import ParseError
from context_hygiene.models import Role
from context_hygiene.parsers.openai import OpenAIParser


@pytest.fixture
def parser() -> OpenAIParser:
    return OpenAIParser()


class TestCanParse:
    def test_openai_export(self, parser: OpenAIParser, openai_file: Path):
        assert parser.can_parse(openai_file)

    def test_non_json(self, parser: OpenAIParser, generic_file: Path):
        assert not parser.can_parse(generic_file)

    def test_claude_format(self, parser: OpenAIParser, claude_file: Path):
        assert not parser.can_parse(claude_file)

    def test_mapping_format(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        f.write_text(json.dumps({"mapping": {}, "title": "Test"}))
        assert parser.can_parse(f)

    def test_list_with_title(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        f.write_text(json.dumps([{"title": "Chat", "mapping": {}}]))
        assert parser.can_parse(f)

    def test_invalid_json(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "bad.json"
        f.write_text("not json")
        assert not parser.can_parse(f)

    def test_empty_list(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "empty.json"
        f.write_text("[]")
        assert not parser.can_parse(f)


class TestParse:
    def test_fixture_file(self, parser: OpenAIParser, openai_file: Path):
        segments = parser.parse(openai_file)
        assert len(segments) > 0
        assert any(s.role == Role.USER for s in segments)

    def test_mapping_format(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = [
            {
                "title": "Test",
                "mapping": {
                    "n1": {
                        "message": {
                            "author": {"role": "user"},
                            "content": {"parts": ["Hello"]},
                        }
                    },
                    "n2": {
                        "message": {
                            "author": {"role": "assistant"},
                            "content": {"parts": ["Hi there"]},
                        }
                    },
                },
            }
        ]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert len(segments) == 2

    def test_messages_format(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = [
            {
                "title": "Test",
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi"},
                ],
            }
        ]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert len(segments) == 2

    def test_string_content(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = [{"title": "T", "messages": [{"role": "user", "content": "hello"}]}]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert segments[0].content == "hello"

    def test_dict_content_with_parts(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = [
            {
                "title": "T",
                "mapping": {
                    "n1": {
                        "message": {
                            "author": {"role": "user"},
                            "content": {"parts": ["part1", "part2"]},
                        }
                    }
                },
            }
        ]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert "part1" in segments[0].content

    def test_list_content(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = [
            {
                "title": "T",
                "messages": [{"role": "user", "content": ["text1", "text2"]}],
            }
        ]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert "text1" in segments[0].content

    def test_empty_content_skipped(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = [
            {
                "title": "T",
                "messages": [
                    {"role": "user", "content": ""},
                    {"role": "assistant", "content": "real"},
                ],
            }
        ]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert len(segments) == 1

    def test_invalid_json_error(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "bad.json"
        f.write_text("invalid")
        with pytest.raises(ParseError):
            parser.parse(f)

    def test_system_role(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = [
            {
                "title": "T",
                "messages": [{"role": "system", "content": "instructions"}],
            }
        ]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert segments[0].role == Role.SYSTEM

    def test_tool_role(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = [
            {
                "title": "T",
                "messages": [{"role": "tool", "content": "result"}],
            }
        ]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert segments[0].role == Role.SYSTEM

    def test_single_conversation_dict(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = {
            "mapping": {
                "n1": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["hello"]},
                    }
                }
            }
        }
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert len(segments) == 1

    def test_null_message_nodes_skipped(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = [
            {
                "title": "T",
                "mapping": {
                    "root": {"message": None},
                    "n1": {
                        "message": {
                            "author": {"role": "user"},
                            "content": {"parts": ["hi"]},
                        }
                    },
                },
            }
        ]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert len(segments) == 1

    def test_non_dict_conv_skipped(self, parser: OpenAIParser, tmp_path: Path):
        f = tmp_path / "oai.json"
        data = ["not a dict", {"title": "T", "messages": [{"role": "user", "content": "hi"}]}]
        f.write_text(json.dumps(data))
        segments = parser.parse(f)
        assert len(segments) == 1
