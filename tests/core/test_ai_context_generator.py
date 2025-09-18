"""Tests for AI Context Generator Module."""

from unittest.mock import patch

import pytest

from src.core.ai_context_generator import AIContextGenerator


class TestAIContextGenerator:
    """Test suite for AIContextGenerator class."""

    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio data for testing."""
        return {
            "BTC": {"balance": 0.5, "value": 50000, "allocation_pct": 52.0},
            "ETH": {"balance": 10.0, "value": 30000, "allocation_pct": 31.0},
            "USDT": {"balance": 17000, "value": 17000, "allocation_pct": 17.0},
        }

    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for testing."""
        return {"BTC": {"price": 100000, "rsi": 58.5, "ema_10": 98000, "ema_21": 96000}, "ETH": {"price": 3000, "rsi": 45.2, "ema_10": 2950, "ema_21": 2900}}

    @pytest.fixture
    def sample_order_data(self):
        """Sample order data for testing."""
        return [
            {"symbol": "BTCUSDT", "side": "SELL", "type": "LIMIT", "price": "125000", "origQty": "0.1"},
            {"symbol": "ETHUSDT", "side": "BUY", "type": "LIMIT", "price": "2800", "origQty": "1.0"},
        ]

    @pytest.fixture
    def sample_balance_data(self):
        """Sample balance data for testing."""
        return {"available": {"BTC": 0.2, "ETH": 5.0, "USDT": 10000}, "committed": {"BTC": 0.3, "ETH": 5.0, "USDT": 7000}}

    def test_generate_comprehensive_context_complete(self, sample_portfolio_data, sample_market_data, sample_order_data, sample_balance_data):
        """Test comprehensive context generation with all components."""
        with (
            patch.object(AIContextGenerator, "_generate_protection_analysis") as mock_protection,
            patch.object(AIContextGenerator, "_generate_balance_analysis") as mock_balance,
            patch.object(AIContextGenerator, "_generate_strategic_context") as mock_strategic,
            patch.object(AIContextGenerator, "_format_portfolio_data") as mock_portfolio,
            patch.object(AIContextGenerator, "_format_market_data") as mock_market,
            patch.object(AIContextGenerator, "_format_order_data") as mock_orders,
            patch.object(AIContextGenerator, "_generate_concentration_risk_analysis") as mock_concentration,
        ):
            # Setup mock returns
            mock_protection.return_value = "Protection analysis content"
            mock_balance.return_value = "Balance analysis content"
            mock_strategic.return_value = "Strategic context content"
            mock_portfolio.return_value = "Portfolio data content"
            mock_market.return_value = "Market data content"
            mock_orders.return_value = "Order data content"
            mock_concentration.return_value = "Concentration risk content"

            result = AIContextGenerator.generate_comprehensive_context(
                sample_portfolio_data, sample_market_data, sample_order_data, sample_balance_data, "STRATEGIC_ANALYSIS"
            )

            # Verify all sections are present
            assert "🚨 PORTFOLIO CONCENTRATION" in result
            assert "🛡️ PROTECTION ANALYSIS (CRITICAL FOR RECOMMENDATIONS):" in result
            assert "💰 EFFECTIVE BALANCE ANALYSIS (PREVENT BALANCE CONFUSION):" in result
            assert "📊 MACRO INTELLIGENCE REQUIREMENTS:" in result
            assert "🎯 TECHNICAL ANALYSIS COVERAGE REQUIREMENTS:" in result

            # Verify enhanced requirements are specified
            assert "Fear & Greed Index" in result
            assert "institutional fund flows" in result
            assert "Bitcoin dominance" in result
            assert "ETH, LINK, DOT, ADA, AVAX, UNI, XRP" in result

            # Verify all mocks were called
            mock_protection.assert_called_once()
            mock_balance.assert_called_once()
            mock_strategic.assert_called_once()
            mock_concentration.assert_called_once()

    def test_generate_concentration_risk_analysis_with_violations(self):
        """Test concentration risk analysis with allocation violations."""
        portfolio_data = {
            "balances": {
                "BTC": {"free": 1.0, "value": 55000},  # 55% allocation
                "ETH": {"free": 10.0, "value": 30000},  # 30% allocation
                "USDT": {"free": 15000, "value": 15000},  # 15% allocation
            }
        }

        result = AIContextGenerator._generate_concentration_risk_analysis(portfolio_data)

        # Should highlight high concentration contextually
        assert "HIGH CONCENTRATION OBSERVATIONS:" in result or "Elevated concentration" in result
        assert "BTC: 55.0%" in result

    def test_generate_concentration_risk_analysis_within_guidelines(self):
        """Test concentration risk analysis with compliant allocations."""
        portfolio_data = {
            "balances": {
                "BTC": {"free": 0.3, "value": 30000},  # 30% allocation
                "ETH": {"free": 8.0, "value": 24000},  # 24% allocation
                "LINK": {"free": 100, "value": 16000},  # 16% allocation
                "USDT": {"free": 30000, "value": 30000},  # 30% allocation
            }
        }

        result = AIContextGenerator._generate_concentration_risk_analysis(portfolio_data)

        # Should show contextual compliance
        assert "CONCENTRATION CONTEXT" in result or "No unusual concentration" in result
        assert "🚨 CRITICAL CONCENTRATION VIOLATIONS:" not in result

    def test_generate_concentration_risk_analysis_approaching_limit(self):
        """Test concentration risk analysis with allocations approaching limit."""
        portfolio_data = {
            "balances": {
                "BTC": {"free": 0.8, "value": 35000},  # 35% allocation
                "ETH": {"free": 10.0, "value": 32000},  # 32% allocation
                "USDT": {"free": 33000, "value": 33000},  # 33% allocation
            }
        }

        result = AIContextGenerator._generate_concentration_risk_analysis(portfolio_data)

        # Should show approaching/elevated warnings contextually
        assert "35.0%" in result
        assert "32.0%" in result

    def test_generate_concentration_risk_analysis_edge_cases(self):
        """Test concentration risk analysis with edge cases."""
        # Test with empty balances
        empty_portfolio = {"balances": {}}
        result_empty = AIContextGenerator._generate_concentration_risk_analysis(empty_portfolio)
        assert "Manual Review" in result_empty

        # Test with zero values
        zero_portfolio = {"balances": {"BTC": {"free": 0, "value": 0}, "ETH": {"free": 0, "value": 0}}}
        result_zero = AIContextGenerator._generate_concentration_risk_analysis(zero_portfolio)
        assert "Manual Review Required" in result_zero

    def test_generate_concentration_risk_analysis_exception_handling(self):
        """Test concentration risk analysis exception handling."""
        # Test with completely invalid data structure
        invalid_data = {"not_balances": "invalid"}

        result = AIContextGenerator._generate_concentration_risk_analysis(invalid_data)

        # Should handle gracefully
        assert "Manual Review" in result

    def test_enhanced_ai_guidance_rules_comprehensive(self, sample_portfolio_data, sample_market_data, sample_order_data):
        """Test that enhanced AI guidance rules are comprehensive."""
        result = AIContextGenerator.generate_comprehensive_context(sample_portfolio_data, sample_market_data, sample_order_data, None, "STRATEGIC_ANALYSIS")

        # Verify key enhanced guidance rules are present (without hard caps)
        assert "TECHNICAL PRECISION" in result
        assert "MACRO FOUNDATION: Include Fear & Greed Index" in result
        assert "TECHNICAL PRECISION: Provide specific levels for minimum 7 major altcoins" in result
        assert "RISK MANAGEMENT" in result
