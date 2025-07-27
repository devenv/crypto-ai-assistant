"""Cost tracking and calculation for Perplexity API calls."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import CostBreakdown, SessionCostSummary

logger = logging.getLogger(__name__)


class CostTracker:
    """Handles cost calculation and session tracking for Perplexity API calls."""

    # Perplexity API Pricing (2024) - https://docs.perplexity.ai/getting-started/pricing
    MODEL_PRICING = {
        "sonar": {
            "input": 1.0,  # $/1M tokens
            "output": 1.0,  # $/1M tokens
            "citation": 0.0,  # Not applicable
            "search": 0.0,  # Not applicable
            "reasoning": 0.0,  # Not applicable
        },
        "sonar-pro": {
            "input": 3.0,
            "output": 15.0,
            "citation": 0.0,
            "search": 0.0,
            "reasoning": 0.0,
        },
        "sonar-large": {
            "input": 3.0,  # Assume same as sonar-pro
            "output": 15.0,
            "citation": 0.0,
            "search": 0.0,
            "reasoning": 0.0,
        },
        "sonar-deep-research": {
            "input": 2.0,
            "output": 8.0,
            "citation": 2.0,
            "search": 5.0,  # $/1K searches
            "reasoning": 3.0,
        },
    }

    def __init__(self) -> None:
        """Initialize cost tracker."""
        self.session_costs: list[CostBreakdown] = []
        self._load_session_costs()

    def _load_session_costs(self) -> None:
        """Load existing session costs from file if it exists."""
        cost_file = Path("session_costs.json")
        if cost_file.exists():
            try:
                with open(cost_file) as f:
                    data = json.load(f)
                    # Only load costs from today
                    today = datetime.now(UTC).strftime("%Y-%m-%d")
                    for cost_data in data:
                        if cost_data["timestamp"].startswith(today):
                            self.session_costs.append(CostBreakdown(**cost_data))
            except (json.JSONDecodeError, KeyError, TypeError):
                # If file is corrupted or format changed, start fresh
                self.session_costs = []

    def _save_session_costs(self) -> None:
        """Save session costs to file."""
        cost_file = Path("session_costs.json")
        try:
            cost_data = [
                {
                    "input_tokens": cost.input_tokens,
                    "output_tokens": cost.output_tokens,
                    "citation_tokens": cost.citation_tokens,
                    "search_queries": cost.search_queries,
                    "reasoning_tokens": cost.reasoning_tokens,
                    "input_cost": cost.input_cost,
                    "output_cost": cost.output_cost,
                    "citation_cost": cost.citation_cost,
                    "search_cost": cost.search_cost,
                    "reasoning_cost": cost.reasoning_cost,
                    "request_fee": cost.request_fee,
                    "total_cost": cost.total_cost,
                    "model": cost.model,
                    "timestamp": cost.timestamp,
                }
                for cost in self.session_costs
            ]
            with open(cost_file, "w") as f:
                json.dump(cost_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save session costs: {e}")

    def calculate_cost(self, response: dict[str, Any], model: str) -> CostBreakdown:
        """
        Calculate the cost of an API call based on token usage and model pricing.

        Args:
            response: API response containing usage information
            model: Model name used for the call

        Returns:
            CostBreakdown with detailed cost information
        """
        # Extract usage information from response
        usage = response.get("usage", {})

        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # For deep research, extract additional metrics
        citation_tokens = 0
        search_queries = 0
        reasoning_tokens = 0

        # Check for extended usage info (sonar-deep-research)
        if "search_results" in response:
            search_queries = len(response.get("search_results", []))

        # Estimate citation and reasoning tokens for deep research
        if model == "sonar-deep-research":
            # Rough estimates based on typical patterns
            citation_tokens = int(output_tokens * 0.1)  # ~10% of output for citations
            reasoning_tokens = int(total_tokens * 0.05)  # ~5% for reasoning

        # Get model pricing
        pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING["sonar"])

        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        citation_cost = (citation_tokens / 1_000_000) * pricing["citation"]
        search_cost = (search_queries / 1_000) * pricing["search"]
        reasoning_cost = (reasoning_tokens / 1_000_000) * pricing["reasoning"]

        # Estimate request fee (varies by search context size)
        # Conservative estimate: $0.005 for sonar models, $0.006 for deep research
        request_fee = 0.006 if model == "sonar-deep-research" else 0.005

        total_cost = input_cost + output_cost + citation_cost + search_cost + reasoning_cost + request_fee

        cost_breakdown = CostBreakdown(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            citation_tokens=citation_tokens,
            search_queries=search_queries,
            reasoning_tokens=reasoning_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            citation_cost=citation_cost,
            search_cost=search_cost,
            reasoning_cost=reasoning_cost,
            request_fee=request_fee,
            total_cost=total_cost,
            model=model,
            timestamp=datetime.now(UTC).isoformat(),
        )

        # Track the cost
        self.session_costs.append(cost_breakdown)
        self._save_session_costs()

        logger.debug(f"API call cost: ${cost_breakdown.total_cost:.4f} ({cost_breakdown.input_tokens} input, {cost_breakdown.output_tokens} output tokens)")

        return cost_breakdown

    def get_session_cost_summary(self) -> SessionCostSummary:
        """
        Get a summary of costs for the current session.

        Returns:
            SessionCostSummary with aggregated cost information
        """
        if not self.session_costs:
            return SessionCostSummary(
                total_calls=0,
                total_cost=0.0,
                breakdown_by_model={},
                breakdown_by_type={},
                calls_details=[],
            )

        total_cost = sum(cost.total_cost for cost in self.session_costs)

        # Breakdown by model
        breakdown_by_model: dict[str, float] = {}
        for cost in self.session_costs:
            breakdown_by_model[cost.model] = breakdown_by_model.get(cost.model, 0.0) + cost.total_cost

        # Breakdown by cost type
        breakdown_by_type = {
            "Input Tokens": sum(cost.input_cost for cost in self.session_costs),
            "Output Tokens": sum(cost.output_cost for cost in self.session_costs),
            "Citations": sum(cost.citation_cost for cost in self.session_costs),
            "Search Queries": sum(cost.search_cost for cost in self.session_costs),
            "Reasoning": sum(cost.reasoning_cost for cost in self.session_costs),
            "Request Fees": sum(cost.request_fee for cost in self.session_costs),
        }

        return SessionCostSummary(
            total_calls=len(self.session_costs),
            total_cost=total_cost,
            breakdown_by_model=breakdown_by_model,
            breakdown_by_type=breakdown_by_type,
            calls_details=self.session_costs.copy(),
        )

    def format_cost_report(self) -> str:
        """
        Format a human-readable cost report for the current session.

        Returns:
            Formatted cost report string
        """
        summary = self.get_session_cost_summary()

        if summary.total_calls == 0:
            return "📊 **PERPLEXITY API COSTS**: No API calls made in this session."

        report_lines = [
            "📊 **PERPLEXITY API COST REPORT**",
            f"💰 **Total Session Cost**: ${summary.total_cost:.4f}",
            f"📞 **Total API Calls**: {summary.total_calls}",
            f"💵 **Average Cost per Call**: ${summary.total_cost / summary.total_calls:.4f}",
            "",
            "🔍 **Breakdown by Model**:",
        ]

        for model, cost in summary.breakdown_by_model.items():
            calls_count = sum(1 for c in summary.calls_details if c.model == model)
            report_lines.append(f"  • {model}: ${cost:.4f} ({calls_count} calls)")

        report_lines.extend(
            [
                "",
                "📋 **Breakdown by Cost Type**:",
            ]
        )

        for cost_type, cost in summary.breakdown_by_type.items():
            if cost > 0:
                report_lines.append(f"  • {cost_type}: ${cost:.4f}")

        # Add cost efficiency insights
        if summary.total_cost > 0.10:  # If session cost is significant
            report_lines.extend(
                [
                    "",
                    "💡 **Cost Optimization Tips**:",
                    "  • Consider using 'sonar' model for monitoring tasks",
                    "  • 'sonar-deep-research' provides most value for strategic analysis",
                    "  • Monitor token usage to optimize prompt length",
                ]
            )

        return "\n".join(report_lines)
