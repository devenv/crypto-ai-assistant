"""Tests for Enhanced AI Context Generation Module."""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from src.core.ai_context_generator import AIContextGenerator


class TestAIContextGenerator:
    """Test suite for AIContextGenerator class."""

    @pytest.fixture
    def sample_portfolio_data(self) -> dict[str, Any]:
        """Sample portfolio data for testing."""
        return {
            "BTC": {"balance": 0.02126641, "value": 2520.02, "allocation_pct": 37.4},
            "ETH": {"balance": 0.0, "value": 0.0, "allocation_pct": 0.0},
            "TAO": {"balance": 0.5359021, "value": 240.41, "allocation_pct": 3.6},
            "USDT": {"balance": 3930.45, "value": 3930.45, "allocation_pct": 58.3},
        }

    @pytest.fixture
    def sample_market_data(self) -> dict[str, Any]:
        """Sample market data for testing."""
        return {
            "BTC": {"price": 118417.99, "rsi": 45.4, "signal": "STRONG BUY"},
            "ETH": {"price": 3695.50, "rsi": 45.03, "signal": "BUY"},
            "TAO": {"price": 448.50, "rsi": 56.23, "signal": "NEUTRAL"},
        }

    @pytest.fixture
    def sample_order_data(self) -> list[dict[str, Any]]:
        """Sample order data for testing."""
        return [
            {"symbol": "BTCUSDT", "side": "SELL", "type": "LIMIT", "price": "130000", "origQty": "0.004", "orderId": "46144762759"},
            {"symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT", "price": "115000", "origQty": "0.003", "orderId": "46240206918"},
            {"symbol": "ETHUSDT", "side": "BUY", "type": "LIMIT", "price": "3200", "origQty": "0.0625", "orderId": "32643081555"},
        ]

    @pytest.fixture
    def sample_balance_data(self) -> dict[str, Any]:
        """Sample balance data for testing."""
        return {"USDT": {"available": 1841.15, "balance": 3930.45}}

    @patch("src.core.ai_context_generator.ProtectionAnalyzer.analyze_portfolio_protection")
    def test_generate_comprehensive_context(
        self,
        mock_protection_analyzer: Mock,
        sample_portfolio_data: dict[str, Any],
        sample_market_data: dict[str, Any],
        sample_order_data: list[dict[str, Any]],
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test comprehensive context generation."""
        # Mock protection analysis result
        mock_protection_analyzer.return_value = {
            "portfolio_protection_score": 85.0,
            "summary": "Portfolio protection: EXCELLENT (85.0/100). All major positions well protected.",
            "individual_analysis": {
                "BTC": {
                    "score": 95,
                    "level": "EXCELLENT",
                    "recommendation": "SKIP_PROTECTION",
                    "analysis_summary": "BTC: Excellent protection - SKIP new protection orders.",
                }
            },
            "protection_recommendations": [],
        }

        result = AIContextGenerator.generate_comprehensive_context(
            sample_portfolio_data, sample_market_data, sample_order_data, sample_balance_data, "STRATEGIC_ANALYSIS"
        )

        # Verify all major sections are present
        assert "🛡️ PROTECTION ANALYSIS" in result
        assert "💰 EFFECTIVE BALANCE ANALYSIS" in result
        assert "📊 STRATEGIC CONTEXT" in result
        assert "💼 PORTFOLIO DATA" in result
        assert "📈 CURRENT MARKET DATA" in result
        assert "📋 ACTIVE ORDERS" in result
        assert "⚠️ AI GUIDANCE RULES" in result

        # Verify protection analysis integration
        assert "Portfolio Protection Score: 85.0/100" in result
        assert "EXCELLENT" in result
        assert "BTC: EXCELLENT (95/100)" in result

        # Verify balance analysis
        assert "• USDT: $1,841 immediately available" in result
        assert "($2,089 committed to orders)" in result
        assert "EFFECTIVE BALANCE ANALYSIS" in result

        # Verify strategic context
        assert "Strategy Phase: STRATEGIC_ANALYSIS" in result
        assert "DEFENSIVE" in result  # High USDT allocation

        # Verify AI guidance rules
        assert "PROTECTION ASSESSMENT" in result
        assert "BALANCE INTERPRETATION" in result

        # Verify protection analyzer was called correctly
        mock_protection_analyzer.assert_called_once()
        call_args = mock_protection_analyzer.call_args[0]
        assert "BTC" in call_args[0]  # Portfolio data
        assert "BTC" in call_args[1]  # Market data
        assert call_args[2] == sample_order_data  # Order data

    @patch("src.core.ai_context_generator.ProtectionAnalyzer.analyze_portfolio_protection")
    def test_generate_protection_analysis(
        self, mock_protection_analyzer: Mock, sample_portfolio_data: dict[str, Any], sample_market_data: dict[str, Any], sample_order_data: list[dict[str, Any]]
    ) -> None:
        """Test protection analysis generation."""
        mock_protection_analyzer.return_value = {
            "portfolio_protection_score": 75.5,
            "summary": "Portfolio protection: GOOD (75.5/100).",
            "individual_analysis": {
                "BTC": {"score": 90, "level": "EXCELLENT", "recommendation": "SKIP_PROTECTION", "analysis_summary": "BTC: Excellent protection"},
                "TAO": {
                    "score": 25,
                    "level": "POOR",
                    "recommendation": "IMPLEMENT_PROTECTION",
                    "analysis_summary": "TAO: Poor protection - immediate action needed",
                },
            },
            "protection_recommendations": ["TAO: Poor protection - immediate action needed"],
        }

        result = AIContextGenerator._generate_protection_analysis(sample_portfolio_data, sample_market_data, sample_order_data)

        assert "Portfolio Protection Score: 75.5/100" in result
        assert "Portfolio protection: GOOD (75.5/100)." in result
        assert "• BTC: EXCELLENT (90/100) - SKIP_PROTECTION" in result
        assert "• TAO: POOR (25/100) - IMPLEMENT_PROTECTION" in result

    @patch("src.core.ai_context_generator.ProtectionAnalyzer.analyze_portfolio_protection")
    def test_generate_protection_analysis_no_recommendations(
        self, mock_protection_analyzer: Mock, sample_portfolio_data: dict[str, Any], sample_market_data: dict[str, Any], sample_order_data: list[dict[str, Any]]
    ) -> None:
        """Test protection analysis with no immediate needs."""
        mock_protection_analyzer.return_value = {
            "portfolio_protection_score": 95.0,
            "summary": "Portfolio protection: EXCELLENT",
            "individual_analysis": {
                "BTC": {"score": 95, "level": "EXCELLENT", "recommendation": "SKIP_PROTECTION", "analysis_summary": "BTC: Excellent protection"}
            },
            "protection_recommendations": [],
        }

        result = AIContextGenerator._generate_protection_analysis(sample_portfolio_data, sample_market_data, sample_order_data)

        assert "Portfolio Protection Score: 95.0/100" in result
        assert "Portfolio protection: EXCELLENT" in result
        assert "• BTC: EXCELLENT (95/100) - SKIP_PROTECTION" in result

    def test_generate_balance_analysis_with_commitments(self, sample_balance_data: dict[str, Any], sample_order_data: list[dict[str, Any]]) -> None:
        """Test balance analysis generation with committed funds."""
        result = AIContextGenerator._generate_balance_analysis(sample_balance_data, sample_order_data)

        assert "• USDT: $1,841 immediately available" in result
        assert "($2,089 committed to orders)" in result

    def test_generate_balance_analysis_no_data(self) -> None:
        """Test balance analysis with no balance data."""
        result = AIContextGenerator._generate_balance_analysis(None, [])

        assert "Balance data not available" in result

    def test_generate_balance_analysis_no_commitments(self, sample_order_data: list[dict[str, Any]]) -> None:
        """Test balance analysis with no committed funds."""
        balance_data = {"USDT": {"available": 5000.0, "balance": 5000.0}}

        # Filter out buy orders to simulate no commitments
        sell_orders = [order for order in sample_order_data if order.get("side") != "BUY"]

        result = AIContextGenerator._generate_balance_analysis(balance_data, sell_orders)

        assert "• USDT: $5,000 immediately available" in result

    def test_generate_strategic_context_defensive_stance(self, sample_portfolio_data: dict[str, Any]) -> None:
        """Test strategic context for defensive portfolio stance."""
        result = AIContextGenerator._generate_strategic_context("STRATEGIC_ANALYSIS", sample_portfolio_data)

        assert "Strategy Phase: STRATEGIC_ANALYSIS" in result
        assert "Portfolio Stance: DEFENSIVE" in result
        assert "High USDT allocation" in result
        assert "Major Positions (>20%): BTC" in result

    def test_generate_strategic_context_balanced_stance(self) -> None:
        """Test strategic context for balanced portfolio stance."""
        balanced_portfolio = {"BTC": {"allocation_pct": 30.0}, "ETH": {"allocation_pct": 25.0}, "USDT": {"allocation_pct": 45.0}}

        result = AIContextGenerator._generate_strategic_context("MONITORING", balanced_portfolio)

        assert "Strategy Phase: MONITORING" in result
        assert "Portfolio Stance: BALANCED" in result
        assert "Moderate USDT allocation" in result

    def test_generate_strategic_context_aggressive_stance(self) -> None:
        """Test strategic context for aggressive portfolio stance."""
        aggressive_portfolio = {
            "BTC": {"allocation_pct": 40.0},
            "ETH": {"allocation_pct": 35.0},
            "SOL": {"allocation_pct": 15.0},
            "USDT": {"allocation_pct": 10.0},
        }

        result = AIContextGenerator._generate_strategic_context("ACCUMULATION", aggressive_portfolio)

        assert "Strategy Phase: ACCUMULATION" in result
        assert "Portfolio Stance: AGGRESSIVE" in result
        assert "Low USDT allocation" in result

    def test_format_portfolio_data(self, sample_portfolio_data: dict[str, Any]) -> None:
        """Test portfolio data formatting."""
        result = AIContextGenerator._format_portfolio_data(sample_portfolio_data)

        assert "Total Value: $6,691" in result
        assert "• BTC: $2,520 (37.4%) - 0.02126641 tokens" in result
        assert "• TAO: $240 (3.6%) - 0.5359021 tokens" in result
        assert "• USDT: $3,930 (58.3%)" in result

    def test_format_portfolio_data_empty(self) -> None:
        """Test portfolio data formatting with empty data."""
        result = AIContextGenerator._format_portfolio_data({})

        assert "Portfolio data not available" in result

    def test_format_market_data(self, sample_market_data: dict[str, Any]) -> None:
        """Test market data formatting."""
        result = AIContextGenerator._format_market_data(sample_market_data)

        assert "• BTC: $118,418 - RSI 45.4 (STRONG BUY)" in result
        assert "• ETH: $3,696 - RSI 45.03 (BUY)" in result
        assert "• TAO: $448.50 - RSI 56.23 (NEUTRAL)" in result

    def test_format_market_data_empty(self) -> None:
        """Test market data formatting with empty data."""
        result = AIContextGenerator._format_market_data({})

        assert "Market data not available" in result

    def test_format_order_data(self, sample_order_data: list[dict[str, Any]]) -> None:
        """Test order data formatting."""
        result = AIContextGenerator._format_order_data(sample_order_data)

        assert "ACTIVE ORDERS (3 total):" in result
        assert "BTCUSDT:" in result
        assert "SELL LIMIT: 0.004 @ $130000 (ID: 46144762759)" in result
        assert "BUY LIMIT: 0.003 @ $115000 (ID: 46240206918)" in result
        assert "ETHUSDT:" in result
        assert "BUY LIMIT: 0.0625 @ $3200 (ID: 32643081555)" in result

    def test_format_order_data_empty(self) -> None:
        """Test order data formatting with empty data."""
        result = AIContextGenerator._format_order_data([])

        assert "No active orders" in result

    def test_enhance_existing_context(self) -> None:
        """Test enhancement of existing context."""
        existing_context = "Original AI analysis content here."
        protection_analysis = "BTC: Excellent protection (95/100)"
        balance_analysis = "Available: $1,841 USDT"

        result = AIContextGenerator.enhance_existing_context(existing_context, protection_analysis, balance_analysis)

        assert "🛡️ PROTECTION ANALYSIS:" in result
        assert "BTC: Excellent protection (95/100)" in result
        assert "💰 BALANCE ANALYSIS:" in result
        assert "Available: $1,841 USDT" in result
        assert "Original AI analysis content here." in result
        assert "⚠️ AI GUIDANCE RULES:" in result

    def test_enhance_existing_context_no_enhancements(self) -> None:
        """Test enhancement with no additional analysis."""
        existing_context = "Original content"

        result = AIContextGenerator.enhance_existing_context(existing_context)

        assert result == existing_context

    def test_enhance_existing_context_partial_enhancements(self) -> None:
        """Test enhancement with only protection analysis."""
        existing_context = "Original content"
        protection_analysis = "BTC: Good protection"

        result = AIContextGenerator.enhance_existing_context(existing_context, protection_analysis=protection_analysis)

        assert "🛡️ PROTECTION ANALYSIS:" in result
        assert "BTC: Good protection" in result
        assert "💰 BALANCE ANALYSIS:" not in result
        assert "Original content" in result

    def test_enhance_existing_context_already_has_guidance(self) -> None:
        """Test enhancement when context already has guidance rules."""
        existing_context = """
        Original content here.

        ⚠️ AI GUIDANCE RULES:
        Existing rules here.
        """
        protection_analysis = "BTC: Good protection"

        result = AIContextGenerator.enhance_existing_context(existing_context, protection_analysis=protection_analysis)

        # Should not duplicate guidance rules
        guidance_count = result.count("⚠️ AI GUIDANCE RULES:")
        assert guidance_count == 1
        assert "BTC: Good protection" in result
        assert "Original content here." in result

    def test_format_order_data_missing_fields(self) -> None:
        """Test order data formatting with missing fields."""
        incomplete_orders = [
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "LIMIT",
                # Missing price, origQty, orderId
            },
            {
                # Missing symbol, will be 'UNKNOWN'
                "side": "SELL",
                "type": "LIMIT",
                "price": "2500",
                "origQty": "1.0",
                "orderId": "123456",
            },
        ]

        result = AIContextGenerator._format_order_data(incomplete_orders)

        assert "ACTIVE ORDERS (2 total):" in result
        assert "BTCUSDT:" in result
        assert "BUY LIMIT: N/A @ $N/A (ID: N/A)" in result
        assert "UNKNOWN:" in result
        assert "SELL LIMIT: 1.0 @ $2500 (ID: 123456)" in result

    def test_generate_balance_analysis_utilization_ranges(self) -> None:
        """Test balance analysis utilization calculation for different ranges."""
        order_data = [{"side": "BUY", "type": "LIMIT", "price": "1000", "origQty": "1.0"}]

        # High utilization (>70%)
        high_util_balance = {"USDT": {"available": 200.0, "balance": 1200.0}}
        result = AIContextGenerator._generate_balance_analysis(high_util_balance, order_data)
        assert "• USDT: $200 immediately available" in result
        assert "($1,000 committed to orders)" in result

        # Low utilization (<40%)
        low_util_balance = {"USDT": {"available": 4000.0, "balance": 5000.0}}
        result = AIContextGenerator._generate_balance_analysis(low_util_balance, order_data)
        assert "• USDT: $4,000 immediately available" in result
        assert "($1,000 committed to orders)" in result

    def test_protection_analysis_data_conversion(
        self, sample_portfolio_data: dict[str, Any], sample_market_data: dict[str, Any], sample_order_data: list[dict[str, Any]]
    ) -> None:
        """Test that data is properly converted for ProtectionAnalyzer."""
        with patch("src.core.ai_context_generator.ProtectionAnalyzer.analyze_portfolio_protection") as mock_analyzer:
            mock_analyzer.return_value = {
                "portfolio_protection_score": 85.0,
                "summary": "Good protection",
                "individual_analysis": {},
                "protection_recommendations": [],
            }

            AIContextGenerator._generate_protection_analysis(sample_portfolio_data, sample_market_data, sample_order_data)

            # Verify the data conversion
            call_args = mock_analyzer.call_args[0]
            portfolio_arg = call_args[0]
            market_arg = call_args[1]
            order_arg = call_args[2]

            # USDT should be filtered out of portfolio data
            assert "USDT" not in portfolio_arg
            assert "BTC" in portfolio_arg
            assert "TAO" in portfolio_arg

            # Market data should have proper structure
            assert "BTC" in market_arg
            assert "price" in market_arg["BTC"]

            # Order data should be passed through unchanged
            assert order_arg == sample_order_data
