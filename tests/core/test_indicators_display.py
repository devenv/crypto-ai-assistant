"""Tests for the indicators display module."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest
from pandas import DataFrame

from src.core.indicators.display import IndicatorDisplay


@pytest.fixture
def display_handler() -> IndicatorDisplay:
    """Create an IndicatorDisplay instance for testing."""
    return IndicatorDisplay()


@pytest.fixture
def sample_dataframe() -> DataFrame:
    """Create a sample DataFrame with indicator data."""
    return pd.DataFrame(
        {
            "Close": [100.0, 101.0, 102.0],
            "Open": [99.0, 100.0, 101.0],
            "High": [102.0, 103.0, 104.0],
            "Low": [98.0, 99.0, 100.0],
            "Volume": [1000.0, 1100.0, 1200.0],
            "RSI": [45.0, 50.0, 55.0],
            "EMA_10": [98.0, 99.0, 100.0],
            "EMA_21": [97.0, 98.0, 99.0],
            "EMA_50": [96.0, 97.0, 98.0],
            "MACD_Line": [0.5, 0.6, 0.7],
            "Signal_Line": [0.4, 0.5, 0.6],
            "MACD_Histogram": [0.1, 0.1, 0.1],
        }
    )


@pytest.fixture
def sample_indicators_data() -> list[dict]:
    """Create sample indicator data for display testing."""
    return [
        {
            "symbol": "BTCUSDT",
            "close": "50000.00",
            "rsi": "65.50",
            "ema_10": "49800.00",
            "ema_21": "49600.00",
            "ema_50": "49400.00",
            "macd_line": "150.5000",
            "signal_line": "145.2500",
            "macd_histogram": "5.2500",
            "volume": "1,200,000.00",
            "support_levels": "49000.00, 48000.00, 47000.00",
        },
        {
            "symbol": "ETHUSDT",
            "close": "3500.00",
            "rsi": "55.20",
            "ema_10": "3450.00",
            "ema_21": "3400.00",
            "ema_50": "3350.00",
            "macd_line": "25.5000",
            "signal_line": "20.2500",
            "macd_histogram": "5.2500",
            "volume": "500,000.00",
            "support_levels": "3400.00, 3300.00, 3200.00",
        },
    ]


class TestIndicatorDisplay:
    """Test suite for IndicatorDisplay class."""

    def test_extract_indicator_data_with_complete_data(self, display_handler: IndicatorDisplay, sample_dataframe: DataFrame) -> None:
        """Test extraction with complete indicator data."""
        support_levels = [95.0, 90.0, 85.0]
        result = display_handler.extract_indicator_data(sample_dataframe, "BTCUSDT", support_levels)

        assert result["symbol"] == "BTCUSDT"
        assert result["close"] == "102.00"
        assert result["rsi"] == "55.00"
        assert result["ema_10"] == "100.00"
        assert result["ema_21"] == "99.00"
        assert result["ema_50"] == "98.00"
        assert result["macd_line"] == "0.7000"
        assert result["signal_line"] == "0.6000"
        assert result["macd_histogram"] == "0.1000"
        assert result["volume"] == "1,200.00"
        assert "95.00" in result["support_levels"]

    def test_extract_indicator_data_with_missing_columns(self, display_handler: IndicatorDisplay) -> None:
        """Test extraction with missing indicator columns."""
        # Create DataFrame with minimal columns
        df = pd.DataFrame(
            {
                "Close": [100.0],
                "Volume": [1000.0],
            }
        )

        result = display_handler.extract_indicator_data(df, "ETHUSDT", [])

        assert result["symbol"] == "ETHUSDT"
        assert result["close"] == "100.00"
        assert result["rsi"] == "N/A"
        assert result["ema_10"] == "N/A"
        assert result["volume"] == "1,000.00"
        assert result["support_levels"] == "None"

    def test_extract_indicator_data_with_string_values(self, display_handler: IndicatorDisplay) -> None:
        """Test extraction with string values in numeric columns."""
        # Create DataFrame with string values that would cause formatting errors
        df = pd.DataFrame(
            {
                "Close": ["100.0"],  # String instead of float
                "Volume": ["1000"],
                "RSI": ["N/A"],
            }
        )

        result = display_handler.extract_indicator_data(df, "SOLUSDT", [80.0])

        assert result["symbol"] == "SOLUSDT"
        assert result["close"] == "N/A"  # Should handle string value gracefully
        assert result["rsi"] == "N/A"
        assert result["volume"] == "N/A"
        assert "80.00" in result["support_levels"]

    def test_extract_indicator_data_with_nan_values(self, display_handler: IndicatorDisplay) -> None:
        """Test extraction with NaN values."""
        # Create DataFrame with NaN values
        df = pd.DataFrame(
            {
                "Close": [100.0],
                "Volume": [pd.NA],
                "RSI": [float("nan")],  # Use float('nan') instead of pd.NaN
                "EMA_10": [None],
            }
        )

        result = display_handler.extract_indicator_data(df, "BTCUSDT", [])

        assert result["symbol"] == "BTCUSDT"
        assert result["close"] == "100.00"
        assert result["rsi"] == "0.00"  # NaN should be replaced with default
        assert result["ema_10"] == "0.00"  # None should be replaced with default
        assert result["volume"] == "0.00"  # NA should be replaced with default

    def test_display_indicators_table(self, display_handler: IndicatorDisplay, sample_indicators_data: list[dict]) -> None:
        """Test displaying indicators in a table."""
        # Mock the console to capture output
        with patch.object(display_handler, "_console") as mock_console:
            display_handler.display_indicators_table(sample_indicators_data)

            # Verify the console.print was called with a table
            mock_console.print.assert_called_once()

            # Just verify that print was called - we can't easily check the table contents
            # in a unit test since rich tables don't have a string representation that includes the title
            assert mock_console.print.call_count == 1

    def test_print_method(self, display_handler: IndicatorDisplay) -> None:
        """Test the print convenience method."""
        # Mock the console to capture output
        with patch.object(display_handler, "_console") as mock_console:
            display_handler.print("Test message", style="bold")

            # Verify the console.print was called with the right arguments
            mock_console.print.assert_called_once_with("Test message", style="bold")

    def test_extract_indicator_data_with_large_numbers(self, display_handler: IndicatorDisplay) -> None:
        """Test extraction with large numbers for proper formatting."""
        df = pd.DataFrame(
            {
                "Close": [50000.0],
                "Volume": [1000000.0],
            }
        )

        result = display_handler.extract_indicator_data(df, "BTCUSDT", [])

        assert result["symbol"] == "BTCUSDT"
        assert result["close"] == "50000.00"
        assert result["volume"] == "1,000,000.00"  # Should have commas for large numbers
