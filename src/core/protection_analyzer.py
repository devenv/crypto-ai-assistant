"""Protection Analysis Module for Trading Portfolio.

This module provides automated analysis of existing protective orders
to prevent redundant protection recommendations and improve strategic decision-making.
"""

import logging
from typing import Any

from api.models import Order

logger = logging.getLogger(__name__)


class ProtectionAnalyzer:
    """Analyzes portfolio protection coverage and provides recommendations."""

    def __init__(self, client):
        """Initialize protection analyzer with Binance client."""
        self._client = client

    @staticmethod
    def calculate_protection_score(symbol: str, current_price: float, existing_orders: list[Order], position_quantity: float = 0.0) -> dict[str, Any]:
        """
        Calculate protection coverage score for a symbol position.

        Args:
            symbol: Trading symbol (e.g., 'ETHUSDT')
            current_price: Current market price
            existing_orders: List of existing orders
            position_quantity: Size of position to protect (optional)

        Returns:
            Dictionary with protection analysis results
        """
        score: int = 0
        details: dict[str, str | int | float] = {
            "proximity_score": 0,
            "coverage_score": 0,
            "diversification_score": 0,
            "protective_orders_count": 0,
            "closest_protection_distance": "N/A",
            "total_protected_quantity": 0.0,
        }

        # Filter for protective orders:
        # - SELL LIMIT above current price (take-profit)
        # - SELL STOP/STOP_LOSS/STOP_LOSS_LIMIT below current price (stop-loss)
        protective_orders = []
        for order in existing_orders:
            try:
                side = order.get("side")
                otype = order.get("type")
                price = float(order.get("price", 0))

                if side == "SELL" and otype == "LIMIT" and price > current_price:
                    protective_orders.append(order)
                elif side == "SELL" and otype in {"STOP", "STOP_LOSS", "STOP_LOSS_LIMIT"} and price < current_price:
                    protective_orders.append(order)
            except (ValueError, TypeError):
                # Skip orders with invalid price data
                continue

        details["protective_orders_count"] = len(protective_orders)

        if not protective_orders:
            return {
                "score": 0,
                "level": "NONE",
                "recommendation": "IMPLEMENT_PROTECTION",
                "details": details,
                "analysis_summary": f"No protective orders found for {symbol}. Consider implementing protection.",
            }

        # PROXIMITY SCORING (50 points max)
        closest_order = min(protective_orders, key=lambda x: abs(float(x.get("price", 0)) - current_price))
        closest_price = float(closest_order.get("price", 0))

        # Prevent division by zero
        if current_price == 0:
            return {
                "score": 0,
                "level": "NONE",
                "recommendation": "IMPLEMENT_PROTECTION",
                "details": details,
                "analysis_summary": f"Invalid current price for {symbol}. Cannot analyze protection.",
            }

        distance_pct = (closest_price - current_price) / current_price
        details["closest_protection_distance"] = f"{distance_pct:.1%}"

        proximity_score = 0
        if distance_pct <= 0.05:  # Within 5%
            proximity_score = 50
        elif distance_pct <= 0.10:  # Within 10%
            proximity_score = 40
        elif distance_pct <= 0.15:  # Within 15%
            proximity_score = 25
        elif distance_pct <= 0.25:  # Within 25%
            proximity_score = 10

        details["proximity_score"] = proximity_score
        score += proximity_score

        # COVERAGE SCORING (30 points max)
        total_protected_qty = 0.0
        for order in protective_orders:
            try:
                qty = float(order.get("origQty", 0))
                total_protected_qty += qty
            except (ValueError, TypeError):
                continue

        details["total_protected_quantity"] = total_protected_qty

        coverage_score = 0
        if position_quantity > 0:
            coverage_ratio = total_protected_qty / position_quantity
            if coverage_ratio >= 0.95:  # 95%+ covered
                coverage_score = 30
            elif coverage_ratio >= 0.75:  # 75%+ covered
                coverage_score = 25
            elif coverage_ratio >= 0.50:  # 50%+ covered
                coverage_score = 15
            elif coverage_ratio >= 0.25:  # 25%+ covered
                coverage_score = 5
        else:
            # If no position quantity provided, give points for having protection
            if total_protected_qty > 0:
                coverage_score = 20  # Moderate score for unknown coverage

        details["coverage_score"] = coverage_score
        score += coverage_score

        # DIVERSIFICATION SCORING (20 points max)
        # Points for multiple protection levels
        unique_prices = set()
        for order in protective_orders:
            try:
                price = float(order.get("price", 0))
                unique_prices.add(round(price, 2))
            except (ValueError, TypeError):
                continue

        diversification_score = 0
        if len(unique_prices) >= 3:
            diversification_score = 20
        elif len(unique_prices) == 2:
            diversification_score = 10
        elif len(unique_prices) == 1:
            diversification_score = 5

        details["diversification_score"] = diversification_score
        score += diversification_score

        # Determine protection level and recommendation
        if score >= 90:
            level = "EXCELLENT"
            recommendation = "MAINTAIN_CURRENT"
        elif score >= 70:
            level = "GOOD"
            recommendation = "MINOR_IMPROVEMENTS"
        elif score >= 50:
            level = "MODERATE"
            recommendation = "ENHANCE_PROTECTION"
        elif score >= 30:
            level = "WEAK"
            recommendation = "SIGNIFICANT_IMPROVEMENT"
        else:
            level = "POOR"
            recommendation = "IMPLEMENT_PROTECTION"

        # Generate analysis summary
        summary_parts = [
            f"{symbol} Protection Score: {score}/100 ({level})",
            f"Protective orders: {len(protective_orders)}",
            f"Closest protection: {details['closest_protection_distance']}",
        ]

        if position_quantity > 0:
            coverage_pct = (total_protected_qty / position_quantity) * 100
            summary_parts.append(f"Coverage: {coverage_pct:.1f}% of position")

        analysis_summary = " | ".join(summary_parts)

        return {
            "score": score,
            "level": level,
            "recommendation": recommendation,
            "details": details,
            "analysis_summary": analysis_summary,
        }

    @staticmethod
    def analyze_portfolio_protection(
        portfolio_data: dict[str, dict[str, Any]], market_data: dict[str, dict[str, Any]], all_orders: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze protection across entire portfolio.

        Args:
            portfolio_data: Dict of {symbol: {balance, value, allocation}}
            market_data: Dict of {symbol: {price, ...}}
            all_orders: List of all existing orders

        Returns:
            Comprehensive portfolio protection analysis
        """
        portfolio_analysis = {}
        overall_scores = []
        protection_recommendations = []

        for symbol, position_info in portfolio_data.items():
            # Skip USDT and very small positions
            if symbol == "USDT" or position_info.get("allocation_pct", 0) < 1.0:
                continue

            current_price = market_data.get(symbol, {}).get("price", 0)
            if current_price <= 0:
                continue

            # Filter orders for this symbol
            symbol_orders = [order for order in all_orders if order.get("symbol") == f"{symbol}USDT"]
            position_size = position_info.get("balance", 0)

            analysis = ProtectionAnalyzer.calculate_protection_score(f"{symbol}USDT", current_price, symbol_orders, position_size)

            portfolio_analysis[symbol] = analysis
            overall_scores.append(analysis["score"])

            if analysis["recommendation"] in ["IMPLEMENT_PROTECTION", "URGENT_PROTECTION"]:
                protection_recommendations.append(analysis["analysis_summary"])

        # Calculate portfolio-wide protection score
        portfolio_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0

        return {
            "portfolio_protection_score": round(portfolio_score, 1),
            "individual_analysis": portfolio_analysis,
            "protection_recommendations": protection_recommendations,
            "summary": ProtectionAnalyzer._generate_portfolio_summary(portfolio_score, len(protection_recommendations), len(portfolio_analysis)),
        }

    @staticmethod
    def _generate_portfolio_summary(portfolio_score: float, recommendations_count: int, positions_analyzed: int) -> str:
        """Generate portfolio protection summary."""
        if portfolio_score >= 85:
            return f"Portfolio protection: EXCELLENT ({portfolio_score:.1f}/100). All {positions_analyzed} major positions well protected."
        elif portfolio_score >= 70:
            return f"Portfolio protection: GOOD ({portfolio_score:.1f}/100). Minor improvements may be beneficial."
        elif portfolio_score >= 50:
            return f"Portfolio protection: MODERATE ({portfolio_score:.1f}/100). {recommendations_count} positions need attention."
        else:
            return f"Portfolio protection: POOR ({portfolio_score:.1f}/100). {recommendations_count} positions require immediate protection."
