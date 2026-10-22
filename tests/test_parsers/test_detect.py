"""Tests for context_hygiene.parsers.detect."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_hygiene.exceptions import ParseError
from context_hygiene.parsers.claude import ClaudeParser
from context_hygiene.parsers.codex import CodexParser
from context_hygiene.parsers.detect import detect_parser, parse_file
from context_hygiene.parsers.generic import GenericParser
from context_hygiene.parsers.openai import OpenAIParser


class TestDetectParser:
    def test_claude_json(self, claude_file: Path):
        parser = detect_parser(claude_file)
        assert isinstance(parser, ClaudeParser)

    def test_openai_json(self, openai_file: Path):
        parser = detect_parser(openai_file)
        assert isinstance(parser, OpenAIParser)

    def test_markdown_file(self, generic_file: Path):
        parser = detect_parser(generic_file)
        assert isinstance(parser, GenericParser)

    def test_txt_file(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("User: hello\nAssistant: hi\n")
        parser = detect_parser(f)
        assert isinstance(parser, GenericParser)

    def test_unknown_json(self, tmp_path: Path):
        f = tmp_path / "unknown.json"
        f.write_text(json.dumps({"random": "data"}))
        # Should fall through to generic since .json isn't in generic's extensions
        with pytest.raises(ParseError, match="No parser"):
            detect_parser(f)

    def test_codex_jsonl(self, tmp_path: Path):
        f = tmp_path / "session.jsonl"
        f.write_text(json.dumps({"type": "response_item", "payload": {}}) + "\n")
        parser = detect_parser(f)
        assert isinstance(parser, CodexParser)

    def test_unsupported_extension(self, tmp_path: Path):
        f = tmp_path / "test.xlsx"
        f.write_text("data")
        with pytest.raises(ParseError, match="No parser"):
            detect_parser(f)


class TestParseFile:
    def test_generic(self, generic_file: Path):
        segments = parse_file(generic_file)
        assert len(segments) > 0

    def test_claude(self, claude_file: Path):
        segments = parse_file(claude_file)
        assert len(segments) > 0

    def test_openai(self, openai_file: Path):
        segments = parse_file(openai_file)
        assert len(segments) > 0

    def test_nonexistent(self, tmp_path: Path):
        with pytest.raises(ParseError, match="not found"):
            parse_file(tmp_path / "nope.md")

    def test_path_as_string(self, generic_file: Path):
        segments = parse_file(generic_file)
        assert len(segments) > 0

    def test_empty_file(self, empty_file: Path):
        segments = parse_file(empty_file)
        assert segments == []
