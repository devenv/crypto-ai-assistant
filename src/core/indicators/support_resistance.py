"""Support and resistance level detection.

This module handles the detection of swing lows and highs that serve as
potential support and resistance levels in technical analysis.
"""

from __future__ import annotations

from pandas import Series


class SupportResistanceDetector:
    """Detects support and resistance levels from price data."""

    def find_swing_lows(self, low_series: Series, window: int = 2) -> list[float]:
        """Finds swing lows in a series of low prices.

        A swing low is a point that is lower than the points `window` periods
        before and after it.

        Args:
            low_series: A pandas Series of low prices.
            window: The number of periods to look back and forward.

        Returns:
            A sorted list of unique swing low prices.
        """
        if len(low_series) < window * 2 + 1:
            return []
        lows: list[float] = []
        # Ensure the series is float for comparison
        low_series_float: Series = low_series.astype(float)
        start_index = max(window, len(low_series_float) - 50)
        end_index = len(low_series_float) - window
        for i in range(start_index, end_index):
            # Access series values with proper typing
            current_low = low_series_float.iloc[i]
            before_min = low_series_float.iloc[i - window : i].min()
            after_min = low_series_float.iloc[i + 1 : i + window + 1].min()
            is_swing_low = current_low < before_min and current_low < after_min
            if is_swing_low:
                lows.append(float(current_low))
        return sorted(set(lows))

    def find_swing_lows_from_prices(self, prices: list[float], window: int = 2) -> list[float]:
        """Find swing lows from a list of prices.

        Args:
            prices: List of price values
            window: Number of periods to look back and forward

        Returns:
            List of swing low prices
        """
        if len(prices) < window * 2 + 1:
            return []

        lows: list[float] = []
        # Only look at recent data to avoid too many old support levels
        start_index = max(window, len(prices) - 50)
        end_index = len(prices) - window

        for i in range(start_index, end_index):
            # Check if current price is lower than surrounding prices
            left_min = min(prices[i - window : i])
            right_min = min(prices[i + 1 : i + window + 1])

            if prices[i] < left_min and prices[i] < right_min:
                lows.append(prices[i])

        return sorted(set(lows))
