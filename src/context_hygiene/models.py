"""Pydantic models and enums for context-hygiene."""

from __future__ import annotations

import sys
from datetime import datetime

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return self.value


from pydantic import BaseModel, Field


class Role(StrEnum):
    """Conversation message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Grade(StrEnum):
    """Overall hygiene grade."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class AnalysisMode(StrEnum):
    """Analysis depth mode."""

    FAST = "fast"
    DEEP = "deep"


class Segment(BaseModel):
    """A single conversation segment (message or block)."""

    index: int
    role: Role
    content: str
    token_estimate: int = 0
    timestamp: datetime | None = None

    def model_post_init(self, __context: object) -> None:
        if self.token_estimate == 0:
            self.token_estimate = estimate_tokens(self.content)


class StalenessResult(BaseModel):
    """Staleness analysis for a segment."""

    segment_index: int
    score: float = 0.0  # 0 = fresh, 1 = completely stale
    reasons: list[str] = Field(default_factory=list)


class Contradiction(BaseModel):
    """A detected contradiction between segments."""

    segment_a: int
    segment_b: int
    description: str
    confidence: float = 0.0  # 0-1


class DeadweightResult(BaseModel):
    """A segment identified as deadweight."""

    segment_index: int
    reason: str
    tokens_recoverable: int = 0


class CompressionCandidate(BaseModel):
    """A group of segments that could be compressed."""

    segment_indices: list[int] = Field(default_factory=list)
    current_tokens: int = 0
    estimated_compressed_tokens: int = 0
    reason: str = ""

    @property
    def savings_tokens(self) -> int:
        return self.current_tokens - self.estimated_compressed_tokens

    @property
    def savings_pct(self) -> float:
        if self.current_tokens == 0:
            return 0.0
        return self.savings_tokens / self.current_tokens * 100


class HygieneReport(BaseModel):
    """Complete hygiene analysis report."""

    file_path: str = ""
    total_segments: int = 0
    total_tokens: int = 0
    grade: Grade = Grade.A
    staleness_score: float = 0.0  # weighted avg 0-1
    staleness_results: list[StalenessResult] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    deadweight: list[DeadweightResult] = Field(default_factory=list)
    compression_candidates: list[CompressionCandidate] = Field(default_factory=list)
    tokens_recoverable: int = 0
    analyzed_at: datetime | None = None
    mode: AnalysisMode = AnalysisMode.FAST

    def compute_grade(self) -> Grade:
        """Compute grade from analysis results."""
        score = 100.0
        # Staleness penalty: up to -30
        score -= self.staleness_score * 30
        # Contradiction penalty: -10 each, max -30
        score -= min(len(self.contradictions) * 10, 30)
        # Deadweight penalty: proportional to recoverable tokens
        if self.total_tokens > 0:
            waste_ratio = self.tokens_recoverable / self.total_tokens
            score -= waste_ratio * 40

        if score >= 90:
            return Grade.A
        elif score >= 75:
            return Grade.B
        elif score >= 60:
            return Grade.C
        elif score >= 40:
            return Grade.D
        return Grade.F


class AuditSummary(BaseModel):
    """Stored audit summary for history."""

    audit_id: int = 0
    file_path: str = ""
    grade: Grade = Grade.A
    total_tokens: int = 0
    tokens_recoverable: int = 0
    contradiction_count: int = 0
    deadweight_count: int = 0
    audited_at: datetime | None = None


def estimate_tokens(text: str) -> int:
    """Estimate token count. Uses tiktoken if available, else word proxy."""
    try:
        import tiktoken

        enc = tiktoken.encoding_for_model("gpt-4")
        return len(enc.encode(text))
    except (ImportError, ModuleNotFoundError, KeyError, OSError):
        # tiktoken not installed, model unknown, or I/O error — fall back to word proxy
        words = len(text.split())
        return max(int(words * 1.3), 1) if words else 0
