"""Data processing for technical indicators.

This module handles k-line data fetching, processing, and conversion
into pandas DataFrames for technical analysis.
"""

from __future__ import annotations

import logging
from typing import Any, cast

import pandas as pd
from pandas import DataFrame

from api.client import BinanceClient

logger = logging.getLogger(__name__)


def safe_float(value: str, default: float = 0.0) -> float:
    """Safely converts a string to a float.

    Args:
        value: The string value to convert.
        default: The default value to return if conversion fails.

    Returns:
        The converted float or the default value.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


class DataProcessor:
    """Handles k-line data processing and DataFrame creation."""

    def __init__(self, client: BinanceClient) -> None:
        """Initialize with Binance client.

        Args:
            client: Binance API client for data fetching
        """
        self._client = client

    def fetch_and_process_kline_data(self, coin_symbol: str, interval: str = "1h", limit: int = 100) -> DataFrame | None:
        """Fetch and process k-line data for a symbol.

        Args:
            coin_symbol: The coin symbol (e.g., "BTC")
            interval: The k-line interval (default: "1h")
            limit: Number of k-lines to fetch (default: 100)

        Returns:
            Processed DataFrame or None if data is insufficient
        """
        symbol_pair = f"{coin_symbol.upper()}USDT"
        logger.info(f"Processing {symbol_pair}...")

        try:
            # Use hourly data with more periods for better EMA calculation
            kline_data = self._client.get_klines(symbol=symbol_pair, interval=interval, limit=limit)
        except Exception as e:
            logger.error(f"API error fetching kline data for {symbol_pair}: {e}")
            return None

        if not kline_data:
            logger.warning(f"No kline data fetched for {symbol_pair}. Skipping.")
            return None

        return self._process_kline_data(kline_data, symbol_pair)

    def _process_kline_data(self, kline_data: list[Any], symbol_pair: str) -> DataFrame | None:
        """Process raw k-line data into a clean DataFrame.

        Args:
            kline_data: Raw k-line data from Binance API
            symbol_pair: The trading pair symbol

        Returns:
            Processed DataFrame or None if insufficient data
        """
        # Create DataFrame with explicit type annotation for columns
        column_names = [
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
        ]
        # Use cast to resolve pandas DataFrame columns typing issue
        df: DataFrame = pd.DataFrame(kline_data, columns=cast(Any, column_names))

        # Convert price and volume columns to numeric
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(subset=["Open", "High", "Low", "Close", "Volume"], inplace=True)

        # Ensure proper float types for calculations
        df["Close"] = df["Close"].astype(float)
        df["Low"] = df["Low"].astype(float)

        # Use reasonable minimum for hourly data (need at least 50 for EMA calculations)
        min_data_points = 50  # Override config for hourly analysis
        if len(df) < min_data_points:
            logger.warning(f"Insufficient data points ({len(df)}) for {symbol_pair} for meaningful analysis.")
            return None

        return df
