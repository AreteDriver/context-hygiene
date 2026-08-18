"""Tests for context_hygiene.__main__ and __init__."""

from __future__ import annotations

import runpy
from importlib.metadata import version

import pytest

from context_hygiene import __version__


class TestVersion:
    def test_version_matches_package_metadata(self):
        assert __version__ == version("context-hygiene")


class TestMain:
    def test_main_module(self):
        with pytest.raises(SystemExit):
            runpy.run_module("context_hygiene", run_name="__main__")
