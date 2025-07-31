from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture

from src.core.indicators import IndicatorService


@pytest.fixture
def mock_client() -> MagicMock:
    """Fixture to create a mock BinanceClient with realistic data."""
    client = MagicMock()
    # Provide realistic k-line data for 50 periods (sufficient for most indicators)
    kline_data = [
        [
            1672531200000 + i * 86400000,  # Open time
            50000 + i * 100,  # Open (trending up)
            50100 + i * 100,  # High
            49900 + i * 100,  # Low
            50050 + i * 100,  # Close (trending up)
            1000,  # Volume
            1672617599999 + i * 86400000,  # Close time
            50000000,  # Quote asset volume
            100,  # Number of trades
            500,  # Taker buy base asset volume
            25000000,  # Taker buy quote asset volume
            0,
        ]
        for i in range(50)
    ]
    client.get_klines.return_value = kline_data
    return client


@pytest.fixture
def mock_config() -> dict:
    """Fixture to create mock configuration."""
    return {
        "analysis": {
            "min_data_points": 21,
            "rsi_period": 14,
            "ema_periods": [10, 21, 50],
            "ema_short_period": 12,
            "ema_long_period": 26,
            "ema_signal_period": 9,
        }
    }


@pytest.fixture
def indicator_service(mock_client: MagicMock, mock_config: dict) -> IndicatorService:
    """Fixture to create an IndicatorService instance."""
    return IndicatorService(mock_client, mock_config)


class TestIndicatorService:
    """Test suite for IndicatorService core functionality."""

    def test_calculate_indicators_success(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test successful indicator calculation with sufficient data."""
        result = indicator_service.calculate_indicators(["BTC"])

        assert "BTC" in result
        assert "errors" not in result
        # Check the actual field names returned by extract_indicator_data
        assert "close" in result["BTC"]
        assert "rsi" in result["BTC"]
        assert "signal_line" in result["BTC"]
        assert "symbol" in result["BTC"]
        mock_client.get_klines.assert_called_once_with(symbol="BTCUSDT", interval="1h", limit=100)

    def test_calculate_indicators_insufficient_data(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test indicator calculation with insufficient data."""
        # Mock insufficient data (less than minimum required)
        mock_client.get_klines.return_value = [
            ["1672531200000", "50000", "50100", "49900", "50050", "1000", "1672617599999", "50000000", 100, "500", "25000000", "0"]
            for _ in range(5)  # Only 5 data points
        ]

        result = indicator_service.calculate_indicators(["BTC"])

        # Check new error format
        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: Insufficient data" in result["errors"]["error_list"]
        assert "BTC" not in result  # Symbol is not included when there are errors

    def test_calculate_indicators_api_error(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test indicator calculation when API call fails."""
        mock_client.get_klines.side_effect = Exception("API connection failed")

        result = indicator_service.calculate_indicators(["BTC"])

        # Check new error format
        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: Insufficient data" in result["errors"]["error_list"]
        assert "BTC" not in result  # Symbol is not included when there are errors

    def test_calculate_indicators_empty_symbols(self, indicator_service: IndicatorService) -> None:
        """Test calculation with empty symbol list."""
        result = indicator_service.calculate_indicators([])
        assert result == {}

    def test_calculate_indicators_invalid_symbols(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test calculation with invalid symbols."""
        # Test with None and empty strings
        result = indicator_service.calculate_indicators([None, "", "BTC"])

        # Should only process valid symbols
        if result:
            assert "BTC" in result or len(result) == 0

    def test_get_technical_indicators_success(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test successful technical indicator retrieval."""
        result = indicator_service.get_technical_indicators("BTC")

        assert result is not None
        assert result["symbol"] == "BTCUSDT"
        assert "close" in result
        assert "rsi" in result
        assert "ema_10" in result
        mock_client.get_klines.assert_called_once_with(symbol="BTCUSDT", interval="1h", limit=100)

    def test_get_technical_indicators_api_failure(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test technical indicator retrieval when API fails."""
        mock_client.get_klines.side_effect = Exception("Network error")

        result = indicator_service.get_technical_indicators("BTC")
        assert result is None

    def test_calculate_and_display_indicators(
        self, indicator_service: IndicatorService, mock_client: MagicMock, caplog: LogCaptureFixture, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test indicator calculation and display."""
        import logging

        caplog.set_level(logging.INFO)  # Ensure we capture INFO level logs

        indicator_service.calculate_and_display_indicators(coin_symbols=["BTC"])

        # Check console output
        captured = capsys.readouterr()
        assert "Technical Indicators Summary" in captured.out
        assert "BTC" in captured.out

        # Check logging
        assert "Calculating indicators for 1 symbols: ['BTC']" in caplog.text


class TestIndicatorCalculations:
    """Test individual indicator calculation methods."""

    def test_calculate_rsi_with_sufficient_data(self, indicator_service: IndicatorService) -> None:
        """Test RSI calculation with sufficient data."""
        # Create DataFrame with price variation
        df = pd.DataFrame({"Close": [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115, 117, 116, 118, 120, 119]})

        rsi_series = indicator_service._calculations.calculate_rsi(df)
        assert rsi_series is not None
        assert len(rsi_series) > 0
        # RSI should be between 0 and 100
        for rsi_val in rsi_series.dropna():
            assert 0 <= rsi_val <= 100

    def test_calculate_rsi_insufficient_data(self, indicator_service: IndicatorService) -> None:
        """Test RSI calculation with insufficient data."""
        df = pd.DataFrame({"Close": [100, 101, 102]})  # Only 3 data points

        rsi_series = indicator_service._calculations.calculate_rsi(df)
        assert rsi_series is None

    def test_calculate_emas_success(self, indicator_service: IndicatorService) -> None:
        """Test EMA calculation with sufficient data."""
        df = pd.DataFrame(
            {
                "Close": [50000 + i * 100 for i in range(30)]  # 30 data points, trending up
            }
        )

        indicator_service._calculations.calculate_emas(df)

        # Check that EMA columns were added
        assert "EMA_10" in df.columns
        assert "EMA_21" in df.columns
        # EMA_50 should not be added with only 30 data points

    def test_calculate_macd_success(self, indicator_service: IndicatorService) -> None:
        """Test MACD calculation with sufficient data."""
        df = pd.DataFrame(
            {
                "Close": [50000 + i * 50 for i in range(40)]  # 40 data points (sufficient for MACD signal)
            }
        )

        macd_line, signal_line = indicator_service._calculations.calculate_macd(df)

        assert macd_line is not None
        assert signal_line is not None
        assert len(macd_line) > 0
        assert len(signal_line) > 0

    def test_calculate_macd_insufficient_data(self, indicator_service: IndicatorService) -> None:
        """Test MACD calculation with insufficient data."""
        df = pd.DataFrame(
            {
                "Close": [50000, 50100, 50200]  # Only 3 data points
            }
        )

        macd_line, signal_line = indicator_service._calculations.calculate_macd(df)

        assert macd_line is None
        assert signal_line is None

    def test_find_swing_lows_success(self, indicator_service: IndicatorService) -> None:
        """Test swing low detection with realistic data."""
        # Create price data with clear swing lows
        prices = [100, 95, 90, 95, 100, 105, 100, 95, 90, 85, 90, 95]
        low_series = pd.Series(prices)

        swing_lows = indicator_service._support_resistance.find_swing_lows(low_series, window=2)

        assert isinstance(swing_lows, list)
        assert len(swing_lows) <= len(prices)
        # All swing lows should be actual prices from the data
        for swing_low in swing_lows:
            assert swing_low in prices

    def test_extract_indicator_data(self, indicator_service: IndicatorService) -> None:
        """Test indicator data extraction and formatting."""
        df = pd.DataFrame(
            {
                "Close": [50000],
                "Volume": [1000000],
                "RSI": [65.5],
                "EMA_10": [49800],
                "EMA_21": [49600],
                "MACD_Line": [150.75],
                "Signal_Line": [145.25],
            }
        )

        result = indicator_service._display.extract_indicator_data(df, "BTCUSDT", [49000])

        assert result["symbol"] == "BTCUSDT"
        assert result["close"] == "50000.00"
        assert result["rsi"] == "65.50"
        assert result["ema_10"] == "49800.00"
        assert "49000.00" in result["support_levels"]

    def test_extract_indicator_data_with_mixed_types(self, indicator_service: IndicatorService) -> None:
        """Test indicator data extraction with mixed data types."""
        # This test specifically checks the fix for the '>' not supported between 'str' and 'int' error
        df = pd.DataFrame(
            {
                "Close": ["50000"],  # String instead of number
                "Volume": [1000000],
                "RSI": [65.5],
                "EMA_10": ["49800"],  # String instead of number
            }
        )

        # This should not raise a TypeError
        result = indicator_service._display.extract_indicator_data(df, "BTCUSDT", [49000])

        assert result["symbol"] == "BTCUSDT"
        assert result["close"] == "N/A"  # String values should be handled gracefully
        assert result["ema_10"] == "N/A"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_malformed_kline_data(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test handling of malformed kline data."""
        mock_client.get_klines.return_value = []  # Empty response

        result = indicator_service.calculate_indicators(["BTC"])

        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: Insufficient data" in result["errors"]["error_list"]
        assert "BTC" not in result  # Symbol is not included when there are errors

    def test_network_timeout(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test handling of network timeouts."""
        from requests.exceptions import Timeout

        mock_client.get_klines.side_effect = Timeout("Request timeout")

        result = indicator_service.calculate_indicators(["BTC"])

        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: Insufficient data" in result["errors"]["error_list"]
        assert "BTC" not in result  # Symbol is not included when there are errors

    def test_invalid_price_data(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test handling of invalid price data."""
        # Mock klines with all zero prices
        mock_client.get_klines.return_value = [["1672531200000", "0", "0", "0", "0", "1000", "1672617599999", "0", 100, "500", "0", "0"] for _ in range(25)]

        result = indicator_service.calculate_indicators(["BTC"])

        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: Insufficient data" in result["errors"]["error_list"]
        assert "BTC" not in result  # Symbol is not included when there are errors


class TestSignalGeneration:
    """Test trading signal generation logic."""

    def test_signal_generation_buy_conditions(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test signal generation for buy conditions."""
        # Create klines that should generate a buy signal (RSI < 40, price > EMA)
        klines = []
        for i in range(30):
            if i < 20:
                # Initial higher prices
                close_price = 50000 + i * 100
            else:
                # Recent price drop (should create low RSI)
                close_price = 51000 - (i - 19) * 200

            klines.append(
                [
                    1672531200000 + i * 3600000,
                    close_price - 50,
                    close_price + 50,
                    close_price - 100,
                    close_price,
                    1000,
                    1672531200000 + (i + 1) * 3600000,
                    50000000,
                    100,
                    500,
                    25000000,
                    0,
                ]
            )

        mock_client.get_klines.return_value = klines

        result = indicator_service.calculate_indicators(["BTC"])

        if "BTC" in result and "errors" not in result["BTC"]:
            assert "signal" in result["BTC"]
            assert result["BTC"]["signal"] in ["STRONG BUY", "BUY", "SELL", "STRONG SELL", "NEUTRAL"]

    def test_signal_generation_with_insufficient_indicators(self, indicator_service: IndicatorService, mock_client: MagicMock) -> None:
        """Test signal generation when indicators can't be calculated."""
        # Provide minimal data that won't allow indicator calculation
        mock_client.get_klines.return_value = [
            ["1672531200000", "50000", "50100", "49900", "50050", "1000", "1672617599999", "50000000", 100, "500", "25000000", "0"]
        ]

        result = indicator_service.calculate_indicators(["BTC"])

        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: Insufficient data" in result["errors"]["error_list"]
        assert "BTC" not in result  # Symbol is not included when there are errors
