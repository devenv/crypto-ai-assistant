"""Tests for AI Integration Module."""

from unittest.mock import Mock, patch

import pytest

from src.core.ai_integration import (
    generate_comprehensive_ai_context,
    generate_effective_balance_analysis,
    generate_protection_coverage_analysis,
    generate_recent_activity_context,
    generate_risk_context,
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
        assert "POSITION SIZING RULES:" in result
        assert "Maximum single asset allocation: 40%" in result
        assert "STRATEGY PHASES:" in result
        assert "RISK TOLERANCE GUIDELINES:" in result
        assert "⚠️ AI INSTRUCTION:" in result
        assert "Never recommend positions exceeding 40% allocation" in result

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
