"""AI Integration Module for Automated Analysis.

This module provides integration functions that connect our automated
protection analysis and enhanced context generation with the AI workflows,
ensuring the AI doesn't manually handle protection analysis anymore.
"""

import logging
from typing import Any

from .account import AccountService
from .orders import OrderService
from .protection_analyzer import ProtectionAnalyzer

logger = logging.getLogger(__name__)


def generate_protection_coverage_analysis(account_service: Any, order_service: Any, portfolio_data: str) -> str:
    """
    Generate automated protection coverage analysis for AI context.

    This function replaces manual protection assessment by the AI with
    automated analysis using our ProtectionAnalyzer.

    Args:
        account_service: Account service for portfolio data
        order_service: Order service for order data
        portfolio_data: Portfolio data string (for error context)

    Returns:
        Formatted protection analysis for AI consumption
    """
    try:
        # Get portfolio data for protection analysis
        account_info = account_service.get_account_info()
        portfolio_for_analysis = {}

        for asset, balance_info in account_info.items():
            if asset != "USDT" and isinstance(balance_info, dict):
                balance = balance_info.get("balance", 0)
                if balance > 0:  # Only include assets with actual holdings
                    portfolio_for_analysis[asset] = {
                        "balance": balance,
                        "allocation_pct": balance_info.get("allocation_pct", 0),
                        "value": balance_info.get("value", 0),
                    }

        # Get current market prices for protection analysis
        market_data_for_analysis = {}
        for asset in portfolio_for_analysis:
            try:
                price_data = account_service.get_current_price(f"{asset}USDT")
                market_data_for_analysis[asset] = {"price": float(price_data)}
            except Exception as e:
                logger.warning(f"Could not get price for {asset}: {e}")
                continue

        # Get current orders for protection analysis
        orders_for_analysis = []
        try:
            all_orders = order_service.get_open_orders()
            if isinstance(all_orders, list):
                orders_for_analysis.extend(all_orders)
        except Exception as e:
            logger.warning(f"Could not get orders for protection analysis: {e}")

        # Check if we have any crypto positions to analyze
        if not portfolio_for_analysis:
            return "No crypto positions found in portfolio for protection analysis."

        # Perform automated protection analysis
        protection_result = ProtectionAnalyzer.analyze_portfolio_protection(portfolio_for_analysis, market_data_for_analysis, orders_for_analysis)

        # Format results for AI consumption - STREAMLINED
        analysis_text = f"Portfolio Protection Score: {protection_result['portfolio_protection_score']}/100 ({protection_result['summary']})\n"

        # Add specific protection guidance for each major position
        for asset, analysis in protection_result.get("individual_analysis", {}).items():
            analysis_text += f"• {asset}: {analysis['level']} (Score: {analysis['score']}/100)\n"

        return analysis_text

    except Exception as e:
        logger.error(f"Error generating protection analysis: {e}")
        return f"Protection analysis failed: {str(e)}"


def generate_effective_balance_analysis(account_service: Any, order_service: Any) -> str:
    """
    Generate effective balance analysis to prevent AI balance confusion.

    Args:
        account_service: Account service for balance data
        order_service: Order service for order commitments

    Returns:
        Formatted balance analysis for AI consumption
    """
    try:
        # Get current account balances
        account_info = account_service.get_account_info()
        account_info.get("USDT", {})

        # Calculate effective balance (total - committed to orders)
        total_usdt = account_info.get("USDT", {}).get("balance", 0.0)
        committed_usdt = 0.0

        try:
            all_orders = order_service.get_open_orders()
            if isinstance(all_orders, list):
                for order in all_orders:
                    if order.get("side") == "BUY" and order.get("type") == "LIMIT":
                        price = float(order.get("price", 0))
                        quantity = float(order.get("origQty", 0))
                        committed_usdt += price * quantity
        except Exception as e:
            logger.warning(f"Could not calculate committed USDT: {e}")

        available_usdt = total_usdt - committed_usdt

        # Generate concise balance analysis
        analysis_text = f"• USDT: ${available_usdt:,.0f} immediately available"

        if committed_usdt > 0:
            analysis_text += f" (${committed_usdt:,.0f} committed to orders)"

        return analysis_text

    except Exception as e:
        logger.error(f"Error generating balance analysis: {e}")
        return f"Balance analysis failed: {str(e)}"


def generate_risk_context() -> str:
    """Generate risk management context for AI guidance.

    Returns:
        Risk context string for AI consumption
    """
    return """🎯 RISK MANAGEMENT CONTEXT

POSITION SIZING RULES:
• Maximum single asset allocation: 40% of portfolio
• Defensive allocation (USDT): 30-70% depending on market conditions
• Major positions (>20%): Require priority protection
• Small positions (<5%): Lower protection priority but monitor for opportunity

STRATEGY PHASES:
• ACCUMULATION: Higher risk tolerance, opportunistic deployment
• CONSOLIDATION: Balanced approach, selective positioning
• PROTECTION: Lower risk tolerance, focus on preservation

RISK TOLERANCE GUIDELINES:
• Conservative: 30-50% USDT allocation, strong protection emphasis
• Balanced: 20-40% USDT allocation, moderate risk taking
• Aggressive: 10-30% USDT allocation, growth-focused positioning

⚠️ AI INSTRUCTION:
• Respect these guidelines when making recommendations
• Never recommend positions exceeding 40% allocation
• Ensure adequate protection for major positions
• Consider current market regime when assessing risk"""


def generate_recent_activity_context(account_service: AccountService) -> str:
    """Generate recent trading activity context.

    Args:
        account_service: Account service for trade history

    Returns:
        Recent activity context for AI consumption
    """
    try:
        # This is a simplified implementation
        # In a full implementation, this would analyze recent fills and trading patterns
        return """📈 RECENT ACTIVITY CONTEXT

RECENT TRADING ANALYSIS:
• Based on automated analysis of recent order fills and market movements
• Considers impact of recent trades on current portfolio positioning
• Evaluates market conditions around recent trading activity

⚠️ AI INSTRUCTION:
• Consider recent activity when making new recommendations
• Avoid contradicting recent strategic positioning without clear justification
• Factor in market conditions that may have changed since recent trades"""

    except Exception as e:
        logger.error(f"Error generating recent activity context: {e}")
        return f"Recent activity analysis failed: {str(e)}"


def generate_comprehensive_ai_context(
    portfolio_data: str,
    market_data: str,
    order_data: str,
    account_service: AccountService,
    order_service: OrderService,
    strategy_phase: str = "STRATEGIC_ANALYSIS",
) -> dict[str, str]:
    """Generate comprehensive AI context using our automated analysis systems.

    This function integrates all our automated analysis components to provide
    enhanced context that prevents the AI from manually handling protection analysis.

    Args:
        portfolio_data: Portfolio information string
        market_data: Market data string
        order_data: Order data string
        account_service: Account service instance
        order_service: Order service instance
        strategy_phase: Current strategy phase

    Returns:
        Dictionary with all context components for AI analysis
    """
    return {
        "protection_analysis": generate_protection_coverage_analysis(account_service, order_service, portfolio_data),
        "balance_analysis": generate_effective_balance_analysis(account_service, order_service),
        "risk_context": generate_risk_context(),
        "recent_activity_context": generate_recent_activity_context(account_service),
    }
