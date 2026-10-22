"""Context window hygiene analyzer for LLM conversations."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("context-hygiene")
except PackageNotFoundError:  # pragma: no cover - source tree without an installed package
    __version__ = "0+unknown"

from context_hygiene.api import audit_file, score_file

__all__ = ["__version__", "audit_file", "score_file"]
