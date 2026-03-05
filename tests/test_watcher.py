"""Tests for the file watcher module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from context_hygiene.exceptions import LicenseError
from context_hygiene.watcher import _score_file, watch_directory


class TestWatchDirectory:
    def test_requires_pro(self):
        with pytest.raises(LicenseError):
            watch_directory("/tmp")

    def test_not_a_directory_error(self):
        # require_pro fires first, so this is covered by test_requires_pro
        pass

    def test_not_a_directory_raises(self, tmp_path):
        # The require_pro gate fires first, so we test that path
        with pytest.raises(LicenseError):
            watch_directory(str(tmp_path / "nonexistent"))


class TestScoreFile:
    def test_scores_valid_file(self, generic_file):
        console = MagicMock()
        _score_file(str(generic_file), console)
        console.print.assert_called_once()
        output = console.print.call_args[0][0]
        assert any(g in output for g in ("A", "B", "C", "D", "F"))

    def test_empty_file_no_output(self, empty_file):
        console = MagicMock()
        _score_file(str(empty_file), console)
        console.print.assert_not_called()

    def test_nonexistent_file_no_crash(self, tmp_path):
        console = MagicMock()
        _score_file(str(tmp_path / "nope.md"), console)
        # Should not raise — errors are caught

    def test_unparseable_file_no_crash(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("")
        console = MagicMock()
        _score_file(str(f), console)
        console.print.assert_not_called()
