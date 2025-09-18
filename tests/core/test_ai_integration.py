"""Tests for AI Integration Module."""

from unittest.mock import Mock, patch

import pytest

from src.core.ai_integration import (
    generate_comprehensive_ai_context,
    generate_effective_balance_analysis,
    generate_protection_coverage_analysis,
    generate_recent_activity_context,
    generate_risk_context,
    validate_and_enhance_analysis,
)


class TestAIIntegration:
    """Test suite for AI Integration functions."""

    @pytest.fixture
    def mock_account_service(self) -> Mock:
        """Mock account service with realistic data."""
        mock_service = Mock()
        mock_service.get_balances.return_value = [
            {"asset": "BTC", "balance": 0.02126641, "value_usdt": 2520.02},
            {"asset": "USDT", "balance": 3930.45, "value_usdt": 3930.45},
            {"asset": "TAO", "balance": 0.5359021, "value_usdt": 240.41},
        ]
        return mock_service

    @pytest.fixture
    def mock_order_service(self) -> Mock:
        """Mock order service with realistic orders."""
        mock_service = Mock()
        mock_service.get_all_orders.return_value = [
            {"symbol": "BTCUSDT", "side": "SELL", "type": "LIMIT", "price": "130000", "origQty": "0.004", "orderId": "46144762759"},
            {"symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT", "price": "115000", "origQty": "0.003", "orderId": "46240206918"},
            {"symbol": "ETHUSDT", "side": "BUY", "type": "LIMIT", "price": "3200", "origQty": "0.0625", "orderId": "32643081555"},
        ]
        return mock_service

    @patch("src.core.ai_integration.ProtectionAnalyzer.analyze_portfolio_protection")
    def test_generate_protection_coverage_analysis(self, mock_analyzer: Mock, mock_account_service: Mock, mock_order_service: Mock) -> None:
        """Test automated protection coverage analysis generation."""
        # Set up proper mock data
        portfolio_data = {"BTC": {"value": 1000}, "ETH": {"value": 500}}

        # Mock account service methods
        mock_account_service.get_account_info.return_value = {
            "BTC": {"balance": 1.0, "allocation_pct": 60.0, "value": 1000},
            "ETH": {"balance": 10.0, "allocation_pct": 40.0, "value": 500},
            "USDT": {"balance": 0, "allocation_pct": 0, "value": 0},
        }
        mock_account_service.get_current_price.return_value = "50000"

        # Mock order service
        mock_order_service.get_open_orders.return_value = [
            {"symbol": "BTCUSDT", "side": "SELL", "type": "LIMIT", "price": "130000", "origQty": "0.004"},
        ]

        # Mock protection analyzer result
        mock_analyzer.return_value = {
            "portfolio_protection_score": 85.0,
            "summary": "Portfolio protection: EXCELLENT (85.0/100)",
            "individual_analysis": {"BTC": {"level": "EXCELLENT", "score": 95}},
        }

        result = generate_protection_coverage_analysis(mock_account_service, mock_order_service, portfolio_data)

        # Verify automated analysis was called
        mock_analyzer.assert_called_once()

        # Verify output format
        assert "Portfolio Protection Score: 85.0/100" in result
        assert "EXCELLENT" in result
        assert "• BTC: EXCELLENT (Score: 95/100)" in result

        # Verify ProtectionAnalyzer received correct data format
        call_args = mock_analyzer.call_args[0]
        portfolio_arg = call_args[0]
        market_arg = call_args[1]
        orders_arg = call_args[2]

        # Portfolio should have non-USDT assets with balances
        assert "BTC" in portfolio_arg
        assert "ETH" in portfolio_arg
        assert "USDT" not in portfolio_arg  # USDT excluded from protection analysis

        # Market data should have price information for non-USDT assets
        assert "BTC" in market_arg
        assert "price" in market_arg["BTC"]
        assert "ETH" in market_arg
        assert "price" in market_arg["ETH"]
        # USDT is base currency, so no price data needed

        # Orders should be properly formatted
        assert len(orders_arg) == 1  # One order from mock setup
        assert orders_arg[0]["symbol"] == "BTCUSDT"

    @patch("src.core.ai_integration.ProtectionAnalyzer.analyze_portfolio_protection")
    def test_generate_protection_coverage_analysis_with_recommendations(
        self, mock_analyzer: Mock, mock_account_service: Mock, mock_order_service: Mock
    ) -> None:
        """Test protection analysis with urgent recommendations."""
        # Set up proper mock data
        mock_account_service.get_account_info.return_value = {"TAO": {"balance": 1.0, "value": 400.0}}
        mock_account_service.get_current_price.return_value = "400.0"
        mock_order_service.get_open_orders.return_value = []

        # Mock analyzer with protection needs
        mock_analyzer.return_value = {
            "portfolio_protection_score": 45.0,
            "summary": "Portfolio protection: POOR (45.0/100)",
            "individual_analysis": {
                "TAO": {
                    "score": 25,
                    "level": "POOR",
                    "recommendation": "IMPLEMENT_PROTECTION",
                    "analysis_summary": "TAO: Poor protection - immediate action needed",
                }
            },
            "protection_recommendations": ["TAO: Poor protection - immediate action needed"],
        }

        portfolio_data = {"TAO": {"value": 400}}
        result = generate_protection_coverage_analysis(mock_account_service, mock_order_service, portfolio_data)

        assert "Portfolio Protection Score: 45.0/100" in result
        assert "• TAO: POOR (Score: 25/100)" in result

    def test_generate_protection_coverage_analysis_no_portfolio_data(self, mock_order_service: Mock) -> None:
        """Test protection analysis with no portfolio data."""
        mock_account_service = Mock()
        mock_account_service.get_account_info.return_value = {"USDT": {"balance": 1000.0}}
        mock_order_service.get_open_orders.return_value = []

        # Empty portfolio data (no crypto positions)
        portfolio_data = {}
        result = generate_protection_coverage_analysis(mock_account_service, mock_order_service, portfolio_data)

        assert "No crypto positions found" in result or "Protection analysis not available" in result

    def test_generate_protection_coverage_analysis_order_service_error(self, mock_account_service: Mock) -> None:
        """Test protection analysis when order service fails."""
        mock_account_service.get_account_info.return_value = {"BTC": {"balance": 1.0, "value": 50000.0}}
        mock_order_service = Mock()
        mock_order_service.get_open_orders.side_effect = Exception("API Error")

        portfolio_data = {"BTC": {"value": 50000}}
        result = generate_protection_coverage_analysis(mock_account_service, mock_order_service, portfolio_data)

        # Should handle the error gracefully and continue with analysis
        assert "Portfolio Protection Score:" in result
        # Error should be logged but analysis should still complete

    def test_generate_effective_balance_analysis(self, mock_account_service: Mock, mock_order_service: Mock) -> None:
        """Test effective balance analysis generation."""
        # Set up proper mock data
        mock_account_service.get_account_info.return_value = {"USDT": {"balance": 5000.0}}
        mock_order_service.get_open_orders.return_value = [
            {"side": "BUY", "type": "LIMIT", "price": "2500", "origQty": "1.0"}  # 2500 USDT committed
        ]

        result = generate_effective_balance_analysis(mock_account_service, mock_order_service)

        assert "USDT: $2,500 immediately available" in result
        assert "($2,500 committed to orders)" in result

    def test_generate_effective_balance_analysis_high_utilization(self, mock_order_service: Mock) -> None:
        """Test balance analysis with high utilization."""
        # Mock high USDT balance with high commitments
        mock_account_service = Mock()
        mock_account_service.get_account_info.return_value = {"USDT": {"balance": 1000.0}}

        # Mock high commitment orders (80% utilization)
        mock_order_service.get_open_orders.return_value = [
            {
                "side": "BUY",
                "type": "LIMIT",
                "price": "2000",
                "origQty": "0.4",  # 800 USDT committed
            }
        ]

        result = generate_effective_balance_analysis(mock_account_service, mock_order_service)

        assert "USDT: $200 immediately available" in result
        assert "($800 committed to orders)" in result

    def test_generate_effective_balance_analysis_no_usdt(self, mock_order_service: Mock) -> None:
        """Test balance analysis with no USDT balance."""
        mock_account_service = Mock()
        mock_account_service.get_account_info.return_value = {
            "BTC": {"balance": 1.0}  # No USDT key
        }
        mock_order_service.get_open_orders.return_value = []

        result = generate_effective_balance_analysis(mock_account_service, mock_order_service)

        assert "USDT: $0 immediately available" in result

    def test_generate_risk_context(self) -> None:
        """Test risk context generation."""
        result = generate_risk_context()

        assert "🎯 RISK MANAGEMENT CONTEXT" in result
        assert "STRATEGY PHASES:" in result
        assert "RISK CONSIDERATIONS:" in result

    def test_generate_recent_activity_context(self, mock_account_service: Mock) -> None:
        """Test recent activity context generation."""
        result = generate_recent_activity_context(mock_account_service)

        assert "📈 RECENT ACTIVITY CONTEXT" in result
        assert "RECENT TRADING ANALYSIS:" in result
        assert "⚠️ AI INSTRUCTION:" in result
        assert "Consider recent activity when making new recommendations" in result

    def test_generate_comprehensive_ai_context(self, mock_account_service: Mock, mock_order_service: Mock) -> None:
        """Test comprehensive AI context generation."""
        with patch("src.core.ai_integration.ProtectionAnalyzer.analyze_portfolio_protection") as mock_analyzer:
            mock_analyzer.return_value = {
                "portfolio_protection_score": 85.0,
                "summary": "Portfolio protection: EXCELLENT",
                "individual_analysis": {},
                "protection_recommendations": [],
            }

            # Provide proper data structures instead of string literals
            portfolio_data = {"BTC": {"balance": 1.0, "value": 50000, "allocation_pct": 70.0}}
            market_data = {"BTC": {"price": 50000}}
            order_data = []

            # Mock the account service methods that will be called
            mock_account_service.get_account_info.return_value = {
                "BTC": {"balance": 1.0, "allocation_pct": 70.0, "value": 50000},
                "USDT": {"balance": 1000, "allocation_pct": 30.0, "value": 1000},
            }
            mock_account_service.get_current_price.return_value = "50000"
            mock_order_service.get_open_orders.return_value = []

            result = generate_comprehensive_ai_context(portfolio_data, market_data, order_data, mock_account_service, mock_order_service, "STRATEGIC_ANALYSIS")

            # Verify all components are present
            assert "protection_analysis" in result
            assert "balance_analysis" in result
            assert "risk_context" in result
            assert "recent_activity_context" in result

            # Verify content quality - check for actual function outputs
            assert "Portfolio Protection Score:" in result["protection_analysis"]
            assert "USDT:" in result["balance_analysis"]  # Fixed to match actual format
            assert "🎯 RISK MANAGEMENT CONTEXT" in result["risk_context"]
            assert "📈 RECENT ACTIVITY CONTEXT" in result["recent_activity_context"]

    def test_generate_protection_coverage_analysis_exception_handling(self, mock_order_service: Mock) -> None:
        """Test protection analysis error handling."""
        mock_account_service = Mock()
        mock_account_service.get_account_info.side_effect = Exception("API Error")
        mock_order_service.get_open_orders.return_value = []

        portfolio_data = {"BTC": {"value": 50000}}
        result = generate_protection_coverage_analysis(mock_account_service, mock_order_service, portfolio_data)

        assert "Protection analysis failed:" in result
        assert "API Error" in result

    def test_generate_effective_balance_analysis_exception_handling(self, mock_order_service: Mock) -> None:
        """Test balance analysis error handling."""
        mock_account_service = Mock()
        mock_account_service.get_account_info.side_effect = Exception("Connection Error")
        mock_order_service.get_open_orders.return_value = []

        result = generate_effective_balance_analysis(mock_account_service, mock_order_service)

        assert "Balance analysis failed:" in result
        assert "Connection Error" in result

    def test_order_data_conversion_edge_cases(self, mock_account_service: Mock) -> None:
        """Test order data conversion with edge cases."""
        mock_account_service.get_account_info.return_value = {"BTC": {"balance": 1.0, "value": 50000.0}}

        # Mock order service with problematic orders
        mock_order_service = Mock()
        mock_order_service.get_open_orders.return_value = [
            {
                # Missing fields
                "symbol": "BTCUSDT",
                "side": "SELL",
                # Missing type, price, origQty, orderId
            },
            {
                # None values
                "symbol": None,
                "side": None,
                "type": None,
                "price": None,
                "origQty": None,
                "orderId": None,
            },
        ]

        portfolio_data = {"BTC": {"value": 50000}}

        # Should not crash with problematic order data
        result = generate_protection_coverage_analysis(mock_account_service, mock_order_service, portfolio_data)

        # Should handle edge cases gracefully
        assert "Portfolio Protection Score:" in result or "Protection analysis failed:" in result


class TestAIQualityValidation:
    """Test suite for AI quality validation functionality."""

    def test_validate_and_enhance_analysis_excellent_quality(self) -> None:
        """Test validation of excellent quality analysis."""
        excellent_analysis = """
        **MACRO FOUNDATION**: Fear & Greed Index at 55/100 shows neutral sentiment.
        Institutional flows: $150M outflows from BTC ETFs, $75M inflows to ETH.
        Bitcoin dominance declined to 58.2% enabling altcoin season rotation.

        **PORTFOLIO RISK ASSESSMENT**: BTC allocation 52.3% indicates high concentration.
        Consider rebalancing via existing sell orders.

        **COMPREHENSIVE TECHNICAL ANALYSIS**:
        ETH: Support $3,480, resistance $3,650
        LINK: Falling wedge $15.40-$16.20, target $30
        DOT: Consolidation $3.55, breakout $3.80
        ADA: Oversold $0.68, support $0.66
        AVAX: Triangle apex $18, target $23
        UNI: Validation needed $9.50
        XRP: Mixed signals, support $2.76

        **RISK MANAGEMENT PRIORITIES**: Risk-first approach mandatory.
        Stop-losses below support. Maintain 30% USDT reserves.

        **STRATEGIC OPPORTUNITIES**: Conservative entries at support levels.
        ETH $3,480 entry, LINK $15.80, stops below key levels.
        """

        portfolio_data = {"balances": {"BTC": {"free": 0.5, "value": 52300}, "ETH": {"free": 10, "value": 30000}, "USDT": {"free": 20000, "value": 20000}}}

        quality_assessment, validation_results = validate_and_enhance_analysis(excellent_analysis, portfolio_data, min_quality_threshold=80)

        # Should meet high quality standards
        assert validation_results["meets_threshold"] is True
        assert validation_results["score"].total >= 80
        assert "EXCELLENT" in quality_assessment or "GOOD" in quality_assessment

        # Check individual components
        assert validation_results["breakdown"]["macro_intelligence"] >= 15
        assert validation_results["breakdown"]["concentration_risk"] >= 15
        assert validation_results["breakdown"]["technical_analysis"] >= 15
        assert validation_results["breakdown"]["risk_management"] >= 15

        # Should have minimal or no suggestions
        assert len(validation_results["suggestions"]) <= 2

    def test_validate_and_enhance_analysis_poor_quality(self) -> None:
        """Test validation of poor quality analysis."""
        poor_analysis = """
        Market looks okay. Bitcoin might go up or down.
        Consider some altcoins maybe. Check the charts.
        """

        quality_assessment, validation_results = validate_and_enhance_analysis(poor_analysis, None, min_quality_threshold=80)

        # Should not meet quality standards
        assert validation_results["meets_threshold"] is False
        assert validation_results["score"].total < 80
        assert "POOR" in quality_assessment or "NEEDS IMPROVEMENT" in quality_assessment

        # Should have many suggestions
        assert len(validation_results["suggestions"]) >= 3

        # Check that all categories scored low
        for category_score in validation_results["breakdown"].values():
            assert category_score <= 15

    def test_validate_and_enhance_analysis_partial_quality(self) -> None:
        """Test validation of analysis with partial quality."""
        partial_analysis = """
        **MACRO FOUNDATION**: Fear & Greed Index at 45/100.

        **TECHNICAL ANALYSIS**: ETH support at $3,400.
        LINK showing strength above $15.

        **RISK MANAGEMENT**: Consider position sizing.
        """

        quality_assessment, validation_results = validate_and_enhance_analysis(partial_analysis, None, min_quality_threshold=70)

        # Should partially meet standards (updated based on actual scoring logic)
        score = validation_results["score"].total
        assert 10 <= score <= 25  # Partial score range (basic elements only)

        # Should have some good elements but room for improvement
        assert validation_results["breakdown"]["macro_intelligence"] > 0
        assert validation_results["breakdown"]["technical_analysis"] > 0
        assert len(validation_results["suggestions"]) >= 1

    def test_validate_and_enhance_analysis_custom_threshold(self) -> None:
        """Test validation with custom quality threshold."""
        analysis = """
        Fear & Greed Index neutral. Some institutional activity.
        ETH and LINK analysis. Basic risk considerations.
        """

        # Test with low threshold (should pass) - analysis scores ~14 points
        quality_assessment_low, validation_results_low = validate_and_enhance_analysis(analysis, None, min_quality_threshold=10)

        # Test with high threshold (should fail)
        quality_assessment_high, validation_results_high = validate_and_enhance_analysis(analysis, None, min_quality_threshold=30)

        # Same analysis should have different threshold results
        assert validation_results_low["meets_threshold"] != validation_results_high["meets_threshold"]
        assert validation_results_low["score"].total == validation_results_high["score"].total

        # Higher threshold should have more suggestions
        assert len(validation_results_high["suggestions"]) >= len(validation_results_low["suggestions"])

    def test_validate_and_enhance_analysis_with_portfolio_context(self) -> None:
        """Test validation with portfolio context for concentration analysis."""
        analysis_with_concentration = """
        BTC allocation at 55% indicates high concentration.
        Overweight position suggests rebalancing attention.
        """

        portfolio_data = {"balances": {"BTC": {"free": 1.0, "value": 55000}, "USDT": {"free": 45000, "value": 45000}}}

        quality_assessment, validation_results = validate_and_enhance_analysis(analysis_with_concentration, portfolio_data, min_quality_threshold=60)

        # Should score well on concentration risk assessment
        assert validation_results["breakdown"]["concentration_risk"] >= 10

        # Verify portfolio context was used effectively
        assert validation_results["score"].concentration_risk > 0

    def test_validate_and_enhance_analysis_empty_input(self) -> None:
        """Test validation with empty analysis."""
        quality_assessment, validation_results = validate_and_enhance_analysis("", None, min_quality_threshold=50)

        # Should score zero across all categories
        assert validation_results["score"].total == 0
        assert validation_results["meets_threshold"] is False
        assert "POOR" in quality_assessment

        # Should have maximum suggestions
        assert len(validation_results["suggestions"]) == 5  # All categories need improvement
