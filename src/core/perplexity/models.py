"""Data models for Perplexity AI service."""

from dataclasses import dataclass
from typing import Any


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a Perplexity API call."""

    input_tokens: int
    output_tokens: int
    citation_tokens: int
    search_queries: int
    reasoning_tokens: int
    input_cost: float
    output_cost: float
    citation_cost: float
    search_cost: float
    reasoning_cost: float
    request_fee: float
    total_cost: float
    model: str
    timestamp: str


@dataclass
class SessionCostSummary:
    """Summary of costs for the current session."""

    total_calls: int
    total_cost: float
    breakdown_by_model: dict[str, float]
    breakdown_by_type: dict[str, float]
    calls_details: list[CostBreakdown]


@dataclass
class ParallelAnalysisResult:
    """Result of parallel analysis with consistency scoring and consensus."""

    primary_analysis: str
    secondary_analysis: str
    recommendations_primary: list[dict[str, Any]] | None
    recommendations_secondary: list[dict[str, Any]] | None
    consistency_score: float
    consensus_recommendations: list[dict[str, Any]] | None
    discrepancies: list[str]
