"""Technical indicator calculation methods.

This module contains the core mathematical calculations for technical indicators
including RSI, EMA, and MACD.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd
from pandas import Series

if TYPE_CHECKING:
    from ..config import AppConfig

logger = logging.getLogger(__name__)


class IndicatorCalculations:
    """Handles mathematical calculations for technical indicators."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize with configuration.

        Args:
            config: Application configuration containing indicator parameters
        """
        self._config = config

    def calculate_rsi_from_prices(self, prices: list[float]) -> float | None:
        """Calculate RSI from a list of prices.

        Args:
            prices: List of price values

        Returns:
            Current RSI value or None if insufficient data
        """
        window = self._config["analysis"]["rsi_period"]
        if len(prices) < window + 1:  # Need at least window+1 for diff calculation
            return None

        try:
            # Convert to pandas Series and calculate RSI
            series = pd.Series(prices)
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).ewm(com=window - 1, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(com=window - 1, adjust=False).mean()
            rs = gain / loss
            rsi_series = 100 - (100 / (1 + rs))
            return float(rsi_series.iloc[-1])
        except Exception:
            return None

    def calculate_rsi(self, df: pd.DataFrame) -> Series | None:
        """Calculates the Relative Strength Index (RSI).

        Args:
            df: A DataFrame with a "Close" column.

        Returns:
            A pandas Series containing the RSI values, or None if there is
            not enough data.
        """
        window = self._config["analysis"]["rsi_period"]
        if len(df) < window:
            return None
        close_series: Series = df["Close"].astype(float)
        delta: Series = close_series.diff()
        gain: Series = (delta.where(delta > 0, 0)).ewm(com=window - 1, adjust=False).mean()
        loss: Series = (-delta.where(delta < 0, 0)).ewm(com=window - 1, adjust=False).mean()
        rs: Series = gain / loss
        rsi: Series = 100 - (100 / (1 + rs))
        return rsi

    def calculate_ema(self, prices: list[float], period: int) -> float | None:
        """Calculate a single Exponential Moving Average for a given period.

        Args:
            prices: List of price values
            period: EMA period

        Returns:
            Current EMA value or None if insufficient data
        """
        if len(prices) < period:
            return None

        try:
            # Convert to pandas Series and calculate EMA
            series: Series = pd.Series(prices)
            ema_series: Series = series.ewm(span=period, adjust=False).mean()
            return float(ema_series.iloc[-1])
        except Exception:
            return None

    def calculate_emas(self, df: pd.DataFrame) -> None:
        """Calculates multiple Exponential Moving Averages (EMAs).

        The periods for the EMAs are defined in the application configuration.

        Args:
            df: A DataFrame with a "Close" column. The calculated EMAs will
                be added as new columns.
        """
        ema_periods = self._config["analysis"]["ema_periods"]
        close_series: Series = df["Close"].astype(float)

        for period in ema_periods:
            if len(df) >= period:
                df[f"EMA_{period}"] = close_series.ewm(span=period, adjust=False).mean()

    def calculate_macd(self, df: pd.DataFrame) -> tuple[Series | None, Series | None]:
        """Calculates the MACD (Moving Average Convergence Divergence).

        Args:
            df: A DataFrame with a "Close" column.

        Returns:
            A tuple containing the MACD line and Signal line Series, or
            (None, None) if there is not enough data.
        """
        fast_period = self._config["analysis"]["ema_short_period"]
        slow_period = self._config["analysis"]["ema_long_period"]
        signal_period = self._config["analysis"]["ema_signal_period"]

        if len(df) < slow_period:
            return None, None

        close_series: Series = df["Close"].astype(float)
        ema_fast: Series = close_series.ewm(span=fast_period, adjust=False).mean()
        ema_slow: Series = close_series.ewm(span=slow_period, adjust=False).mean()
        macd_line: Series = ema_fast - ema_slow

        if len(df) < slow_period + signal_period:
            return macd_line, None

        signal_line: Series = macd_line.ewm(span=signal_period, adjust=False).mean()
        return macd_line, signal_line
