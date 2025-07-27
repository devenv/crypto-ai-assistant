"""
Comprehensive tests for ValidationService module.

Tests cover all validation methods, error handling, and edge cases.
"""

from unittest.mock import Mock, patch

import pytest

from src.api.client import BinanceClient
from src.core.config import AppConfig
from src.core.validation_service import (
    AIRecommendation,
    ValidationResult,
    ValidationService,
)


class TestValidationService:
    """Test suite for ValidationService class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def mock_config(self):
        """Create a mock AppConfig."""
        return Mock(spec=AppConfig)

    @pytest.fixture
    def validation_service(self, mock_client, mock_config):
        """Create ValidationService with mocked dependencies."""
        return ValidationService(mock_client, mock_config)

    @pytest.fixture
    def sample_recommendations(self):
        """Create sample AI recommendations for testing."""
        return [
            AIRecommendation(
                symbol="BTCUSDT",
                action="BUY",
                quantity=0.01,
                price=50000.0,
                reasoning="Technical analysis suggests upward momentum",
                expected_current_price=49500.0,
            ),
            AIRecommendation(
                symbol="ETHUSDT",
                action="OCO",
                quantity=0.5,
                price=3500.0,
                stop_price=3200.0,
                reasoning="Take profit and set stop loss",
                expected_current_price=3400.0,
            ),
        ]

    def test_init(self, mock_client, mock_config):
        """Test ValidationService initialization."""
        service = ValidationService(mock_client, mock_config)
        assert service._client == mock_client
        assert service._account_service is not None
        assert service._indicator_service is not None
        assert service._order_service is not None

    def test_validate_ai_recommendations_success(self, validation_service, sample_recommendations):
        """Test successful validation of AI recommendations."""
        # Mock all the services and validation methods for a true success scenario
        with (
            patch.object(validation_service._account_service, "get_account_info") as mock_account,
            patch.object(validation_service._order_service, "get_open_orders") as mock_orders,
            patch.object(validation_service, "_validate_technical_indicators") as mock_tech,
            patch.object(validation_service, "_validate_portfolio_alignment") as mock_portfolio,
            patch.object(validation_service, "_validate_risk_management") as mock_risk,
            patch.object(validation_service, "_validate_execution_feasibility") as mock_exec,
            patch.object(validation_service, "_assess_data_freshness") as mock_freshness,
        ):
            # Setup successful responses
            mock_account.return_value = {"balances": [{"asset": "USDT", "free": "10000.0"}]}
            mock_orders.return_value = []

            # Mock all validation methods to return very high scores to test scoring system
            mock_tech.return_value = (90, [])  # Very high technical score
            mock_portfolio.return_value = (90, [])  # Very high portfolio score
            mock_risk.return_value = (90, [])  # Very high risk score
            mock_exec.return_value = (90, [])  # Very high execution score
            mock_freshness.return_value = (95, [])  # Good data freshness

            result = validation_service.validate_ai_recommendations(sample_recommendations)

            assert isinstance(result, ValidationResult)
            assert result.score >= 60  # Should be valid
            assert result.is_valid

    def test_validate_ai_recommendations_empty_list(self, validation_service):
        """Test validation with empty recommendations list."""
        # Mock all validation methods to return high scores for empty list (should be valid)
        with (
            patch.object(validation_service._account_service, "get_account_info") as mock_account,
            patch.object(validation_service._order_service, "get_open_orders") as mock_orders,
            patch.object(validation_service, "_validate_technical_indicators") as mock_tech,
            patch.object(validation_service, "_validate_portfolio_alignment") as mock_portfolio,
            patch.object(validation_service, "_validate_risk_management") as mock_risk,
            patch.object(validation_service, "_validate_execution_feasibility") as mock_exec,
            patch.object(validation_service, "_assess_data_freshness") as mock_freshness,
        ):
            # Setup successful responses
            mock_account.return_value = {"balances": [{"asset": "USDT", "free": "10000.0"}]}
            mock_orders.return_value = []

            # Mock all validation methods to return very high scores for empty list
            mock_tech.return_value = (90, [])  # Very high technical score
            mock_portfolio.return_value = (90, [])  # Very high portfolio score
            mock_risk.return_value = (90, [])  # Very high risk score
            mock_exec.return_value = (90, [])  # Very high execution score
            mock_freshness.return_value = (100, [])  # Perfect data freshness

            result = validation_service.validate_ai_recommendations([])

            assert isinstance(result, ValidationResult)
            assert result.score >= 60  # Empty list should be valid

    @patch("src.core.validation_service.AccountService")
    @patch("src.core.validation_service.IndicatorService")
    @patch("src.core.validation_service.OrderService")
    def test_validate_ai_recommendations_with_errors(self, mock_order_service, mock_indicator_service, mock_account_service, validation_service):
        """Test validation with recommendations that have errors."""
        problematic_rec = AIRecommendation(
            symbol="BTCUSDT", action="SELL", quantity=0.01, price=50000.0, reasoning="Sell in oversold conditions", expected_current_price=49500.0
        )

        # Mock RSI showing oversold conditions (should flag SELL as error)
        mock_indicator_service.return_value.get_indicators.return_value = {
            "BTC": {"rsi": 15.0, "price": 49800.0}  # Very oversold
        }

        mock_account_service.return_value.get_account_info.return_value = {"balances": [{"asset": "USDT", "free": "1000.0"}]}

        mock_order_service.return_value.get_open_orders.return_value = []

        with patch("core.order_validator.OrderValidator") as mock_validator:
            mock_validator.return_value.validate_order_placement.return_value = (True, [])

            result = validation_service.validate_ai_recommendations([problematic_rec])

            assert len(result.errors) > 0  # Should have errors
            assert result.score < 75  # Score should be impacted

    def test_assess_data_freshness_success(self, validation_service, sample_recommendations):
        """Test data freshness assessment with good data."""
        with patch.object(validation_service._indicator_service, "get_indicators") as mock_indicators:
            mock_indicators.return_value = {
                "BTC": {"price": 49600.0},  # Close to expected price
                "ETH": {"price": 3420.0},  # Close to expected price
            }

            score, issues = validation_service._assess_data_freshness(sample_recommendations)

            assert score >= 80  # Should be good score
            assert len(issues) <= 1  # Minimal issues

    def test_assess_data_freshness_stale_data(self, validation_service, sample_recommendations):
        """Test data freshness assessment with stale data."""
        with patch.object(validation_service._indicator_service, "get_indicators") as mock_indicators:
            mock_indicators.return_value = {
                "BTC": {"price": 40000.0},  # Way off from expected 49500
                "ETH": {"price": 2500.0},  # Way off from expected 3400
            }

            score, issues = validation_service._assess_data_freshness(sample_recommendations)

            assert score < 70  # Should be low score due to stale data
            assert len(issues) >= 2  # Should have issues for both symbols

    def test_assess_data_freshness_exception(self, validation_service, sample_recommendations):
        """Test data freshness assessment with exception."""
        with patch.object(validation_service._indicator_service, "get_indicators") as mock_indicators:
            mock_indicators.side_effect = Exception("API Error")

            score, issues = validation_service._assess_data_freshness(sample_recommendations)

            # Exception in get_indicators is caught silently, so score remains 100
            # Only outer try block failures set score to 50
            assert score == 100  # Exception in inner loop is caught silently
            assert len(issues) == 0  # No indicators retrieved, so no price comparisons

    def test_validate_technical_indicators_success(self, validation_service, sample_recommendations):
        """Test technical indicators validation with good conditions."""
        with patch.object(validation_service._indicator_service, "get_indicators") as mock_indicators:
            mock_indicators.return_value = {
                "BTC": {"rsi": 45.0},  # Good RSI for BUY
                "ETH": {"rsi": 65.0},  # Reasonable RSI
            }

            score, issues = validation_service._validate_technical_indicators(sample_recommendations)

            assert score >= 20  # Should be good score
            assert len(issues) == 0  # No issues

    def test_validate_technical_indicators_overbought_buy(self, validation_service):
        """Test technical indicators validation with overbought BUY."""
        overbought_rec = AIRecommendation(
            symbol="BTCUSDT",
            action="BUY",
            quantity=0.01,
            price=50000.0,
            reasoning="Buy despite overbought",
        )

        with patch.object(validation_service._indicator_service, "get_indicators") as mock_indicators:
            mock_indicators.return_value = {
                "BTC": {"rsi": 90.0}  # Extremely overbought
            }

            score, issues = validation_service._validate_technical_indicators([overbought_rec])

            assert score < 25  # Should be penalized
            assert any("extremely overbought" in issue for issue in issues)

    def test_validate_technical_indicators_oversold_sell(self, validation_service):
        """Test technical indicators validation with oversold SELL."""
        oversold_rec = AIRecommendation(
            symbol="BTCUSDT",
            action="SELL",
            quantity=0.01,
            price=50000.0,
            reasoning="Sell in oversold",
        )

        with patch.object(validation_service._indicator_service, "get_indicators") as mock_indicators:
            mock_indicators.return_value = {
                "BTC": {"rsi": 15.0}  # Oversold
            }

            score, issues = validation_service._validate_technical_indicators([oversold_rec])

            assert score < 25  # Should be heavily penalized
            assert any("ERROR" in issue for issue in issues)

    def test_validate_technical_indicators_no_data(self, validation_service, sample_recommendations):
        """Test technical indicators validation when no data available."""
        with patch.object(validation_service._indicator_service, "get_indicators") as mock_indicators:
            mock_indicators.return_value = {}  # No data

            score, issues = validation_service._validate_technical_indicators(sample_recommendations)

            assert score < 25  # Should be penalized
            assert any("No technical indicators available" in issue for issue in issues)

    def test_validate_technical_indicators_exception(self, validation_service, sample_recommendations):
        """Test technical indicators validation with exception."""
        with patch.object(validation_service._indicator_service, "get_indicators") as mock_indicators:
            mock_indicators.side_effect = Exception("Indicator error")

            score, issues = validation_service._validate_technical_indicators(sample_recommendations)

            assert score == 0  # Should be zero on exception
            assert any("Technical validation failed" in issue for issue in issues)

    def test_validate_risk_management_success(self, validation_service, sample_recommendations):
        """Test risk management validation with good practices."""
        with patch.object(validation_service._account_service, "get_account_info") as mock_account:
            mock_account.return_value = {"balances": [{"asset": "USDT", "free": "10000.0"}]}

            score, issues = validation_service._validate_risk_management(sample_recommendations)

            assert score >= 15  # Should have reasonable score
            assert len([issue for issue in issues if "ERROR" in issue]) == 0  # No critical errors

    def test_validate_risk_management_large_position_no_protection(self, validation_service):
        """Test risk management with large position without protection."""
        large_buy_rec = AIRecommendation(
            symbol="BTCUSDT",
            action="BUY",
            quantity=0.02,  # $1000 position at $50k
            price=50000.0,
            reasoning="Large buy without protection",
        )

        with patch.object(validation_service._account_service, "get_account_info") as mock_account:
            mock_account.return_value = {"balances": [{"asset": "USDT", "free": "10000.0"}]}

            score, issues = validation_service._validate_risk_management([large_buy_rec])

            assert score < 20  # Should be penalized
            assert any("without protective OCO orders" in issue for issue in issues)

    def test_validate_risk_management_excessive_deployment(self, validation_service):
        """Test risk management with excessive cash deployment."""
        large_rec = AIRecommendation(
            symbol="BTCUSDT",
            action="BUY",
            quantity=0.2,  # $10k position
            price=50000.0,
            reasoning="Deploy most of cash",
        )

        with patch.object(validation_service._account_service, "get_account_info") as mock_account:
            mock_account.return_value = {
                "balances": [{"asset": "USDT", "free": "10000.0"}]  # Small balance
            }

            score, issues = validation_service._validate_risk_management([large_rec])

            assert score < 20  # Should be heavily penalized
            assert any(">90% of available cash" in issue or ">50% of available cash" in issue for issue in issues)

    def test_validate_risk_management_stop_loss_validation(self, validation_service):
        """Test risk management stop loss percentage validation."""
        wide_stop_rec = AIRecommendation(
            symbol="BTCUSDT",
            action="OCO",
            quantity=0.01,
            price=50000.0,
            stop_price=40000.0,  # 20% stop loss - too wide
            reasoning="Wide stop loss",
        )

        tight_stop_rec = AIRecommendation(
            symbol="ETHUSDT",
            action="OCO",
            quantity=0.5,
            price=3000.0,
            stop_price=2995.0,  # 0.17% stop loss - too tight
            reasoning="Tight stop loss",
        )

        with patch.object(validation_service._account_service, "get_account_info") as mock_account:
            mock_account.return_value = {"balances": [{"asset": "USDT", "free": "10000.0"}]}

            score, issues = validation_service._validate_risk_management([wide_stop_rec, tight_stop_rec])

            assert score < 20  # Should be penalized
            assert any("too wide" in issue for issue in issues)
            assert any("too tight" in issue for issue in issues)

    def test_validate_risk_management_exception(self, validation_service, sample_recommendations):
        """Test risk management validation with exception."""
        with patch.object(validation_service._account_service, "get_account_info") as mock_account:
            mock_account.side_effect = Exception("Account error")

            score, issues = validation_service._validate_risk_management(sample_recommendations)

            assert score == 0  # Should be zero on exception
            assert any("Risk management validation failed" in issue for issue in issues)

    def test_validate_execution_feasibility_success(self, validation_service, sample_recommendations):
        """Test execution feasibility validation with valid orders."""
        with patch("core.order_validator.OrderValidator") as mock_validator:
            mock_validator.return_value.validate_order_placement.return_value = (True, [])

            score, issues = validation_service._validate_execution_feasibility(sample_recommendations)

            assert score >= 10  # Should have reasonable score
            assert len([issue for issue in issues if "ERROR" in issue]) == 0  # No critical errors

    def test_validate_execution_feasibility_validation_errors(self, validation_service, sample_recommendations):
        """Test execution feasibility with validation errors."""
        with patch("core.order_validator.OrderValidator") as mock_validator:
            mock_validator.return_value.validate_order_placement.return_value = (False, ["CRITICAL: Insufficient balance", "WARNING: Price precision issue"])

            score, issues = validation_service._validate_execution_feasibility(sample_recommendations)

            assert score < 15  # Should be penalized
            assert any("ERROR" in issue for issue in issues)  # Critical issues as errors
            assert any("WARNING" in issue for issue in issues)  # Warnings

    def test_validate_execution_feasibility_exception(self, validation_service, sample_recommendations):
        """Test execution feasibility validation with exception."""
        with patch("core.order_validator.OrderValidator") as mock_validator:
            mock_validator.side_effect = Exception("Validator error")

            score, issues = validation_service._validate_execution_feasibility(sample_recommendations)

            assert score == 0  # Should be zero on exception
            assert any("Execution feasibility validation failed" in issue for issue in issues)

    def test_validate_portfolio_alignment_success(self, validation_service, sample_recommendations):
        """Test portfolio alignment validation with good diversification."""
        with patch.object(validation_service._order_service, "get_open_orders") as mock_orders:
            mock_orders.return_value = []  # No existing orders

            score, issues = validation_service._validate_portfolio_alignment(sample_recommendations)

            assert score >= 20  # Should have good score
            assert len([issue for issue in issues if "ERROR" in issue]) == 0  # No critical errors

    def test_validate_portfolio_alignment_concentration_risk(self, validation_service):
        """Test portfolio alignment with concentration risk."""
        concentrated_recs = [
            AIRecommendation(symbol="BTCUSDT", action="BUY", quantity=0.01, price=50000.0),
            AIRecommendation(symbol="BTCUSDT", action="BUY", quantity=0.01, price=49000.0),
            AIRecommendation(symbol="BTCUSDT", action="OCO", quantity=0.02, price=51000.0, stop_price=48000.0),
        ]

        with patch.object(validation_service._order_service, "get_open_orders") as mock_orders:
            mock_orders.return_value = []

            score, issues = validation_service._validate_portfolio_alignment(concentrated_recs)

            assert score < 25  # Should be penalized
            assert any("Heavy concentration in single asset" in issue for issue in issues)

    def test_validate_portfolio_alignment_high_allocation(self, validation_service):
        """Test portfolio alignment with high single allocation."""
        high_allocation_recs = [
            AIRecommendation(symbol="BTCUSDT", action="BUY", quantity=0.01, price=50000.0),  # $500
            AIRecommendation(symbol="ETHUSDT", action="BUY", quantity=0.02, price=3000.0),  # $60 - 10.7%
        ]

        with patch.object(validation_service._order_service, "get_open_orders") as mock_orders:
            mock_orders.return_value = []

            score, issues = validation_service._validate_portfolio_alignment(high_allocation_recs)

            assert score <= 25  # Should check allocation
            # BTC is ~89% allocation, should trigger warning
            assert any("high concentration" in issue for issue in issues if "89" in issue or "90" in issue)

    def test_validate_portfolio_alignment_exception(self, validation_service, sample_recommendations):
        """Test portfolio alignment validation with exception."""
        with patch.object(validation_service._order_service, "get_open_orders") as mock_orders:
            mock_orders.side_effect = Exception("Orders error")

            score, issues = validation_service._validate_portfolio_alignment(sample_recommendations)

            assert score == 0  # Should be zero on exception
            assert any("Portfolio alignment validation failed" in issue for issue in issues)

    def test_generate_validation_report_excellent(self, validation_service):
        """Test report generation for excellent validation result."""
        result = ValidationResult(
            is_valid=True,
            score=95,
            technical_score=85,
            category_scores={"technical_validity": 25, "risk_management": 25, "execution_feasibility": 23, "portfolio_alignment": 22},
            errors=[],
            warnings=[],
            technical_issues=["INFO: Minor price variance"],
            recommendations=["✅ Excellent - No significant actionable issues found"],
        )

        report = validation_service.generate_validation_report(result)

        assert "EXCELLENT" in report
        assert "95/100" in report
        assert "Technical Data Quality: 85/100" in report
        assert "CRITICAL ERRORS" not in report  # No errors section
        assert "TECHNICAL LIMITATIONS" in report
        assert "✅ FOCUS: Recommendations are actionable" in report

    def test_generate_validation_report_poor(self, validation_service):
        """Test report generation for poor validation result."""
        result = ValidationResult(
            is_valid=False,
            score=45,
            technical_score=30,
            category_scores={"technical_validity": 10, "risk_management": 15, "execution_feasibility": 10, "portfolio_alignment": 10},
            errors=["ERROR: Critical issue 1", "ERROR: Critical issue 2"],
            warnings=["WARNING: Consider this"],
            technical_issues=["INFO: Stale data"],
            recommendations=["🚨 Poor - Critical actionable issues found", "Must resolve all errors before proceeding"],
        )

        report = validation_service.generate_validation_report(result)

        assert "POOR" in report
        assert "45/100" in report
        assert "CRITICAL ERRORS" in report
        assert "ERROR: Critical issue 1" in report
        assert "ERROR: Critical issue 2" in report
        assert "WARNING: Consider this" in report
        assert "🔴 FOCUS: Critical actionable issues must be resolved first" in report

    def test_ai_recommendation_dataclass(self):
        """Test AIRecommendation dataclass functionality."""
        rec = AIRecommendation(
            symbol="BTCUSDT", action="BUY", quantity=0.01, price=50000.0, stop_price=None, reasoning="Test recommendation", expected_current_price=49500.0
        )

        assert rec.symbol == "BTCUSDT"
        assert rec.action == "BUY"
        assert rec.quantity == 0.01
        assert rec.price == 50000.0
        assert rec.stop_price is None
        assert rec.reasoning == "Test recommendation"
        assert rec.expected_current_price == 49500.0

    def test_validation_result_dataclass(self):
        """Test ValidationResult dataclass functionality."""
        result = ValidationResult(
            is_valid=True,
            score=85,
            technical_score=75,
            category_scores={"test": 25},
            errors=["error1"],
            warnings=["warning1"],
            technical_issues=["issue1"],
            recommendations=["rec1"],
        )

        assert result.is_valid is True
        assert result.score == 85
        assert result.technical_score == 75
        assert result.category_scores == {"test": 25}
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]
        assert result.technical_issues == ["issue1"]
        assert result.recommendations == ["rec1"]
