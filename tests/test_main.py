"""Tests for context_hygiene.__main__ and __init__."""

from __future__ import annotations

import runpy

import pytest

from context_hygiene import __version__


class TestVersion:
    def test_version_string(self):
        assert __version__ == "0.2.0"


class TestMain:
    def test_main_module(self):
        with pytest.raises(SystemExit):
            runpy.run_module("context_hygiene", run_name="__main__")
