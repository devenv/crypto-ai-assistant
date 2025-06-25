"""Unit tests for OrderValidator class."""

from typing import Any, Dict, List
from unittest.mock import Mock

import pytest

from api.client import BinanceClient
from api.enums import OrderSide
from core.order_validator import OrderValidator


class TestOrderValidator:
    """Test cases for OrderValidator class."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient for testing."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def validator(self, mock_client: Mock) -> OrderValidator:
        """Create an OrderValidator instance with mock client."""
        return OrderValidator(mock_client)

    @pytest.fixture
    def sample_symbol_info(self) -> Dict[str, Any]:
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
    def sample_tickers(self) -> List[Dict[str, str]]:
        """Sample ticker data for testing."""
        return [{"symbol": "ETHUSDT", "price": "2500.00"}, {"symbol": "BTCUSDT", "price": "100000.00"}]

    def test_validate_oco_order_success(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: Dict[str, Any], sample_tickers: List[Dict[str, str]]
    ) -> None:
        """Test successful OCO order validation."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        # Valid OCO parameters
        is_valid, errors = validator.validate_oco_order(
            symbol="ETHUSDT",
            quantity=0.5000,  # Aligned with step size
            limit_price=2600.00,  # Above current price
            stop_price=2400.00,  # Below current price
        )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_oco_order_invalid_prices(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: Dict[str, Any], sample_tickers: List[Dict[str, str]]
    ) -> None:
        """Test OCO order validation with invalid price logic."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        # Invalid OCO parameters - limit below current, stop above current
        is_valid, errors = validator.validate_oco_order(
            symbol="ETHUSDT",
            quantity=0.5000,
            limit_price=2400.00,  # Below current price (invalid)
            stop_price=2600.00,  # Above current price (invalid)
        )

        assert is_valid is False
        assert len(errors) >= 2
        assert any("must be ABOVE current price" in error for error in errors)
        assert any("must be BELOW current price" in error for error in errors)

    def test_validate_limit_order_success(
        self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: Dict[str, Any], sample_tickers: List[Dict[str, str]]
    ) -> None:
        """Test successful limit order validation."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = sample_tickers

        # Valid limit order parameters
        is_valid, errors = validator.validate_limit_order(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            quantity=0.5000,  # Aligned with step size
            price=2400.00,  # Valid price
        )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_lot_size_below_minimum(self, validator: OrderValidator) -> None:
        """Test LOT_SIZE validation below minimum."""
        lot_filter = {"minQty": "0.001", "maxQty": "1000.0", "stepSize": "0.001"}

        errors = validator._validate_lot_size(0.0005, lot_filter)
        # Quantity 0.0005 will fail both minimum check AND step size alignment
        assert len(errors) == 2
        assert any("below minimum" in error for error in errors)
        assert any("not aligned with step size" in error for error in errors)

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

    def test_validate_percent_price_buy_side(self, validator: OrderValidator) -> None:
        """Test PERCENT_PRICE_BY_SIDE validation for BUY orders."""
        percent_filter = {"bidMultiplierUp": "2.0", "bidMultiplierDown": "0.5", "askMultiplierUp": "2.0", "askMultiplierDown": "0.5"}

        current_price = 1000.0

        # Price too high for BUY (above 2x current)
        errors = validator._validate_percent_price([2500.0], current_price, percent_filter, OrderSide.BUY)
        assert len(errors) == 1
        assert "above BUY limit" in errors[0]

        # Price too low for BUY (below 0.5x current)
        errors = validator._validate_percent_price([400.0], current_price, percent_filter, OrderSide.BUY)
        assert len(errors) == 1
        assert "below BUY limit" in errors[0]

    def test_validate_percent_price_sell_side(self, validator: OrderValidator) -> None:
        """Test PERCENT_PRICE_BY_SIDE validation for SELL orders."""
        percent_filter = {"bidMultiplierUp": "2.0", "bidMultiplierDown": "0.5", "askMultiplierUp": "2.0", "askMultiplierDown": "0.5"}

        current_price = 1000.0

        # Price too high for SELL (above 2x current)
        errors = validator._validate_percent_price([2500.0], current_price, percent_filter, OrderSide.SELL)
        assert len(errors) == 1
        assert "above SELL limit" in errors[0]

    def test_validate_notional_below_minimum(self, validator: OrderValidator) -> None:
        """Test NOTIONAL validation below minimum."""
        notional_filter = {"minNotional": "100.0", "maxNotional": "10000.0"}

        # Quantity * Price = 0.01 * 500 = 5.0 (below minimum 100.0)
        errors = validator._validate_notional(0.01, [500.0], notional_filter)
        assert len(errors) == 1
        assert "below minimum" in errors[0]

    def test_validate_notional_above_maximum(self, validator: OrderValidator) -> None:
        """Test NOTIONAL validation above maximum."""
        notional_filter = {"minNotional": "100.0", "maxNotional": "10000.0"}

        # Quantity * Price = 100 * 200 = 20000 (above maximum 10000.0)
        errors = validator._validate_notional(100.0, [200.0], notional_filter)
        assert len(errors) == 1
        assert "above maximum" in errors[0]

    def test_get_current_price_success(self, validator: OrderValidator, mock_client: Mock, sample_tickers: List[Dict[str, str]]) -> None:
        """Test successful current price retrieval."""
        mock_client.get_all_tickers.return_value = sample_tickers

        price = validator._get_current_price("ETHUSDT")
        assert price == 2500.0

    def test_get_current_price_not_found(self, validator: OrderValidator, mock_client: Mock, sample_tickers: List[Dict[str, str]]) -> None:
        """Test current price retrieval for non-existent symbol."""
        mock_client.get_all_tickers.return_value = sample_tickers

        price = validator._get_current_price("NONEXISTENT")
        assert price is None

    def test_get_current_price_api_error(self, validator: OrderValidator, mock_client: Mock) -> None:
        """Test current price retrieval with API error."""
        mock_client.get_all_tickers.side_effect = Exception("API Error")

        price = validator._get_current_price("ETHUSDT")
        assert price is None

    def test_validate_with_missing_symbol_info(self, validator: OrderValidator, mock_client: Mock) -> None:
        """Test validation when symbol info is missing."""
        mock_client.get_exchange_info.return_value = None

        is_valid, errors = validator.validate_oco_order("ETHUSDT", 1.0, 2600.0, 2400.0)
        assert is_valid is False
        assert len(errors) == 1
        assert "Could not retrieve symbol information" in errors[0]

    def test_validate_with_missing_current_price(self, validator: OrderValidator, mock_client: Mock, sample_symbol_info: Dict[str, Any]) -> None:
        """Test validation when current price is missing."""
        mock_client.get_exchange_info.return_value = sample_symbol_info
        mock_client.get_all_tickers.return_value = []

        is_valid, errors = validator.validate_oco_order("ETHUSDT", 1.0, 2600.0, 2400.0)
        assert is_valid is False
        assert len(errors) == 1
        assert "Could not retrieve symbol information" in errors[0]

    def test_validate_with_exception(self, validator: OrderValidator, mock_client: Mock) -> None:
        """Test validation when an unexpected exception occurs."""
        mock_client.get_exchange_info.side_effect = Exception("Unexpected error")

        is_valid, errors = validator.validate_oco_order("ETHUSDT", 1.0, 2600.0, 2400.0)
        assert is_valid is False
        assert len(errors) == 1
        assert "Validation error: Unexpected error" in errors[0]

    def test_validate_empty_filters(self, validator: OrderValidator) -> None:
        """Test validation methods with empty filter parameters."""
        # All validation methods should handle None filters gracefully
        assert validator._validate_lot_size(1.0, None) == []
        assert validator._validate_price_filter([100.0], None) == []
        assert validator._validate_percent_price([100.0], 100.0, None, OrderSide.BUY) == []
        assert validator._validate_notional(1.0, [100.0], None) == []
