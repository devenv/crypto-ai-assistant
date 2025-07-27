"""Main indicator service that orchestrates technical analysis.

This module contains the primary IndicatorService class that coordinates
data processing, calculations, display, and support/resistance detection.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from pandas import DataFrame, Series

from api.client import BinanceClient

from ..config import AppConfig
from .calculations import IndicatorCalculations
from .data_processor import DataProcessor
from .display import IndicatorDisplay
from .support_resistance import SupportResistanceDetector

logger = logging.getLogger(__name__)


class IndicatorService:
    """Provides methods for calculating technical analysis indicators."""

    def __init__(self, client: BinanceClient, config: AppConfig) -> None:
        """Initializes the IndicatorService.

        Args:
            client: An instance of `BinanceClient` to interact with the API.
            config: The application configuration.
        """
        self._client = client
        self._config = config

        # Initialize component classes
        self._calculations = IndicatorCalculations(config)
        self._data_processor = DataProcessor(client)
        self._display = IndicatorDisplay()
        self._support_resistance = SupportResistanceDetector()

    def get_technical_indicators(self, coin_symbol: str) -> dict[str, Any] | None:
        """
        Fetches k-line data and calculates technical indicators for a single coin.
        Returns a dictionary with the results, or None if data is insufficient.
        """
        # Fetch and process the data
        df = self._data_processor.fetch_and_process_kline_data(coin_symbol)
        if df is None:
            return None

        symbol_pair = f"{coin_symbol.upper()}USDT"

        # Calculate indicators
        self._add_indicators_to_dataframe(df)

        # Detect support levels
        low_series: Series = cast(Series, df["Low"].astype(float))
        support_levels = self._support_resistance.find_swing_lows(low_series)

        # Extract and return formatted data
        return self._display.extract_indicator_data(df, symbol_pair, support_levels)

    def calculate_indicators(self, coin_symbols: list[str]) -> dict[str, dict[str, Any]]:
        """Calculate technical indicators for multiple symbols.

        Args:
            coin_symbols: List of coin symbols to analyze

        Returns:
            Dictionary mapping symbols to their indicator data
        """
        if not coin_symbols:
            logger.warning("No coin symbols provided")
            return {}

        logger.info(f"Calculating indicators for {len(coin_symbols)} symbols: {coin_symbols}")

        results: dict[str, dict[str, Any]] = {}
        errors: list[str] = []

        for symbol in coin_symbols:
            try:
                symbol_key = symbol.upper()
                indicators = self.get_technical_indicators(symbol)

                if indicators:
                    results[symbol_key] = indicators
                    logger.debug(f"Successfully calculated indicators for {symbol_key}")
                else:
                    logger.warning(f"No indicators calculated for {symbol_key}")
                    errors.append(f"{symbol_key}: Insufficient data")

            except Exception as e:
                logger.error(f"Unexpected error calculating indicators for {symbol}: {e}")
                errors.append(f"{symbol}: {str(e)}")

        if errors:
            results["errors"] = {"error_list": errors}

        return results

    def calculate_and_display_indicators(self, coin_symbols: list[str]) -> None:
        """Calculate and display technical indicators with enhanced error handling.

        Args:
            coin_symbols: List of coin symbols to analyze
        """
        try:
            if not coin_symbols:
                self._display.print("⚠️  [yellow]No symbols provided for indicator analysis[/yellow]")
                return

            self._display.print(f"🔍 Analyzing technical indicators for: {', '.join(coin_symbols)}")

            # Calculate indicators
            indicators = self.calculate_indicators(coin_symbols)

            if not indicators:
                self._display.print("❌ [red]No indicator data available[/red]")
                return

            # Check for errors
            if "errors" in indicators:
                error_list = indicators["errors"]["error_list"]
                self._display.print(f"⚠️  [yellow]Errors occurred for {len(error_list)} symbols[/yellow]")
                for error in error_list:
                    self._display.print(f"   • {error}")
                del indicators["errors"]  # Remove errors from display data

            if not indicators:
                self._display.print("❌ [red]No valid indicator data to display[/red]")
                return

            # Prepare data for table display
            indicators_data = list(indicators.values())

            # Display results
            self._display.display_indicators_table(indicators_data)

            self._display.print(f"\n✅ [green]Analysis complete for {len(indicators_data)} symbols[/green]")

        except Exception as e:
            logger.error(f"Error in calculate_and_display_indicators: {e}")
            self._display.print(f"❌ [red]Error during indicator analysis: {e}[/red]")

    def get_indicators(self, coin_symbols: list[str]) -> dict[str, dict[str, Any]]:
        """Get technical indicators for multiple symbols (alias for calculate_indicators).

        Args:
            coin_symbols: List of coin symbols to analyze

        Returns:
            Dictionary mapping symbols to their indicator data
        """
        return self.calculate_indicators(coin_symbols)

    def _add_indicators_to_dataframe(self, df: DataFrame) -> None:
        """Add all calculated indicators to the DataFrame.

        Args:
            df: DataFrame to add indicators to
        """
        # Calculate RSI
        rsi_series = self._calculations.calculate_rsi(df)
        if rsi_series is not None:
            df["RSI"] = rsi_series

        # Calculate EMAs
        self._calculations.calculate_emas(df)

        # Calculate MACD
        macd_line, signal_line = self._calculations.calculate_macd(df)
        if macd_line is not None and signal_line is not None:
            df["MACD_Line"] = macd_line
            df["Signal_Line"] = signal_line
            df["MACD_Histogram"] = df["MACD_Line"] - df["Signal_Line"]
