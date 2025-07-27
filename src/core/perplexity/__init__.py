"""Perplexity AI service module for crypto trading analysis.

This module provides a comprehensive AI-powered analysis service for cryptocurrency
trading strategies using Perplexity's advanced search and reasoning capabilities.
"""

# Main service class
# Component classes (for advanced usage)
from .analysis_generator import AnalysisGenerator
from .cost_tracker import CostTracker

# Data models
from .models import CostBreakdown, ParallelAnalysisResult, SessionCostSummary
from .quality_validator import QualityValidator
from .service import PerplexityService
from .text_analyzer import TextAnalyzer

# Main exports for backward compatibility
__all__ = [
    # Main service
    "PerplexityService",
    # Data models
    "CostBreakdown",
    "SessionCostSummary",
    "ParallelAnalysisResult",
    # Component classes
    "AnalysisGenerator",
    "CostTracker",
    "QualityValidator",
    "TextAnalyzer",
]
