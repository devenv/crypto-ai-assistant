"""Automated validation service for external AI recommendations."""

import logging
from dataclasses import dataclass

from api.client import BinanceClient
from api.enums import OrderSide, OrderType

from .account import AccountService
from .config import AppConfig
from .indicators import IndicatorService
from .orders import OrderService

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of automated validation with scoring and details."""

    is_valid: bool
    score: int  # 0-100 (actionable issues only)
    technical_score: int  # 0-100 (technical quality)
    category_scores: dict[str, int]
    errors: list[str]  # Only actionable errors
    warnings: list[str]  # Only actionable warnings
    technical_issues: list[str]  # Non-actionable technical limitations
    recommendations: list[str]


@dataclass
class AIRecommendation:
    """Structured representation of external AI trading recommendation."""

    symbol: str
    action: str  # 'BUY', 'SELL', 'OCO', 'CANCEL'
    quantity: float
    price: float | None = None
    stop_price: float | None = None
    reasoning: str = ""
    expected_current_price: float | None = None


class ValidationService:
    """Automated validation service for external AI recommendations."""

    def __init__(self, client: BinanceClient, config: AppConfig):
        """Initialize the validation service.

        Args:
            client: BinanceClient instance for API calls.
            config: Application configuration.
        """
        self._client = client
        self._account_service = AccountService(client)
        self._indicator_service = IndicatorService(client, config)
        self._order_service = OrderService(client)

    def validate_ai_recommendations(self, recommendations: list[AIRecommendation]) -> ValidationResult:
        """Validate a list of AI recommendations with separated actionable vs technical scoring.

        This separates technical limitations (AI data quality) from actionable issues
        (user needs to do something) to prevent false alarms in monitoring.

        Args:
            recommendations: List of AI recommendations to validate.

        Returns:
            ValidationResult with separated scores and categorized feedback.
        """
        actionable_score = 0
        technical_score = 0
        category_scores = {
            "technical_validity": 0,  # 25 points (actionable)
            "risk_management": 0,  # 25 points (actionable)
            "execution_feasibility": 0,  # 25 points (actionable)
            "portfolio_alignment": 0,  # 25 points (actionable)
        }
        actionable_errors: list[str] = []
        actionable_warnings: list[str] = []
        technical_issues: list[str] = []
        recommendations_list: list[str] = []

        try:
            # 1. Technical Validity (25 points) - ACTIONABLE
            technical_score_val, technical_issues_val = self._validate_technical_indicators(recommendations)
            category_scores["technical_validity"] = technical_score_val
            # Only flag severe technical violations as actionable
            actionable_errors.extend([issue for issue in technical_issues_val if "BUY recommendation with RSI" in issue and "overbought" in issue])
            actionable_warnings.extend([issue for issue in technical_issues_val if "WARNING" in issue and "RSI" in issue])

            # 2. Risk Management (25 points) - ACTIONABLE
            risk_score, risk_issues = self._validate_risk_management(recommendations)
            category_scores["risk_management"] = risk_score
            actionable_errors.extend([issue for issue in risk_issues if "ERROR" in issue])
            actionable_warnings.extend(
                [issue for issue in risk_issues if "WARNING" in issue and ("protective" in issue.lower() or "stop-loss" in issue.lower())]
            )

            # 3. Execution Feasibility (25 points) - ACTIONABLE
            execution_score, execution_issues = self._validate_execution_feasibility(recommendations)
            category_scores["execution_feasibility"] = execution_score
            # Only flag critical execution issues as actionable
            actionable_errors.extend([issue for issue in execution_issues if "CRITICAL" in issue or "insufficient" in issue.lower()])
            actionable_warnings.extend([issue for issue in execution_issues if "WARNING" in issue and "balance" not in issue.lower()])

            # 4. Portfolio Alignment (25 points) - ACTIONABLE
            portfolio_score, portfolio_issues = self._validate_portfolio_alignment(recommendations)
            category_scores["portfolio_alignment"] = portfolio_score
            # Filter out non-actionable "conflicts" that are actually just existing orders
            for issue in portfolio_issues:
                if "ERROR" in issue:
                    actionable_errors.append(issue)
                elif "WARNING" in issue and ("diversification" in issue.lower() or "allocation" in issue.lower()):
                    actionable_warnings.append(issue)
                # Skip "price conflicts" - they're just awareness, not problems

            # Calculate actionable score (only things user can/should act on)
            actionable_score = int(sum(category_scores.values()) / 4)  # Average of all categories

            # Calculate technical score separately (for AI data quality assessment)
            data_freshness_score, data_freshness_issues = self._assess_data_freshness(recommendations)
            technical_score = data_freshness_score
            technical_issues.extend(data_freshness_issues)

            # Generate recommendations based on ACTIONABLE score only
            if actionable_score >= 90:
                recommendations_list.append("✅ Excellent - No significant actionable issues found")
            elif actionable_score >= 75:
                recommendations_list.append("🟡 Good - Minor actionable adjustments needed")
                recommendations_list.append("Review warnings for optimization opportunities")
            elif actionable_score >= 60:
                recommendations_list.append("🟠 Fair - Several actionable issues require attention")
                recommendations_list.append("Address errors and consider warnings before execution")
            else:
                recommendations_list.append("🚨 Poor - Critical actionable issues found")
                recommendations_list.append("Must resolve all errors before proceeding")

            # Specific improvement recommendations (actionable only)
            if category_scores["technical_validity"] < 20:
                recommendations_list.append("→ Review technical analysis - may be trading against momentum")
            if category_scores["risk_management"] < 20:
                recommendations_list.append("→ Add protective orders for new positions")
            if category_scores["execution_feasibility"] < 20:
                recommendations_list.append("→ Check available balances and order precision")
            if category_scores["portfolio_alignment"] < 20:
                recommendations_list.append("→ Consider portfolio diversification impact")

            # Add technical assessment (informational)
            if technical_score < 50:
                technical_issues.append("Warning: Low data quality detected - consider fresh analysis")

        except Exception as e:
            logger.error(f"Validation service error: {e}")
            actionable_errors.append(f"Validation service error: {str(e)}")
            actionable_score = 0
            technical_score = 0

        return ValidationResult(
            is_valid=len(actionable_errors) == 0 and actionable_score >= 60,
            score=actionable_score,
            technical_score=technical_score,
            category_scores=category_scores,
            errors=actionable_errors,
            warnings=actionable_warnings,
            technical_issues=technical_issues,
            recommendations=recommendations_list,
        )

    def _assess_data_freshness(self, recommendations: list[AIRecommendation]) -> tuple[int, list[str]]:
        """Assess AI data quality without penalizing user (technical assessment only)."""
        issues: list[str] = []
        score = 100  # Start optimistic

        try:
            # Get current prices for comparison
            current_prices: dict[str, float] = {}
            symbols: list[str] = list({rec.symbol for rec in recommendations})

            for symbol in symbols:
                try:
                    if symbol.endswith("USDT"):
                        coin = symbol[:-4]
                    else:
                        coin = symbol

                    indicators = self._indicator_service.get_indicators([coin])
                    if indicators and coin in indicators:
                        current_prices[symbol] = float(indicators[coin]["price"])
                except Exception:
                    pass

            # Compare AI's expected prices with current prices (informational only)
            for rec in recommendations:
                if rec.expected_current_price and rec.symbol in current_prices:
                    current_price: float = float(current_prices[rec.symbol])
                    expected_price: float = float(rec.expected_current_price)
                    price_diff_pct: float = abs(current_price - expected_price) / expected_price * 100

                    if price_diff_pct > 10:
                        issues.append(
                            f"INFO: {rec.symbol} price variance - AI expected ${expected_price:,.2f}, "
                            + f"current ${current_price:,.2f} ({price_diff_pct:.1f}% difference)"
                        )
                        score -= 20
                    elif price_diff_pct > 5:
                        issues.append(f"INFO: {rec.symbol} minor price variance ({price_diff_pct:.1f}%)")
                        score -= 10

        except Exception as e:
            issues.append(f"INFO: Could not assess data freshness: {e}")
            score = 50

        return max(0, score), issues

    def _validate_technical_indicators(self, recommendations: list[AIRecommendation]) -> tuple[int, list[str]]:
        """Validate technical indicators match AI assumptions."""
        issues: list[str] = []
        score = 25  # Start with full points

        try:
            # Get current indicators for all coins
            symbols = list({rec.symbol for rec in recommendations})
            coins: list[str] = []

            for symbol in symbols:
                if symbol.endswith("USDT"):
                    coins.append(symbol[:-4])
                else:
                    coins.append(symbol)

            indicators = self._indicator_service.get_indicators(coins)

            for rec in recommendations:
                coin = rec.symbol.replace("USDT", "")
                if coin not in indicators:
                    issues.append(f"WARNING: No technical indicators available for {coin}")
                    score -= 3
                    continue

                rsi = indicators[coin].get("rsi", 50)

                # Validate RSI-based recommendations - only flag extreme cases
                if rec.action == "BUY":
                    if rsi > 85:
                        issues.append(f"WARNING: {coin} BUY recommendation with RSI {rsi:.1f} (extremely overbought)")
                        score -= 5
                    # RSI 70-85 is normal in bull markets - no penalty

                elif rec.action == "SELL":
                    if rsi < 20:
                        issues.append(f"ERROR: {coin} SELL recommendation with RSI {rsi:.1f} (oversold)")
                        score -= 8
                    elif rsi < 30:
                        issues.append(f"WARNING: {coin} SELL recommendation with RSI {rsi:.1f} (low)")
                        score -= 3

        except Exception as e:
            issues.append(f"ERROR: Technical validation failed: {e}")
            score = 0

        return max(0, score), issues

    def _validate_risk_management(self, recommendations: list[AIRecommendation]) -> tuple[int, list[str]]:
        """Validate risk management aspects of recommendations."""
        issues: list[str] = []
        score = 20  # Start with full points

        try:
            # Check for protective orders (OCO/stop-losses) - only for significant positions
            buy_orders = [rec for rec in recommendations if rec.action == "BUY"]
            oco_orders = [rec for rec in recommendations if rec.action == "OCO"]

            # Only warn for larger buy positions (>$500) without protection
            large_buy_orders = [rec for rec in buy_orders if rec.price and rec.quantity * rec.price > 500]
            if large_buy_orders and not oco_orders:
                issues.append("WARNING: Large buy positions (>$500) without protective OCO orders")
                score -= 3

            # Validate stop-loss percentages
            for rec in recommendations:
                if rec.action == "OCO" and rec.stop_price and rec.price:
                    # Assuming current price is around the OCO creation level
                    stop_loss_pct = abs(rec.price - rec.stop_price) / rec.price * 100

                    if stop_loss_pct > 15:
                        issues.append(f"WARNING: {rec.symbol} stop-loss {stop_loss_pct:.1f}% may be too wide")
                        score -= 3
                    elif stop_loss_pct < 2:
                        issues.append(f"WARNING: {rec.symbol} stop-loss {stop_loss_pct:.1f}% may be too tight")
                        score -= 3

            # Validate position sizing
            total_buy_value = 0.0
            for rec in recommendations:
                if rec.action == "BUY" and rec.price:
                    total_buy_value += rec.quantity * rec.price

            # Get account info to check against portfolio size
            account_info = self._account_service.get_account_info()
            if account_info:
                usdt_balance = 0.0
                for balance in account_info.get("balances", []):
                    if balance["asset"] == "USDT":
                        usdt_balance = float(balance["free"])
                        break

                if total_buy_value > usdt_balance * 0.9:
                    issues.append("ERROR: Recommendations would deploy >90% of available cash")
                    score -= 10
                elif total_buy_value > usdt_balance * 0.5:
                    issues.append("WARNING: Recommendations would deploy >50% of available cash")
                    score -= 5

        except Exception as e:
            issues.append(f"ERROR: Risk management validation failed: {e}")
            score = 0

        return max(0, score), issues

    def _validate_execution_feasibility(self, recommendations: list[AIRecommendation]) -> tuple[int, list[str]]:
        """Validate that recommendations can be executed as specified."""
        issues: list[str] = []
        score = 15  # Start with full points

        try:
            for rec in recommendations:
                if rec.action in ["BUY", "SELL", "OCO"]:
                    # Determine order type and side
                    if rec.action == "BUY":
                        order_type = OrderType.LIMIT if rec.price else OrderType.MARKET
                        side = OrderSide.BUY
                    elif rec.action == "SELL":
                        order_type = OrderType.LIMIT
                        side = OrderSide.SELL
                    else:  # OCO
                        order_type = OrderType.OCO
                        side = OrderSide.SELL

                    # Use our enhanced order validator
                    from core.order_validator import OrderValidator

                    validator = OrderValidator(self._client)

                    is_valid, validation_errors = validator.validate_order_placement(
                        symbol=rec.symbol, side=side, order_type=order_type, quantity=rec.quantity, price=rec.price, stop_price=rec.stop_price
                    )

                    if not is_valid:
                        for error in validation_errors:
                            if "CRITICAL" in error:
                                issues.append(f"ERROR: {rec.symbol} - {error}")
                                score -= 5
                            else:
                                issues.append(f"WARNING: {rec.symbol} - {error}")
                                score -= 2

        except Exception as e:
            issues.append(f"ERROR: Execution feasibility validation failed: {e}")
            score = 0

        return max(0, score), issues

    def _validate_portfolio_alignment(self, recommendations: list[AIRecommendation]) -> tuple[int, list[str]]:
        """Validate portfolio alignment focusing on actionable strategic issues only."""
        issues: list[str] = []
        score = 25  # Start with full points

        try:
            # Check for order awareness (informational, not penalized)
            open_orders = self._order_service.get_open_orders()
            order_awareness_count = 0

            for rec in recommendations:
                for order in open_orders:
                    if order["symbol"] == rec.symbol:
                        existing_price = float(order["price"]) if order["price"] != "0.00000000" else 0
                        if rec.price and abs(existing_price - rec.price) < existing_price * 0.05:  # Within 5%
                            order_awareness_count += 1

            # Only flag actual strategic alignment issues
            # Validate diversification (actionable)
            symbols_involved = {rec.symbol for rec in recommendations}
            if len(symbols_involved) == 1 and len(recommendations) > 2:
                issues.append("WARNING: Heavy concentration in single asset - consider diversification")
                score -= 5

            # Check for reasonable allocation spreads (actionable)
            buy_recommendations = [rec for rec in recommendations if rec.action == "BUY"]
            if len(buy_recommendations) > 1:
                total_value = sum([rec.quantity * (rec.price or 0) for rec in buy_recommendations])
                for rec in buy_recommendations:
                    if rec.price and total_value > 0:
                        allocation_pct = (rec.quantity * rec.price) / total_value * 100
                        if allocation_pct > 70:
                            issues.append(f"WARNING: {rec.symbol} represents {allocation_pct:.1f}% of deployment - high concentration")
                            score -= 3

        except Exception as e:
            issues.append(f"ERROR: Portfolio alignment validation failed: {e}")
            score = 0

        return max(0, score), issues

    def generate_validation_report(self, result: ValidationResult) -> str:
        """Generate a human-readable validation report with separated actionable vs technical scores."""
        report: list[str] = []

        report.append("=" * 60)
        report.append("🤖 AUTOMATED AI RECOMMENDATION VALIDATION REPORT")
        report.append("=" * 60)

        # Actionable Score (primary - what user needs to care about)
        if result.score >= 90:
            status_emoji = "✅"
            status_text = "EXCELLENT"
        elif result.score >= 75:
            status_emoji = "🟡"
            status_text = "GOOD"
        elif result.score >= 60:
            status_emoji = "🟠"
            status_text = "FAIR"
        else:
            status_emoji = "🚨"
            status_text = "POOR"

        report.append(f"{status_emoji} ACTIONABLE SCORE: {result.score}/100 ({status_text})")

        # Technical Score (secondary - AI data quality assessment)
        tech_status = "Good" if result.technical_score >= 70 else "Stale" if result.technical_score >= 40 else "Poor"
        report.append(f"📊 Technical Data Quality: {result.technical_score}/100 ({tech_status})")
        report.append("")

        # Category Breakdown (actionable only)
        report.append("📊 ACTIONABLE CATEGORY SCORES:")
        for category, score in result.category_scores.items():
            max_score = 25  # All categories are now 25 points
            percentage = (score / max_score) * 100
            report.append(f"  • {category.replace('_', ' ').title()}: {score}/{max_score} ({percentage:.0f}%)")

        report.append("")

        # Actionable Errors (require user action)
        if result.errors:
            report.append("🚨 CRITICAL ERRORS (Require Action):")
            for error in result.errors:
                report.append(f"  • {error}")
            report.append("")

        # Actionable Warnings (user should consider)
        if result.warnings:
            report.append("⚠️  WARNINGS (Consider Addressing):")
            for warning in result.warnings:
                report.append(f"  • {warning}")
            report.append("")

        # Technical Issues (informational only)
        if result.technical_issues:
            report.append("ℹ️  TECHNICAL LIMITATIONS (Informational):")
            for issue in result.technical_issues:
                report.append(f"  • {issue}")
            report.append("")

        # Recommendations
        if result.recommendations:
            report.append("💡 RECOMMENDATIONS:")
            for rec in result.recommendations:
                report.append(f"  • {rec}")

        report.append("=" * 60)

        # Clear guidance based on actionable score
        if result.score >= 75:
            report.append("✅ FOCUS: Recommendations are actionable - review for execution")
        elif result.score >= 60:
            report.append("🟡 FOCUS: Address actionable issues, ignore technical limitations")
        else:
            report.append("🔴 FOCUS: Critical actionable issues must be resolved first")

        return "\n".join(report)
