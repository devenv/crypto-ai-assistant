from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture

from core.config import AppConfig
from core.indicators import IndicatorService


@pytest.fixture
def mock_client() -> MagicMock:
    """Fixture to create a mock BinanceClient."""
    client = MagicMock()
    # Provide realistic-looking k-line data (list of lists)
    # 100 entries to satisfy the minimum data requirements for indicators
    kline_data = [
        [
            1672531200000 + i * 86400000,  # Open time
            200 + i,  # Open
            210 + i,  # High
            190 + i,  # Low
            205 + i,  # Close
            1000,  # Volume
            1672617599999 + i * 86400000,  # Close time
            205000,
            100,
            500,
            102500,
            0,
        ]
        for i in range(100)
    ]
    client.get_klines.return_value = kline_data
    return client


@pytest.fixture
def mock_config() -> AppConfig:
    """Fixture to create a mock config dictionary."""
    return {
        "cli": {"account_min_value": 1.0, "history_limit": 5},
        "analysis": {
            "rsi_period": 14,
            "ema_short_period": 12,
            "ema_long_period": 26,
            "ema_signal_period": 9,
            "ema_periods": [10, 21, 50],
            "min_data_points": 35,
        },
    }


@pytest.fixture
def indicator_service(mock_client: MagicMock, mock_config: AppConfig) -> IndicatorService:
    """Fixture to create an IndicatorService instance with a mock client and config."""
    return IndicatorService(mock_client, mock_config)


def test_calculate_and_display_indicators(
    indicator_service: IndicatorService, mock_client: MagicMock, caplog: LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Test that indicator calculation runs and displays output.
    This is more of an integration test for the function, not for the accuracy
    of the indicator math itself, which is assumed to be correct from pandas.
    """
    import logging

    caplog.set_level(logging.INFO)

    indicator_service.calculate_and_display_indicators(coin_symbols=["BTC"])

    mock_client.get_klines.assert_called_once_with(symbol="BTCUSDT", interval="1d", limit=100)

    # Check that console output contains the table
    captured = capsys.readouterr()
    assert "Technical Indicators Summary" in captured.out
    assert "BTCUSDT" in captured.out
    assert "Close" in captured.out
    assert "RSI" in captured.out
    assert "EMA" in captured.out
    assert "MACD" in captured.out

    # Check that processing message is logged
    log_output = caplog.text
    assert "Processing BTCUSDT..." in log_output


def test_calculate_and_display_handles_none_indicators(
    indicator_service: IndicatorService, mock_client: MagicMock, mock_config: AppConfig, caplog: LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that N/A is handled correctly in display when indicator calculations fail."""
    import logging

    caplog.set_level(logging.INFO)

    # Use a dataframe size that passes the min_data_points check
    kline_data = [[i for i in range(12)] for _ in range(40)]
    mock_client.get_klines.return_value = kline_data

    # Set config to require more data than available for RSI/MACD
    mock_config["analysis"]["rsi_period"] = 50
    mock_config["analysis"]["ema_long_period"] = 50

    indicator_service.calculate_and_display_indicators(coin_symbols=["BTC"])

    # Check console output for N/A values
    captured = capsys.readouterr()
    assert "Technical Indicators Summary" in captured.out
    assert "BTCUSDT" in captured.out
    assert "N/A" in captured.out  # Should contain N/A for failed calculations


def test_insufficient_data_for_indicators(
    indicator_service: IndicatorService, mock_client: MagicMock, caplog: LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that warnings are displayed when there is not enough data."""
    import logging

    caplog.set_level(logging.WARNING)

    # Mock kline data with the correct number of columns but few rows
    kline_data = [[i for i in range(12)] for _ in range(10)]  # 10 data points
    mock_client.get_klines.return_value = kline_data
    indicator_service.calculate_and_display_indicators(coin_symbols=["FEW"])

    # Check console output for insufficient data message
    captured = capsys.readouterr()
    assert "Insufficient data points (10) for FEWUSDT for meaningful analysis." in captured.out

    # Test with no data
    mock_client.get_klines.return_value = []
    indicator_service.calculate_and_display_indicators(coin_symbols=["NONE"])
    captured = capsys.readouterr()
    assert "No kline data fetched for NONEUSDT. Skipping." in captured.out


def test_indicator_calculations_with_minimal_data(indicator_service: IndicatorService) -> None:
    """Test individual indicator functions with minimal data to hit edge cases."""
    # This test doesn't check for correctness, just that the functions run without error
    # and hit the conditional branches for small dataframes.

    def create_df(num_rows: int) -> pd.DataFrame:
        kline_data = [[i for i in range(12)] for _ in range(num_rows)]
        df = pd.DataFrame(
            kline_data,
            columns=[
                "Open time",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Close time",
                "Quote asset volume",
                "Number of trades",
                "Taker buy base asset volume",
                "Taker buy quote asset volume",
                "Ignore",
            ],
        )
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    # These calls should trigger the length checks and return early
    indicator_service._calculate_rsi(create_df(10))
    indicator_service._calculate_emas(create_df(5))
    indicator_service._calculate_macd(create_df(20))  # Should hit the len < 26 check
    indicator_service._find_swing_lows(create_df(3)["Low"].astype(float))  # Should hit the len < 5 check


def test_find_swing_lows_logic(indicator_service: IndicatorService) -> None:
    """Test the logic of _find_swing_lows."""
    low_series = pd.Series([10, 5, 12, 4, 15, 6, 11]).astype(float)
    swing_lows = indicator_service._find_swing_lows(low_series, window=1)
    assert swing_lows == [4.0, 5.0, 6.0]


def test_find_swing_lows_not_enough_data(indicator_service: IndicatorService) -> None:
    """Test the early return from _find_swing_lows if data is too short."""
    low_series = pd.Series([1, 2, 3, 4])
    result = indicator_service._find_swing_lows(low_series.astype(float), window=2)
    assert result == []


def test_get_technical_indicators_success(indicator_service: IndicatorService, mock_client: MagicMock) -> None:
    """Test successful calculation of technical indicators for a single coin."""
    results = indicator_service.get_technical_indicators("BTC")

    assert results is not None
    mock_client.get_klines.assert_called_once_with(symbol="BTCUSDT", interval="1d", limit=100)
    assert results["symbol"] == "BTCUSDT"
    assert "close" in results
    assert "rsi" in results
    assert "ema_10" in results


def test_get_technical_indicators_no_data(indicator_service: IndicatorService, mock_client: MagicMock) -> None:
    """Test get_technical_indicators with no kline data."""
    mock_client.get_klines.return_value = []
    results = indicator_service.get_technical_indicators("NONE")
    assert results is None


def test_get_technical_indicators_insufficient_data(indicator_service: IndicatorService, mock_client: MagicMock) -> None:
    """Test get_technical_indicators with insufficient data points."""
    kline_data = [[i for i in range(12)] for _ in range(10)]  # 10 data points
    mock_client.get_klines.return_value = kline_data
    results = indicator_service.get_technical_indicators("FEW")
    assert results is None


def test_get_technical_indicators_handles_none_indicators(
    indicator_service: IndicatorService, mock_client: MagicMock, mock_config: AppConfig, caplog: LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that N/A is returned when indicator calculations fail."""
    import logging

    caplog.set_level(logging.INFO)

    # Set config to require more data than available for RSI/MACD
    mock_config["analysis"]["rsi_period"] = 150
    mock_config["analysis"]["ema_long_period"] = 150
    # Data has 100 points, so RSI and MACD should fail to calculate
    results = indicator_service.get_technical_indicators("BTC")

    assert results is not None
    assert results["rsi"] == "N/A"
    assert results["macd_line"] == "N/A"
    assert results["signal_line"] == "N/A"
    assert results["ema_10"] != "N/A"  # EMA 10 should still be calculated

    # Also test the display function
    caplog.clear()
    mock_client.get_klines.reset_mock()
    indicator_service.calculate_and_display_indicators(["BTC"])

    # Check console output instead of log output
    captured = capsys.readouterr()
    assert "Technical Indicators Summary" in captured.out
    assert "N/A" in captured.out  # Should contain N/A for failed calculations
