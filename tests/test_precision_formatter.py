"""Unit tests for PrecisionFormatter class."""

from typing import Any, Dict
from unittest.mock import Mock

import pytest

from api.client import BinanceClient
from core.precision_formatter import PrecisionFormatter


class TestPrecisionFormatter:
    """Test cases for PrecisionFormatter class."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient for testing."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def formatter(self, mock_client: Mock) -> PrecisionFormatter:
        """Create a PrecisionFormatter instance with mock client."""
        return PrecisionFormatter(mock_client)

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
                    ],
                }
            ]
        }

    def test_format_quantity_success(self, formatter: PrecisionFormatter, mock_client: Mock, sample_symbol_info: Dict[str, Any]) -> None:
        """Test successful quantity formatting."""
        mock_client.get_exchange_info.return_value = sample_symbol_info

        # Test quantity formatting with step size alignment
        formatted = formatter.format_quantity("ETHUSDT", 0.62938)

        # Should be rounded down to align with 0.0001 step size
        assert formatted == 0.6293

    def test_format_quantity_no_step_size(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test quantity formatting when no step size is available."""
        # Mock empty symbol info
        mock_client.get_exchange_info.return_value = {"symbols": [{"filters": []}]}

        # Should return original quantity if no step size
        formatted = formatter.format_quantity("ETHUSDT", 0.62938)
        assert formatted == 0.62938

    def test_format_price_success(self, formatter: PrecisionFormatter, mock_client: Mock, sample_symbol_info: Dict[str, Any]) -> None:
        """Test successful price formatting."""
        mock_client.get_exchange_info.return_value = sample_symbol_info

        # Test price formatting with tick size alignment
        formatted = formatter.format_price("ETHUSDT", 2680.5555)

        # Should be rounded to align with 0.01 tick size
        assert formatted == 2680.56

    def test_format_price_no_tick_size(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test price formatting when no tick size is available."""
        # Mock empty symbol info
        mock_client.get_exchange_info.return_value = {"symbols": [{"filters": []}]}

        # Should return original price if no tick size
        formatted = formatter.format_price("ETHUSDT", 2680.5555)
        assert formatted == 2680.5555

    def test_get_symbol_info_caching(self, formatter: PrecisionFormatter, mock_client: Mock, sample_symbol_info: Dict[str, Any]) -> None:
        """Test symbol info caching mechanism."""
        mock_client.get_exchange_info.return_value = sample_symbol_info

        # First call should fetch from API
        result1 = formatter._get_symbol_info("ETHUSDT")

        # Second call should use cache (no additional API call)
        result2 = formatter._get_symbol_info("ETHUSDT")

        # Should only call API once
        assert mock_client.get_exchange_info.call_count == 1
        assert result1 == result2

    def test_get_symbol_info_api_failure(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test symbol info retrieval with API failure."""
        mock_client.get_exchange_info.side_effect = Exception("API Error")

        # Should return empty dict on API failure
        result = formatter._get_symbol_info("ETHUSDT")
        assert result == {}

    def test_get_symbol_info_empty_response(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test symbol info retrieval with empty API response."""
        mock_client.get_exchange_info.return_value = None

        # Should return empty dict for None response
        result = formatter._get_symbol_info("ETHUSDT")
        assert result == {}

    def test_get_symbol_info_malformed_response(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test symbol info retrieval with malformed API response."""
        mock_client.get_exchange_info.return_value = {"symbols": []}

        # Should return empty dict for empty symbols list
        result = formatter._get_symbol_info("ETHUSDT")
        assert result == {}

    def test_get_lot_size_step_success(self, formatter: PrecisionFormatter, mock_client: Mock, sample_symbol_info: Dict[str, Any]) -> None:
        """Test successful LOT_SIZE step size retrieval."""
        mock_client.get_exchange_info.return_value = sample_symbol_info

        step_size = formatter._get_lot_size_step("ETHUSDT")
        assert step_size == 0.0001

    def test_get_lot_size_step_missing_filter(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test LOT_SIZE step size retrieval when filter is missing."""
        mock_client.get_exchange_info.return_value = {"symbols": [{"filters": []}]}

        step_size = formatter._get_lot_size_step("ETHUSDT")
        assert step_size is None

    def test_get_lot_size_step_missing_field(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test LOT_SIZE step size retrieval when stepSize field is missing."""
        mock_client.get_exchange_info.return_value = {
            "symbols": [
                {
                    "filters": [
                        {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.001",
                            # stepSize missing
                        }
                    ]
                }
            ]
        }

        step_size = formatter._get_lot_size_step("ETHUSDT")
        assert step_size is None

    def test_get_lot_size_min_success(self, formatter: PrecisionFormatter, mock_client: Mock, sample_symbol_info: Dict[str, Any]) -> None:
        """Test successful LOT_SIZE min quantity retrieval."""
        mock_client.get_exchange_info.return_value = sample_symbol_info

        min_qty = formatter._get_lot_size_min("ETHUSDT")
        assert min_qty == 0.0001

    def test_get_lot_size_min_missing_filter(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test LOT_SIZE min quantity retrieval when filter is missing."""
        mock_client.get_exchange_info.return_value = {"symbols": [{"filters": []}]}

        min_qty = formatter._get_lot_size_min("ETHUSDT")
        assert min_qty == 0.0

    def test_get_lot_size_min_missing_field(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test LOT_SIZE min quantity retrieval when minQty field is missing."""
        mock_client.get_exchange_info.return_value = {
            "symbols": [
                {
                    "filters": [
                        {
                            "filterType": "LOT_SIZE",
                            "stepSize": "0.001",
                            # minQty missing
                        }
                    ]
                }
            ]
        }

        min_qty = formatter._get_lot_size_min("ETHUSDT")
        assert min_qty == 0.0

    def test_get_price_tick_size_success(self, formatter: PrecisionFormatter, mock_client: Mock, sample_symbol_info: Dict[str, Any]) -> None:
        """Test successful PRICE_FILTER tick size retrieval."""
        mock_client.get_exchange_info.return_value = sample_symbol_info

        tick_size = formatter._get_price_tick_size("ETHUSDT")
        assert tick_size == 0.01

    def test_get_price_tick_size_missing_filter(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test PRICE_FILTER tick size retrieval when filter is missing."""
        mock_client.get_exchange_info.return_value = {"symbols": [{"filters": []}]}

        tick_size = formatter._get_price_tick_size("ETHUSDT")
        assert tick_size is None

    def test_get_price_tick_size_missing_field(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test PRICE_FILTER tick size retrieval when tickSize field is missing."""
        mock_client.get_exchange_info.return_value = {
            "symbols": [
                {
                    "filters": [
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.01",
                            # tickSize missing
                        }
                    ]
                }
            ]
        }

        tick_size = formatter._get_price_tick_size("ETHUSDT")
        assert tick_size is None

    def test_format_oco_params(self, formatter: PrecisionFormatter, mock_client: Mock, sample_symbol_info: Dict[str, Any]) -> None:
        """Test OCO parameters formatting."""
        mock_client.get_exchange_info.return_value = sample_symbol_info

        qty, limit, stop = formatter.format_oco_params("ETHUSDT", 0.62938, 2680.5555, 2450.7777)

        assert qty == 0.6293  # Aligned to step size
        assert limit == 2680.56  # Aligned to tick size
        assert stop == 2450.78  # Aligned to tick size

    def test_format_limit_params(self, formatter: PrecisionFormatter, mock_client: Mock, sample_symbol_info: Dict[str, Any]) -> None:
        """Test limit order parameters formatting."""
        mock_client.get_exchange_info.return_value = sample_symbol_info

        qty, price = formatter.format_limit_params("ETHUSDT", 0.62938, 2680.5555)

        assert qty == 0.6293  # Aligned to step size
        assert price == 2680.56  # Aligned to tick size

    def test_decimal_precision_edge_cases(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test decimal precision handling for edge cases."""
        # Create symbol info with very small step/tick sizes
        symbol_info = {
            "symbols": [
                {
                    "filters": [
                        {"filterType": "LOT_SIZE", "minQty": "0.00000001", "stepSize": "0.00000001"},
                        {"filterType": "PRICE_FILTER", "tickSize": "0.00000001"},
                    ]
                }
            ]
        }
        mock_client.get_exchange_info.return_value = symbol_info

        # Test very small quantities and prices
        formatted_qty = formatter.format_quantity("TESTUSDT", 0.000000015)
        formatted_price = formatter.format_price("TESTUSDT", 0.000000015)

        # Should handle precision correctly
        assert isinstance(formatted_qty, float)
        assert isinstance(formatted_price, float)

    def test_large_number_handling(self, formatter: PrecisionFormatter, mock_client: Mock) -> None:
        """Test handling of large numbers."""
        symbol_info = {
            "symbols": [{"filters": [{"filterType": "LOT_SIZE", "minQty": "1.0", "stepSize": "1.0"}, {"filterType": "PRICE_FILTER", "tickSize": "1.0"}]}]
        }
        mock_client.get_exchange_info.return_value = symbol_info

        # Test large quantities and prices
        formatted_qty = formatter.format_quantity("TESTUSDT", 1000000.7)
        formatted_price = formatter.format_price("TESTUSDT", 1000000.7)

        # Should handle large numbers correctly
        assert formatted_qty == 1000000.0
        assert formatted_price == 1000001.0  # Rounded up to nearest tick
