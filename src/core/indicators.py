from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from pandas import DataFrame, Series
from rich.console import Console
from rich.table import Table

from api.client import BinanceClient
from core.config import AppConfig


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
        self._console = Console()

    def get_technical_indicators(self, coin_symbol: str) -> dict[str, Any] | None:
        """
        Fetches k-line data and calculates technical indicators for a single coin.
        Returns a dictionary with the results, or None if data is insufficient.
        """
        symbol_pair = f"{coin_symbol.upper()}USDT"
        logging.info(f"Processing {symbol_pair}...")

        kline_data = self._client.get_klines(symbol=symbol_pair, interval="1d", limit=100)
        if not kline_data:
            logging.warning(f"No kline data fetched for {symbol_pair}. Skipping.")
            return None

        df: DataFrame = pd.DataFrame(
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
        df.dropna(subset=["Open", "High", "Low", "Close", "Volume"], inplace=True)

        df["Close"] = df["Close"].astype(float)
        df["Low"] = df["Low"].astype(float)

        min_data_points = self._config["analysis"]["min_data_points"]
        if len(df) < min_data_points:
            logging.warning(f"Insufficient data points ({len(df)}) for {symbol_pair} for meaningful analysis.")
            return None

        rsi_series = self._calculate_rsi(df)
        if rsi_series is not None:
            df["RSI"] = rsi_series

        self._calculate_emas(df)

        macd_line, signal_line = self._calculate_macd(df)
        if macd_line is not None and signal_line is not None:
            df["MACD_Line"] = macd_line
            df["Signal_Line"] = signal_line
            df["MACD_Histogram"] = df["MACD_Line"] - df["Signal_Line"]

        support_levels = self._find_swing_lows(df["Low"].astype(float))

        last = df.iloc[-1]
        return {
            "symbol": symbol_pair,
            "close": f"{last.get('Close', 0):.2f}",
            "rsi": f"{last.get('RSI', 0):.2f}" if "RSI" in last else "N/A",
            "ema_10": f"{last.get('EMA_10', 0):.2f}" if "EMA_10" in last else "N/A",
            "ema_21": f"{last.get('EMA_21', 0):.2f}" if "EMA_21" in last else "N/A",
            "ema_50": f"{last.get('EMA_50', 0):.2f}" if "EMA_50" in last else "N/A",
            "macd_line": f"{last.get('MACD_Line', 0):.4f}" if "MACD_Line" in last else "N/A",
            "signal_line": f"{last.get('Signal_Line', 0):.4f}" if "Signal_Line" in last else "N/A",
            "macd_histogram": f"{last.get('MACD_Histogram', 0):.4f}" if "MACD_Histogram" in last else "N/A",
            "volume": f"{last.get('Volume', 0):,.2f}",
            "support_levels": support_levels,
        }

    def calculate_and_display_indicators(self, coin_symbols: list[str]) -> None:
        """Fetches k-line data, calculates technical indicators, and displays the results.

        This method iterates through a list of cryptocurrency symbols, fetches
        their daily k-line data, and then calculates the RSI, EMAs, MACD, and
        support levels. The results are displayed using Rich console.

        Args:
            coin_symbols: A list of cryptocurrency symbols (e.g., ["BTC", "ETH"]).
        """
        indicators_data = []

        for crypto_symbol_base in coin_symbols:
            symbol_pair = f"{crypto_symbol_base.upper()}USDT"
            logging.info(f"\nProcessing {symbol_pair}...")

            kline_data = self._client.get_klines(symbol=symbol_pair, interval="1d", limit=100)
            if not kline_data:
                self._console.print(f"[yellow]No kline data fetched for {symbol_pair}. Skipping.[/yellow]")
                continue

            df: DataFrame = pd.DataFrame(
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
            df.dropna(subset=["Open", "High", "Low", "Close", "Volume"], inplace=True)

            # Ensure correct data types for calculation
            df["Close"] = df["Close"].astype(float)
            df["Low"] = df["Low"].astype(float)

            # Use a config value to determine required data length
            min_data_points = self._config["analysis"]["min_data_points"]
            if len(df) < min_data_points:
                self._console.print(f"[yellow]Insufficient data points ({len(df)}) for {symbol_pair} for meaningful analysis.[/yellow]")
                continue

            rsi_series = self._calculate_rsi(df)
            if rsi_series is not None:
                df["RSI"] = rsi_series
            self._calculate_emas(df)
            macd_line, signal_line = self._calculate_macd(df)
            if macd_line is not None and signal_line is not None:
                df["MACD_Line"] = macd_line
                df["Signal_Line"] = signal_line
                df["MACD_Histogram"] = df["MACD_Line"] - df["Signal_Line"]
            support_levels = self._find_swing_lows(df["Low"].astype(float))

            # Collect data for display
            indicators_data.append(self._extract_indicator_data(df, symbol_pair, support_levels))

        # Display all indicators in a structured table
        if indicators_data:
            self._display_indicators_table(indicators_data)
        else:
            self._console.print("[yellow]No indicators data to display.[/yellow]")

    def _calculate_rsi(self, df: pd.DataFrame) -> Series[float] | None:
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
        delta = df["Close"].astype(float).diff()
        gain: Series[float] = (delta.where(delta > 0, 0)).ewm(com=window - 1, adjust=False).mean()
        loss: Series[float] = (-delta.where(delta < 0, 0)).ewm(com=window - 1, adjust=False).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_emas(self, df: pd.DataFrame) -> None:
        """Calculates multiple Exponential Moving Averages (EMAs).

        The periods for the EMAs are defined in the application configuration.

        Args:
            df: A DataFrame with a "Close" column. The EMA values are added
                as new columns to this DataFrame.
        """
        ema_periods = self._config["analysis"]["ema_periods"]
        for span in ema_periods:
            if len(df) >= span:
                df[f"EMA_{span}"] = df["Close"].ewm(span=span, adjust=False).mean()

    def _calculate_macd(self, df: pd.DataFrame) -> tuple[Series[float] | None, Series[float] | None]:
        """Calculates the Moving Average Convergence Divergence (MACD).

        Args:
            df: A DataFrame with a "Close" column.

        Returns:
            A tuple containing two pandas Series: the MACD line and the signal
            line. Returns (None, None) if there is not enough data.
        """
        short_window = self._config["analysis"]["ema_short_period"]
        long_window = self._config["analysis"]["ema_long_period"]
        signal_window = self._config["analysis"]["ema_signal_period"]

        if len(df) < long_window:
            return None, None

        ema_short = df["Close"].ewm(span=short_window, adjust=False).mean()
        ema_long = df["Close"].ewm(span=long_window, adjust=False).mean()
        macd_line = ema_short - ema_long
        signal_line = macd_line.ewm(span=signal_window, adjust=False).mean()
        return macd_line, signal_line

    def _find_swing_lows(self, low_series: Series[float], window: int = 2) -> list[float]:
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
        lows = []
        # Ensure the series is float for comparison
        low_series = low_series.astype(float)
        start_index = max(window, len(low_series) - 50)
        end_index = len(low_series) - window
        for i in range(start_index, end_index):
            is_swing_low = low_series.iloc[i] < low_series.iloc[i - window : i].min() and low_series.iloc[i] < low_series.iloc[i + 1 : i + window + 1].min()
            if is_swing_low:
                lows.append(low_series.iloc[i])
        return sorted(list(set(lows)))

    def _extract_indicator_data(self, df: pd.DataFrame, symbol_pair: str, support_levels: list[float]) -> dict[str, Any]:
        """Extracts indicator data from DataFrame for display."""
        last = df.iloc[-1]
        return {
            "symbol": symbol_pair,
            "close": f"{last.get('Close', 0):.2f}",
            "volume": f"{last.get('Volume', 0):,.0f}",
            "rsi": f"{last.get('RSI', 0):.2f}" if "RSI" in last and pd.notna(last.get("RSI")) else "N/A",
            "ema_10": f"{last.get('EMA_10', 0):.2f}" if "EMA_10" in last and pd.notna(last.get("EMA_10")) else "N/A",
            "ema_21": f"{last.get('EMA_21', 0):.2f}" if "EMA_21" in last and pd.notna(last.get("EMA_21")) else "N/A",
            "ema_50": f"{last.get('EMA_50', 0):.2f}" if "EMA_50" in last and pd.notna(last.get("EMA_50")) else "N/A",
            "macd_line": f"{last.get('MACD_Line', 0):.4f}" if "MACD_Line" in last and pd.notna(last.get("MACD_Line")) else "N/A",
            "signal_line": f"{last.get('Signal_Line', 0):.4f}" if "Signal_Line" in last and pd.notna(last.get("Signal_Line")) else "N/A",
            "macd_histogram": f"{last.get('MACD_Histogram', 0):.4f}" if "MACD_Histogram" in last and pd.notna(last.get("MACD_Histogram")) else "N/A",
            "support_levels": ", ".join([f"{level:.2f}" for level in support_levels]) if support_levels else "None",
        }

    def _display_indicators_table(self, indicators_data: list[dict[str, Any]]) -> None:
        """Displays technical indicators in a structured Rich table."""
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
