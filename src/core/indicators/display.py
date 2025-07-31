"""Display utilities for technical indicators.

This module handles the rich console display and data extraction
for technical indicator results.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandas import DataFrame
from rich.console import Console
from rich.table import Table


class IndicatorDisplay:
    """Handles display and formatting of technical indicator results."""

    def __init__(self) -> None:
        """Initialize the display handler."""
        self._console = Console()

    def extract_indicator_data(self, df: DataFrame, symbol_pair: str, support_levels: list[float]) -> dict[str, Any]:
        """Extracts indicator data from DataFrame for display.

        Args:
            df: DataFrame containing calculated indicators
            symbol_pair: The trading pair symbol
            support_levels: List of detected support levels

        Returns:
            Dictionary containing formatted indicator data
        """
        last = df.iloc[-1]
        cols = df.columns

        # Format support levels for display
        support_str = ", ".join([f"{level:.2f}" for level in support_levels[:3]])  # Show top 3
        if not support_str:
            support_str = "None"

        # Helper function to safely format values
        def safe_format(value, decimal_places=2, use_commas=False):
            if isinstance(value, int | float):
                format_str = f"{{:,.{decimal_places}f}}" if use_commas else f"{{:.{decimal_places}f}}"
                return format_str.format(value)
            return "N/A"

        # Get values with proper type handling
        def get_value(column, default=0):
            if column in cols:
                val = last[column]
                return val if not pd.isna(val) else default
            return default

        return {
            "symbol": symbol_pair,
            "close": safe_format(get_value("Close")),
            "rsi": safe_format(get_value("RSI")) if "RSI" in cols else "N/A",
            "ema_10": safe_format(get_value("EMA_10")) if "EMA_10" in cols else "N/A",
            "ema_21": safe_format(get_value("EMA_21")) if "EMA_21" in cols else "N/A",
            "ema_50": safe_format(get_value("EMA_50")) if "EMA_50" in cols else "N/A",
            "macd_line": safe_format(get_value("MACD_Line"), 4) if "MACD_Line" in cols else "N/A",
            "signal_line": safe_format(get_value("Signal_Line"), 4) if "Signal_Line" in cols else "N/A",
            "macd_histogram": safe_format(get_value("MACD_Histogram"), 4) if "MACD_Histogram" in cols else "N/A",
            "volume": safe_format(get_value("Volume"), 2, True),
            "support_levels": support_str,
        }

    def display_indicators_table(self, indicators_data: list[dict[str, Any]]) -> None:
        """Displays technical indicators in a structured Rich table.

        Args:
            indicators_data: List of indicator data dictionaries
        """
        table = Table(title="Technical Indicators Summary", show_header=True, header_style="bold magenta")
        table.add_column("Symbol", style="cyan", no_wrap=True)
        table.add_column("Close", justify="right", style="green")
        table.add_column("Volume", justify="right")
        table.add_column("RSI", justify="right", style="blue")
        table.add_column("EMA 10", justify="right")
        table.add_column("EMA 21", justify="right")
        table.add_column("EMA 50", justify="right")
        table.add_column("MACD", justify="right", style="yellow")
        table.add_column("Signal", justify="right", style="yellow")
        table.add_column("Support Levels", style="dim")

        for data in indicators_data:
            table.add_row(
                data["symbol"],
                data["close"],
                data["volume"],
                data["rsi"],
                data["ema_10"],
                data["ema_21"],
                data["ema_50"],
                data["macd_line"],
                data["signal_line"],
                data["support_levels"],
            )

        self._console.print(table)

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Convenience method for console printing.

        Args:
            *args: Arguments to pass to console.print
            **kwargs: Keyword arguments to pass to console.print
        """
        self._console.print(*args, **kwargs)
