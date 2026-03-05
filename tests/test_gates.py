"""Tests for context_hygiene.gates."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from context_hygiene.exceptions import LicenseError
from context_hygiene.gates import require_pro
from context_hygiene.licensing import _ENV_VAR, generate_key


class TestRequirePro:
    def test_pro_allowed(self):
        key = generate_key()
        with patch.dict("os.environ", {_ENV_VAR: key}):

            @require_pro("test_feature")
            def my_func():
                return "success"

            assert my_func() == "success"

    def test_free_blocked(self):
        with patch.dict("os.environ", {}, clear=True):

            @require_pro("premium")
            def my_func():
                return "success"

            with pytest.raises(LicenseError, match="premium"):
                my_func()

    def test_preserves_function_name(self):
        @require_pro("test")
        def my_special_func():
            """My docstring."""
            pass

        assert my_special_func.__name__ == "my_special_func"
        assert my_special_func.__doc__ == "My docstring."

    def test_passes_args(self):
        key = generate_key()
        with patch.dict("os.environ", {_ENV_VAR: key}):

            @require_pro("test")
            def add(a, b):
                return a + b

            assert add(2, 3) == 5

    def test_passes_kwargs(self):
        key = generate_key()
        with patch.dict("os.environ", {_ENV_VAR: key}):

            @require_pro("test")
            def greet(name="world"):
                return f"hello {name}"

            assert greet(name="arete") == "hello arete"

    def test_error_message_mentions_env_var(self):
        with patch.dict("os.environ", {}, clear=True):

            @require_pro("watch")
            def watch():
                pass

            with pytest.raises(LicenseError) as exc_info:
                watch()
            assert _ENV_VAR in str(exc_info.value)
