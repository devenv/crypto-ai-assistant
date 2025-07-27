"""Perplexity AI service for generating trading analysis and recommendations.

This module provides backward compatibility by re-exporting all components
from the new modular perplexity package structure.
"""

# Re-export everything from the new modular structure for backward compatibility
from .perplexity import (
    AnalysisGenerator,
    CostBreakdown,
    CostTracker,
    ParallelAnalysisResult,
    PerplexityService,
    QualityValidator,
    SessionCostSummary,
    TextAnalyzer,
)

# Maintain all exports for backward compatibility
__all__ = [
    "PerplexityService",
    "CostBreakdown",
    "SessionCostSummary",
    "ParallelAnalysisResult",
    "AnalysisGenerator",
    "CostTracker",
    "QualityValidator",
    "TextAnalyzer",
]
