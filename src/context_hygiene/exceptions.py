"""Exception hierarchy for context-hygiene."""


class ContextHygieneError(Exception):
    """Base exception for all context-hygiene errors."""


class StoreError(ContextHygieneError):
    """Database/storage operation failed."""


class ConfigError(ContextHygieneError):
    """Configuration read/write/validation failed."""


class ParseError(ContextHygieneError):
    """Conversation file parsing failed."""


class AnalysisError(ContextHygieneError):
    """Analysis operation failed."""


class LicenseError(ContextHygieneError):
    """License validation failed."""


class LLMError(ContextHygieneError):
    """LLM provider communication failed."""
