"""
Focused tests for OrderValidator module.

Tests core order validation business logic, exchange constraints,
and critical safety features without redundant property-based testing.
"""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from src.api.client import BinanceClient
from src.api.enums import OrderSide, OrderType
from src.core.order_validator import OrderValidator


class TestOrderValidator:
    """Test cases for OrderValidator core functionality."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient for testing."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def validator(self, mock_client: Mock) -> OrderValidator:
        """Create an OrderValidator instance with mock client."""
        return OrderValidator(mock_client)

    @pytest.fixture
    def sample_symbol_info(self) -> dict[str, Any]:
        """Sample symbol info data for testing."""
        return {
            "symbols": [
                {
                    "symbol": "ETHUSDT",
                    "filters": [
                        {"filterType": "LOT_SIZE", "minQty": "0.00010000", "maxQty": "9000.00000000", "stepSize": "0.00010000"},
                        {"filterType": "PRICE_FILTER", "minPrice": "0.01000000", "maxPrice": "1000000.00000000", "tickSize": "0.01000000"},
                        {
                            "filterType": "PERCENT_PRICE_BY_SIDE",
                            "bidMultiplierUp": "5",
                            "bidMultiplierDown": "0.2",
                            "askMultiplierUp": "5",
                            "askMultiplierDown": "0.2",
                        },
                        {"filterType": "NOTIONAL", "minNotional": "10.00000000", "maxNotional": "9000000.00000000"},
                    ],
                }
            ]
        }

    @pytest.fixture
    def sample_tickers(self) -> list[dict[str, str]]:
        """Sample ticker data for testing."""
        return [{"symbol": "ETHUSDT", "price": "2500.00"}, {"symbol": "BTCUSDT", "price": "100000.00"}]

    def test_validate_order_placement_oco_success(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: dict[str, Any], sample_tickers: list[dict[str, str]]
    ) -> None:
        """Test successful OCO order validation through main entry point."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        with patch.object(validator, "_validate_available_balance", return_value=(True, [])):
            is_valid, errors = validator.validate_order_placement(
                symbol="ETHUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.OCO,
                quantity=0.5000,
                price=2600.00,  # Above current price
                stop_price=2400.00,  # Below current price
            )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_order_placement_oco_missing_prices(self, validator: OrderValidator, mock_client: Mock) -> None:
        """Test OCO order validation with missing required prices."""
        mock_client.get_all_tickers.return_value = [{"symbol": "ETHUSDT", "price": "2500.00"}]

        # Missing price
        is_valid, errors = validator.validate_order_placement(
            symbol="ETHUSDT",
            side=OrderSide.SELL,
            order_type=OrderType.OCO,
            quantity=0.5000,
            price=None,
            stop_price=2400.00,
        )

        assert is_valid is False
        assert any("Price and stop_price are required for OCO orders" in error for error in errors)

    def test_validate_order_placement_limit_success(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: dict[str, Any], sample_tickers: list[dict[str, str]]
    ) -> None:
        """Test successful limit order validation."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        with patch.object(validator, "_validate_available_balance", return_value=(True, [])):
            is_valid, errors = validator.validate_order_placement(
                symbol="ETHUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.5000,
                price=2400.00,  # Below current price (safe for BUY)
            )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_order_placement_immediate_fill_detection(self, validator: OrderValidator, mock_client: Mock) -> None:
        """Test immediate fill risk detection (CRITICAL safety feature)."""
        mock_client.get_all_tickers.return_value = [{"symbol": "ETHUSDT", "price": "2500.00"}]

        # BUY LIMIT above current price (would fill immediately)
        is_valid, errors = validator.validate_order_placement(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.5000,
            price=2600.00,  # Above current price - DANGEROUS
        )

        assert is_valid is False
        assert any("CRITICAL: BUY LIMIT" in error and "would fill IMMEDIATELY" in error for error in errors)

        # SELL LIMIT below current price (would fill immediately)
        is_valid, errors = validator.validate_order_placement(
            symbol="ETHUSDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=0.5000,
            price=2400.00,  # Below current price - DANGEROUS
        )

        assert is_valid is False
        assert any("CRITICAL: SELL LIMIT" in error and "would fill IMMEDIATELY" in error for error in errors)

    def test_available_balance_uses_exchange_assets_buy_ethbtc(self, validator: OrderValidator, mock_client: Mock) -> None:
        """BUY ETHBTC should check quote BTC, not USDT."""
        mock_client.get_all_tickers.return_value = [{"symbol": "ETHBTC", "price": "0.050000"}]
        mock_client.get_exchange_info.return_value = {"symbols": [{"symbol": "ETHBTC", "baseAsset": "ETH", "quoteAsset": "BTC", "filters": []}]}

        with patch("core.account.AccountService") as MockAcct:
            service = MockAcct.return_value
            # Suppose available BTC is insufficient
            service.get_effective_available_balance.return_value = (0.001, {"buy_orders": 0.0})

            is_valid, errors = validator.validate_order_placement(
                symbol="ETHBTC",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=1.0,
                price=0.1,  # requires 0.1 BTC
            )

            assert is_valid is False
            assert any("Insufficient effective BTC balance" in e for e in errors)

    def test_available_balance_uses_exchange_assets_sell_ethbtc(self, validator: OrderValidator, mock_client: Mock) -> None:
        """SELL ETHBTC should check base ETH balance."""
        mock_client.get_all_tickers.return_value = [{"symbol": "ETHBTC", "price": "0.050000"}]
        mock_client.get_exchange_info.return_value = {"symbols": [{"symbol": "ETHBTC", "baseAsset": "ETH", "quoteAsset": "BTC", "filters": []}]}

        with patch("core.account.AccountService") as MockAcct:
            service = MockAcct.return_value
            # Suppose available ETH is insufficient
            service.get_effective_available_balance.return_value = (0.2, {"sell_orders": 0.0, "oco_orders": 0.0})

            is_valid, errors = validator.validate_order_placement(
                symbol="ETHBTC",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.5,
                price=0.1,
            )

            assert is_valid is False
            assert any("Insufficient effective ETH balance" in e for e in errors)

    def test_validate_order_placement_no_current_price(self, validator: OrderValidator, mock_client: Mock) -> None:
        """Test validation when current price cannot be retrieved."""
        mock_client.get_all_tickers.return_value = []

        is_valid, errors = validator.validate_order_placement(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.5000,
            price=2400.00,
        )

        assert is_valid is False
        assert any("Could not retrieve current price for ETHUSDT" in error for error in errors)

    def test_validate_order_placement_api_exception(self, validator: OrderValidator, mock_client: Mock) -> None:
        """Test validation when API calls fail."""
        mock_client.get_all_tickers.side_effect = Exception("API Error")

        is_valid, errors = validator.validate_order_placement(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.5000,
            price=2400.00,
        )

        assert is_valid is False
        assert any("Could not retrieve current price" in error for error in errors)

    def test_validate_oco_order_success(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: dict[str, Any], sample_tickers: list[dict[str, str]]
    ) -> None:
        """Test successful OCO order validation."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        is_valid, errors = validator.validate_oco_order(
            symbol="ETHUSDT",
            quantity=0.5000,  # Aligned with step size
            limit_price=2600.00,  # Above current price
            stop_price=2400.00,  # Below current price
        )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_oco_order_invalid_price_logic(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: dict[str, Any], sample_tickers: list[dict[str, str]]
    ) -> None:
        """Test OCO order validation with invalid price logic."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        # Invalid price logic - limit below current, stop above current
        is_valid, errors = validator.validate_oco_order(
            symbol="ETHUSDT",
            quantity=0.5000,
            limit_price=2400.00,  # Below current price (invalid for SELL OCO)
            stop_price=2600.00,  # Above current price (invalid for SELL OCO)
        )

        assert is_valid is False
        assert len(errors) >= 2
        assert any("must be ABOVE current price" in error for error in errors)
        assert any("must be BELOW current price" in error for error in errors)

    def test_validate_oco_order_no_symbol_info(self, validator: OrderValidator, mock_client: Mock) -> None:
        """Test OCO validation when symbol information is unavailable."""
        mock_client.get_exchange_info.return_value = None
        mock_client.get_all_tickers.return_value = []

        is_valid, errors = validator.validate_oco_order("BTCUSDT", 1.0, 50000.0, 49000.0)

        assert not is_valid
        assert any("Could not retrieve symbol information" in error for error in errors)

    def test_validate_limit_order_success(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: dict[str, Any], sample_tickers: list[dict[str, str]]
    ) -> None:
        """Test successful limit order validation."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        is_valid, errors = validator.validate_limit_order(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            quantity=0.5000,  # Aligned with step size
            price=2400.00,  # Below current price (safe for BUY)
        )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_market_order_constraints_success(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: dict[str, Any], sample_tickers: list[dict[str, str]]
    ) -> None:
        """Test successful market order validation."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        is_valid, errors = validator._validate_market_order_constraints("ETHUSDT", 0.5000)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_market_order_constraints_invalid_quantity(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: dict[str, Any], sample_tickers: list[dict[str, str]]
    ) -> None:
        """Test market order validation with invalid quantity."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        is_valid, errors = validator._validate_market_order_constraints("ETHUSDT", 0.00005)  # Below minimum

        assert is_valid is False
        assert len(errors) >= 1
        assert any("below minimum" in error for error in errors)


class TestExchangeConstraints:
    """Test exchange constraint validation methods."""

    @pytest.fixture
    def validator(self) -> OrderValidator:
        """Create OrderValidator with mock client."""
        return OrderValidator(Mock(spec=BinanceClient))

    def test_validate_lot_size_below_minimum(self, validator: OrderValidator) -> None:
        """Test LOT_SIZE validation below minimum."""
        lot_filter = {"minQty": "0.001", "maxQty": "1000.0", "stepSize": "0.001"}

        errors = validator._validate_lot_size(0.0005, lot_filter)
        assert len(errors) >= 1
        assert any("below minimum" in error for error in errors)

    def test_validate_lot_size_above_maximum(self, validator: OrderValidator) -> None:
        """Test LOT_SIZE validation above maximum."""
        lot_filter = {"minQty": "0.001", "maxQty": "1000.0", "stepSize": "0.001"}

        errors = validator._validate_lot_size(1500.0, lot_filter)
        assert len(errors) == 1
        assert "above maximum" in errors[0]

    def test_validate_lot_size_step_alignment(self, validator: OrderValidator) -> None:
        """Test LOT_SIZE step size alignment."""
        lot_filter = {"minQty": "0.0", "maxQty": "1000.0", "stepSize": "0.001"}

        # This should fail alignment (0.0015 is not aligned with 0.001 step)
        errors = validator._validate_lot_size(0.0015, lot_filter)
        assert len(errors) == 1
        assert "not aligned with step size" in errors[0]

    def test_validate_lot_size_success(self, validator: OrderValidator) -> None:
        """Test successful LOT_SIZE validation."""
        lot_filter = {"minQty": "0.001", "maxQty": "1000.0", "stepSize": "0.001"}

        errors = validator._validate_lot_size(0.5, lot_filter)  # Valid quantity
        assert len(errors) == 0

    def test_validate_price_filter_below_minimum(self, validator: OrderValidator) -> None:
        """Test PRICE_FILTER validation below minimum."""
        price_filter = {"minPrice": "10.0", "maxPrice": "100000.0", "tickSize": "0.01"}

        errors = validator._validate_price_filter([5.0], price_filter)
        assert len(errors) == 1
        assert "below minimum" in errors[0]

    def test_validate_price_filter_above_maximum(self, validator: OrderValidator) -> None:
        """Test PRICE_FILTER validation above maximum."""
        price_filter = {"minPrice": "10.0", "maxPrice": "100000.0", "tickSize": "0.01"}

        errors = validator._validate_price_filter([150000.0], price_filter)
        assert len(errors) == 1
        assert "above maximum" in errors[0]

    def test_validate_price_filter_tick_alignment(self, validator: OrderValidator) -> None:
        """Test PRICE_FILTER tick size alignment."""
        price_filter = {"minPrice": "0.0", "maxPrice": "100000.0", "tickSize": "0.01"}

        errors = validator._validate_price_filter([100.005], price_filter)  # Not aligned with 0.01
        assert len(errors) == 1
        assert "not aligned with tick size" in errors[0]

    def test_validate_price_filter_success(self, validator: OrderValidator) -> None:
        """Test successful PRICE_FILTER validation."""
        price_filter = {"minPrice": "10.0", "maxPrice": "100000.0", "tickSize": "0.01"}

        errors = validator._validate_price_filter([2500.00], price_filter)  # Valid price
        assert len(errors) == 0

    def test_validate_notional_below_minimum(self, validator: OrderValidator) -> None:
        """Test NOTIONAL validation below minimum."""
        notional_filter = {"minNotional": "10.0", "maxNotional": "100000.0"}

        # Quantity 0.001 × Price 5000 = 5.0 USDT (below 10.0 minimum)
        errors = validator._validate_notional(0.001, [5000.0], notional_filter)
        assert len(errors) == 1
        assert "below minimum notional" in errors[0] or "below minimum" in errors[0]

    def test_validate_notional_success(self, validator: OrderValidator) -> None:
        """Test successful NOTIONAL validation."""
        notional_filter = {"minNotional": "10.0", "maxNotional": "100000.0"}

        # Quantity 0.01 × Price 2500 = 25.0 USDT (above 10.0 minimum)
        errors = validator._validate_notional(0.01, [2500.0], notional_filter)
        assert len(errors) == 0

    def test_validate_percent_price_buy_side(self, validator: OrderValidator) -> None:
        """Test PERCENT_PRICE_BY_SIDE validation for BUY orders."""
        percent_filter = {
            "bidMultiplierUp": "5",  # Max 5x current price
            "bidMultiplierDown": "0.2",  # Min 0.2x current price
            "askMultiplierUp": "5",
            "askMultiplierDown": "0.2",
        }

        # Price too high for BUY (above 5x current)
        errors = validator._validate_percent_price([15000.0], 2500.0, percent_filter, OrderSide.BUY)
        assert len(errors) == 1
        assert "above maximum allowed" in errors[0] or "above BUY limit" in errors[0]

        # Price too low for BUY (below 0.2x current)
        errors = validator._validate_percent_price([400.0], 2500.0, percent_filter, OrderSide.BUY)
        assert len(errors) == 1
        assert "below minimum allowed" in errors[0] or "below BUY limit" in errors[0]

        # Valid BUY price
        errors = validator._validate_percent_price([2400.0], 2500.0, percent_filter, OrderSide.BUY)
        assert len(errors) == 0

    def test_validate_empty_filters(self, validator: OrderValidator) -> None:
        """Test validation methods handle None filters gracefully."""
        # All validation methods should handle None filters without errors
        assert validator._validate_lot_size(1.0, None) == []
        assert validator._validate_price_filter([100.0], None) == []
        assert validator._validate_percent_price([100.0], 100.0, None, OrderSide.BUY) == []
        assert validator._validate_notional(1.0, [100.0], None) == []


class TestUtilityMethods:
    """Test utility and helper methods."""

    @pytest.fixture
    def validator(self) -> OrderValidator:
        """Create OrderValidator with mock client."""
        return OrderValidator(Mock(spec=BinanceClient))

    def test_get_current_price_success(self, validator: OrderValidator) -> None:
        """Test successful current price retrieval."""
        validator._client.get_all_tickers.return_value = [{"symbol": "ETHUSDT", "price": "2500.00"}, {"symbol": "BTCUSDT", "price": "100000.00"}]

        price = validator._get_current_price("ETHUSDT")
        assert price == 2500.0

    def test_get_current_price_not_found(self, validator: OrderValidator) -> None:
        """Test current price retrieval when symbol not found."""
        validator._client.get_all_tickers.return_value = [{"symbol": "BTCUSDT", "price": "100000.00"}]

        price = validator._get_current_price("ETHUSDT")
        assert price is None

    def test_get_current_price_api_error(self, validator: OrderValidator) -> None:
        """Test current price retrieval with API error."""
        validator._client.get_all_tickers.side_effect = Exception("API Error")

        price = validator._get_current_price("ETHUSDT")
        assert price is None

    def test_get_lot_size_info_display(self, validator: OrderValidator) -> None:
        """Test lot size information display formatting."""
        sample_symbol_info = {
            "symbols": [
                {
                    "symbol": "ETHUSDT",
                    "filters": [
                        {"filterType": "LOT_SIZE", "minQty": "0.00010000", "stepSize": "0.00010000"},
                        {"filterType": "PRICE_FILTER", "minPrice": "0.01000000", "maxPrice": "1000000.00000000", "tickSize": "0.01000000"},
                    ],
                }
            ]
        }

        validator._client.get_exchange_info.return_value = sample_symbol_info

        info = validator.get_lot_size_info_display("ETHUSDT")
        assert "ETHUSDT LOT_SIZE" in info
        assert "Step Size:" in info
        assert "Minimum:" in info
        assert "PRICE_FILTER Tick Size:" in info
        assert "Example Valid Prices:" in info

    def test_get_lot_size_info_display_no_data(self, validator: OrderValidator) -> None:
        """Test lot size info display when no data available."""
        validator._client.get_exchange_info.return_value = {"symbols": []}

        info = validator.get_lot_size_info_display("ETHUSDT")
        assert "No LOT_SIZE data available" in info or "No symbol information found" in info

    def test_available_balance_validation_mock(self, validator: OrderValidator) -> None:
        """Test balance validation with mocked AccountService."""
        with patch.object(validator, "_validate_available_balance") as mock_balance:
            mock_balance.return_value = (True, [])

            is_valid, errors = mock_balance("ETHUSDT", OrderSide.BUY, 0.5, 2500.0)

            assert is_valid is True
            assert len(errors) == 0
            mock_balance.assert_called_once_with("ETHUSDT", OrderSide.BUY, 0.5, 2500.0)
