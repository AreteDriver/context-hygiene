"""Tests for context_hygiene.exceptions."""

from context_hygiene.exceptions import (
    AnalysisError,
    ConfigError,
    ContextHygieneError,
    LicenseError,
    LLMError,
    ParseError,
    StoreError,
)


class TestExceptionHierarchy:
    def test_base_exception(self):
        e = ContextHygieneError("test")
        assert str(e) == "test"
        assert isinstance(e, Exception)

    def test_store_error(self):
        e = StoreError("db fail")
        assert isinstance(e, ContextHygieneError)

    def test_config_error(self):
        e = ConfigError("bad config")
        assert isinstance(e, ContextHygieneError)

    def test_parse_error(self):
        e = ParseError("bad file")
        assert isinstance(e, ContextHygieneError)

    def test_analysis_error(self):
        e = AnalysisError("bad analysis")
        assert isinstance(e, ContextHygieneError)

    def test_license_error(self):
        e = LicenseError("bad key")
        assert isinstance(e, ContextHygieneError)

    def test_llm_error(self):
        e = LLMError("api fail")
        assert isinstance(e, ContextHygieneError)
