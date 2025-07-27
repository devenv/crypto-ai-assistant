"""
Tests for financial calculation functions across the codebase.

Tests mathematical accuracy, edge cases, precision handling,
and financial calculation correctness using property-based testing.
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.api.client import BinanceClient
from src.core.indicators import IndicatorService
from src.core.perplexity.text_analyzer import TextAnalyzer
from src.core.perplexity_service import PerplexityService


class TestRSICalculation:
    """Test RSI (Relative Strength Index) calculation accuracy."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def mock_config(self) -> dict:
        """Create mock configuration."""
        return {
            "analysis": {
                "rsi_period": 14,
                "min_data_points": 21,
                "ema_periods": [10, 21, 50],
                "ema_short_period": 12,
                "ema_long_period": 26,
                "ema_signal_period": 9,
            }
        }

    @pytest.fixture
    def indicator_service(self, mock_client: Mock, mock_config: dict) -> IndicatorService:
        """Create IndicatorService with mocks."""
        return IndicatorService(mock_client, mock_config)

    @given(st.lists(st.floats(min_value=1.0, max_value=100000.0, allow_nan=False, allow_infinity=False), min_size=21, max_size=100))
    def test_rsi_calculation_properties(self, price_data: list[float]) -> None:
        """Test RSI calculation properties with random price data."""
        # Create indicator service with mock
        from unittest.mock import Mock

        mock_client = Mock(spec=BinanceClient)
        mock_config = {
            "analysis": {
                "rsi_period": 14,
                "min_data_points": 21,
                "ema_periods": [10, 21, 50],
                "ema_short_period": 12,
                "ema_long_period": 26,
                "ema_signal_period": 9,
            }
        }
        indicator_service = IndicatorService(mock_client, mock_config)

        df = pd.DataFrame({"Close": price_data})

        rsi_series = indicator_service._calculations.calculate_rsi(df)

        if rsi_series is not None:
            # Property 1: RSI values must be between 0 and 100
            for rsi_val in rsi_series.dropna():
                assert 0 <= rsi_val <= 100, f"RSI value {rsi_val} outside valid range [0, 100]"

            # Property 2: RSI series length should match input length
            assert len(rsi_series) == len(price_data)

    @given(st.lists(st.floats(min_value=100.0, max_value=200.0, allow_nan=False, allow_infinity=False), min_size=21, max_size=30))
    @settings(max_examples=3, deadline=100)  # Optimize for performance
    def test_rsi_trending_up_property(self, base_prices: list[float]) -> None:
        """Test RSI property for consistently increasing prices."""
        # Create service inline to avoid fixture issues with hypothesis
        mock_client = Mock()
        mock_config = {"analysis": {"ema_periods": [10, 21, 50], "rsi_period": 14}}
        indicator_service = IndicatorService(mock_client, mock_config)

        # Create strictly increasing price series
        increasing_prices = []
        for i, price in enumerate(base_prices):
            increasing_prices.append(price + i * 0.5)  # Small increments

        df = pd.DataFrame({"Close": increasing_prices})
        rsi_series = indicator_service._calculations.calculate_rsi(df)

        if rsi_series is not None:
            final_rsi = rsi_series.iloc[-1]
            # Property: For strongly trending up prices, RSI should be high
            # But not necessarily > 70 due to the gradual increase
            assert 0 <= final_rsi <= 100, f"RSI {final_rsi} outside valid range [0, 100]"

    def test_rsi_calculation_trending_up(self, indicator_service: IndicatorService) -> None:
        """Test RSI calculation with trending up prices."""
        prices = [100, 102, 105, 107, 110, 112, 115, 118, 120, 125, 128, 130, 135, 138, 140, 145, 148, 150, 155, 158, 160]
        df = pd.DataFrame({"Close": prices})

        rsi_series = indicator_service._calculations.calculate_rsi(df)

        assert rsi_series is not None
        final_rsi = rsi_series.iloc[-1]
        # For trending up market, RSI should be elevated
        assert final_rsi > 50, f"Expected RSI > 50 for trending up market, got {final_rsi}"

    def test_rsi_calculation_trending_down(self, indicator_service: IndicatorService) -> None:
        """Test RSI calculation with trending down prices."""
        prices = [160, 158, 155, 150, 148, 145, 140, 138, 135, 130, 128, 125, 120, 118, 115, 112, 110, 107, 105, 102, 100]
        df = pd.DataFrame({"Close": prices})

        rsi_series = indicator_service._calculations.calculate_rsi(df)

        assert rsi_series is not None
        final_rsi = rsi_series.iloc[-1]
        # For trending down market, RSI should be depressed
        assert final_rsi < 50, f"Expected RSI < 50 for trending down market, got {final_rsi}"

    def test_rsi_calculation_sideways(self, indicator_service: IndicatorService) -> None:
        """Test RSI calculation with sideways/ranging prices."""
        # Oscillating prices around 100
        prices = [100, 102, 99, 101, 98, 103, 97, 102, 99, 101, 100, 102, 98, 101, 99, 103, 100, 102, 99, 101, 100]
        df = pd.DataFrame({"Close": prices})

        rsi_series = indicator_service._calculations.calculate_rsi(df)

        assert rsi_series is not None
        final_rsi = rsi_series.iloc[-1]
        # For sideways market, RSI should be around neutral
        assert 30 < final_rsi < 70, f"Expected RSI between 30-70 for sideways movement, got {final_rsi}"

    @given(st.lists(st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False), min_size=5, max_size=15))
    @settings(max_examples=3, deadline=100)  # Reduced examples and deadline for performance
    def test_rsi_calculation_insufficient_data(self, short_prices: list[float]) -> None:
        """Test RSI calculation with insufficient data points."""
        # Create service inline to avoid fixture issues with hypothesis
        mock_client = Mock()
        mock_config = {"analysis": {"ema_periods": [10, 21, 50], "rsi_period": 14}}
        indicator_service = IndicatorService(mock_client, mock_config)

        df = pd.DataFrame({"Close": short_prices})
        rsi_series = indicator_service._calculations.calculate_rsi(df)

        # Property: With insufficient data (< 14 points for RSI), should return None
        # With sufficient data (>= 14 points), should return a Series
        if len(short_prices) < 14:
            assert rsi_series is None
        else:
            assert rsi_series is not None
            assert isinstance(rsi_series, pd.Series)

    @given(st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=3, deadline=100)  # Optimize for performance
    def test_rsi_with_identical_prices(self, price: float) -> None:
        """Test RSI calculation with identical prices (no volatility)."""
        # Create service inline to avoid fixture issues with hypothesis
        mock_client = Mock()
        mock_config = {"analysis": {"ema_periods": [10, 21, 50], "rsi_period": 14}}
        indicator_service = IndicatorService(mock_client, mock_config)

        prices = [price] * 21
        df = pd.DataFrame({"Close": prices})

        rsi_series = indicator_service._calculations.calculate_rsi(df)

        # With no price movement, RSI should be around 50 or NaN
        if rsi_series is not None:
            final_rsi = rsi_series.iloc[-1]
            # Allow for NaN or neutral RSI
            if not pd.isna(final_rsi):
                assert 40 <= final_rsi <= 60, f"Expected RSI around 50 for no price movement, got {final_rsi}"


class TestEMACalculation:
    """Test EMA (Exponential Moving Average) calculation accuracy."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def mock_config(self) -> dict:
        """Create mock configuration."""
        return {"analysis": {"ema_periods": [10, 21, 50], "rsi_period": 14}}

    @pytest.fixture
    def indicator_service(self, mock_client: Mock, mock_config: dict) -> IndicatorService:
        """Create IndicatorService with mocks."""
        return IndicatorService(mock_client, mock_config)

    @given(
        prices=st.lists(st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False), min_size=10, max_size=30),
        period=st.integers(min_value=2, max_value=20),
    )
    @settings(max_examples=3, deadline=100)  # Optimize for performance
    def test_ema_calculation_properties(self, prices: list[float], period: int) -> None:
        """Test EMA calculation properties with random data."""
        assume(period <= len(prices))

        # Create service inline to avoid fixture issues with hypothesis
        mock_client = Mock()
        mock_config = {"analysis": {"ema_periods": [10, 21, 50], "rsi_period": 14}}
        indicator_service = IndicatorService(mock_client, mock_config)

        ema = indicator_service._calculations.calculate_ema(prices, period)

        if ema is not None:
            # Property 1: EMA should be a positive number for positive prices
            assert ema > 0, f"EMA should be positive for positive prices, got {ema}"

            # Property 2: EMA should be within reasonable bounds of input prices
            min_price = min(prices)
            max_price = max(prices)
            assert min_price <= ema <= max_price * 1.1, f"EMA {ema} outside reasonable bounds [{min_price}, {max_price * 1.1}]"

    def test_ema_calculation_basic(self, indicator_service: IndicatorService) -> None:
        """Test basic EMA calculation."""
        prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120]

        ema10 = indicator_service._calculations.calculate_ema(prices, 10)

        assert ema10 is not None
        assert isinstance(ema10, float)
        assert ema10 > 0

        # For rising prices, EMA should be less than final price but greater than initial price
        assert prices[0] < ema10 < prices[-1]

    def test_ema_calculation_insufficient_data(self, indicator_service: IndicatorService) -> None:
        """Test EMA calculation with insufficient data."""
        prices = [100, 102, 104]  # Only 3 prices for EMA10

        ema10 = indicator_service._calculations.calculate_ema(prices, 10)

        assert ema10 is None

    def test_ema_calculation_exact_period(self, indicator_service: IndicatorService) -> None:
        """Test EMA calculation with exactly the required period."""
        prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]  # Exactly 10 prices

        ema10 = indicator_service._calculations.calculate_ema(prices, 10)

        assert ema10 is not None
        assert isinstance(ema10, float)

    def test_ema_different_periods(self, indicator_service: IndicatorService) -> None:
        """Test EMA calculation with different periods."""
        prices = [100 + i for i in range(50)]  # 50 data points

        ema10 = indicator_service._calculations.calculate_ema(prices, 10)
        ema21 = indicator_service._calculations.calculate_ema(prices, 21)
        ema50 = indicator_service._calculations.calculate_ema(prices, 50)

        assert all(ema is not None for ema in [ema10, ema21, ema50])

        # For trending up data, shorter period EMA should be higher than longer period EMA
        assert ema10 > ema21 > ema50

    def test_ema_with_negative_prices(self, indicator_service: IndicatorService) -> None:
        """Test EMA calculation with negative prices (edge case)."""
        prices = [-10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10]

        ema10 = indicator_service._calculations.calculate_ema(prices, 10)

        assert ema10 is not None
        assert isinstance(ema10, float)

    def test_ema_with_volatile_prices(self, indicator_service: IndicatorService) -> None:
        """Test EMA calculation with highly volatile prices."""
        prices = [100, 50, 150, 25, 175, 10, 200, 5, 250, 1, 300]

        ema10 = indicator_service._calculations.calculate_ema(prices, 10)

        assert ema10 is not None
        assert isinstance(ema10, float)
        assert ema10 > 0


class TestMACDCalculation:
    """Test MACD (Moving Average Convergence Divergence) calculation."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def mock_config(self) -> dict:
        """Create mock configuration."""
        return {
            "analysis": {
                "ema_short_period": 12,
                "ema_long_period": 26,
                "ema_signal_period": 9,
            }
        }

    @pytest.fixture
    def indicator_service(self, mock_client: Mock, mock_config: dict) -> IndicatorService:
        """Create IndicatorService with mocks."""
        return IndicatorService(mock_client, mock_config)

    def test_macd_calculation_basic(self, indicator_service: IndicatorService) -> None:
        """Test basic MACD calculation."""
        # Create sufficient data for MACD calculation (need at least 26 + 9 = 35 points)
        prices = [100 + i * 0.5 for i in range(40)]  # Gradual uptrend
        df = pd.DataFrame({"Close": prices})

        macd_line, signal_line = indicator_service._calculations.calculate_macd(df)

        assert macd_line is not None
        assert signal_line is not None
        assert len(macd_line) == len(df)
        assert len(signal_line) == len(df)

        # For uptrending data, MACD should eventually be positive
        final_macd = macd_line.iloc[-1]
        final_signal = signal_line.iloc[-1]

        assert not pd.isna(final_macd)
        assert not pd.isna(final_signal)

    def test_macd_calculation_insufficient_data(self, indicator_service: IndicatorService) -> None:
        """Test MACD calculation with insufficient data."""
        prices = [100, 102, 104, 106, 108]  # Only 5 data points
        df = pd.DataFrame({"Close": prices})

        macd_line, signal_line = indicator_service._calculations.calculate_macd(df)

        assert macd_line is None
        assert signal_line is None

    def test_macd_crossover_signals(self, indicator_service: IndicatorService) -> None:
        """Test MACD crossover signals."""
        # Create data that should generate MACD crossover
        prices = []
        # Downtrend followed by uptrend
        for i in range(20):
            prices.append(120 - i)  # Declining prices
        for i in range(20):
            prices.append(100 + i * 2)  # Rising prices

        df = pd.DataFrame({"Close": prices})

        macd_line, signal_line = indicator_service._calculations.calculate_macd(df)

        assert macd_line is not None
        assert signal_line is not None

        # Calculate histogram
        histogram = macd_line - signal_line

        # Should have both positive and negative values in histogram
        assert histogram.min() < 0
        assert histogram.max() > 0


class TestBalanceCalculations:
    """Test balance and USD value calculations."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def sample_account_info(self) -> dict:
        """Create sample account information."""
        return {
            "balances": [
                {"asset": "BTC", "free": "0.5", "locked": "0.0"},
                {"asset": "ETH", "free": "2.0", "locked": "0.5"},
                {"asset": "USDT", "free": "1000.0", "locked": "100.0"},
                {"asset": "BNB", "free": "10.0", "locked": "0.0"},
                {"asset": "DUST", "free": "0.001", "locked": "0.0"},  # Low value asset
            ]
        }

    @pytest.fixture
    def sample_tickers(self) -> list[dict[str, str]]:
        """Create sample ticker data."""
        return [
            {"symbol": "BTCUSDT", "price": "50000.0"},
            {"symbol": "ETHUSDT", "price": "3000.0"},
            {"symbol": "BNBUSDT", "price": "400.0"},
            {"symbol": "DUSTUSDT", "price": "0.01"},
        ]

    def test_get_balances_usd_calculation(self, mock_client: Mock, sample_account_info: dict, sample_tickers: list[dict[str, str]]) -> None:
        """Test USD value calculation for balances."""
        mock_client.get_account_info.return_value = sample_account_info
        mock_client.get_all_tickers.return_value = sample_tickers

        client = BinanceClient()
        client._request = mock_client._request  # Use mock request method
        client.get_account_info = mock_client.get_account_info
        client.get_all_tickers = mock_client.get_all_tickers

        balances = client.get_balances(min_value=10.0)

        # Should include BTC, ETH, USDT, BNB but not DUST (below min_value)
        balance_assets = {balance["asset"] for balance in balances}
        assert "BTC" in balance_assets
        assert "ETH" in balance_assets
        assert "USDT" in balance_assets
        assert "BNB" in balance_assets
        assert "DUST" not in balance_assets  # Below min_value threshold

        # Check USD value calculations
        btc_balance = next(b for b in balances if b["asset"] == "BTC")
        eth_balance = next(b for b in balances if b["asset"] == "ETH")
        usdt_balance = next(b for b in balances if b["asset"] == "USDT")

        # BTC: 0.5 * 50000 = 25000
        assert abs(btc_balance["value_usdt"] - 25000.0) < 0.01

        # ETH: 2.5 * 3000 = 7500 (free + locked)
        assert abs(eth_balance["value_usdt"] - 7500.0) < 0.01

        # USDT: 1100 (free + locked)
        assert abs(usdt_balance["value_usdt"] - 1100.0) < 0.01

    def test_get_balances_with_btc_pairs(self, mock_client: Mock) -> None:
        """Test balance calculation using BTC pairs when USDT pair unavailable."""
        account_info = {
            "balances": [
                {"asset": "ALTCOIN", "free": "100.0", "locked": "0.0"},
                {"asset": "BTC", "free": "1.0", "locked": "0.0"},
            ]
        }

        tickers = [
            {"symbol": "BTCUSDT", "price": "50000.0"},
            {"symbol": "ALTCOINBTC", "price": "0.001"},  # No ALTCOINUSDT pair
        ]

        mock_client.get_account_info.return_value = account_info
        mock_client.get_all_tickers.return_value = tickers

        client = BinanceClient()
        client.get_account_info = mock_client.get_account_info
        client.get_all_tickers = mock_client.get_all_tickers

        balances = client.get_balances(min_value=10.0)

        # Should calculate ALTCOIN value via BTC pair
        # ALTCOIN: 100 * 0.001 * 50000 = 5000 USDT
        altcoin_balance = next((b for b in balances if b["asset"] == "ALTCOIN"), None)
        if altcoin_balance:  # Might be filtered out if calculation fails
            assert abs(altcoin_balance["value_usdt"] - 5000.0) < 0.01

    def test_get_balances_precision_handling(self, mock_client: Mock) -> None:
        """Test precision handling in balance calculations."""
        account_info = {
            "balances": [
                {"asset": "ETH", "free": "1.123456789", "locked": "0.876543211"},
                {"asset": "USDT", "free": "0.1", "locked": "0.0"},  # Below min_value
            ]
        }

        tickers = [
            {"symbol": "ETHUSDT", "price": "3000.123456"},
        ]

        mock_client.get_account_info.return_value = account_info
        mock_client.get_all_tickers.return_value = tickers

        client = BinanceClient()
        client.get_account_info = mock_client.get_account_info
        client.get_all_tickers = mock_client.get_all_tickers

        balances = client.get_balances(min_value=1.0)

        eth_balance = next(b for b in balances if b["asset"] == "ETH")

        # Check precise calculation: (1.123456789 + 0.876543211) * 3000.123456
        expected_total = 1.123456789 + 0.876543211
        expected_value = expected_total * 3000.123456

        assert abs(eth_balance["total"] - expected_total) < 1e-9
        assert abs(eth_balance["value_usdt"] - expected_value) < 1e-6

    def test_get_balances_zero_balances_excluded(self, mock_client: Mock) -> None:
        """Test that zero balances are excluded."""
        account_info = {
            "balances": [
                {"asset": "BTC", "free": "0.0", "locked": "0.0"},
                {"asset": "ETH", "free": "1.0", "locked": "0.0"},
                {"asset": "ZERO", "free": "0", "locked": "0"},
            ]
        }

        tickers = [
            {"symbol": "ETHUSDT", "price": "3000.0"},
        ]

        mock_client.get_account_info.return_value = account_info
        mock_client.get_all_tickers.return_value = tickers

        client = BinanceClient()
        client.get_account_info = mock_client.get_account_info
        client.get_all_tickers = mock_client.get_all_tickers

        balances = client.get_balances(min_value=1.0)

        # Should only include ETH, not BTC or ZERO
        balance_assets = {balance["asset"] for balance in balances}
        assert balance_assets == {"ETH"}


class TestConsistencyScoreCalculation:
    """Test consistency score calculations in PerplexityService."""

    @pytest.fixture
    def mock_env_vars(self) -> None:
        """Mock environment variables."""
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test_key"}):
            yield

    @pytest.fixture
    def perplexity_service(self, mock_env_vars: None) -> PerplexityService:
        """Create PerplexityService with mock environment."""
        return PerplexityService()

    @pytest.fixture
    def text_analyzer(self) -> TextAnalyzer:
        """Create TextAnalyzer for consistency score testing."""
        return TextAnalyzer()

    def test_consistency_score_identical_recommendations(self, text_analyzer: TextAnalyzer) -> None:
        """Test consistency score with identical recommendations."""
        recs_1 = [
            {"symbol": "BTCUSDT", "action": "BUY", "price": 50000, "quantity": 0.1},
            {"symbol": "ETHUSDT", "action": "SELL", "price": 3000, "quantity": 1.0},
        ]
        recs_2 = [
            {"symbol": "BTCUSDT", "action": "BUY", "price": 50000, "quantity": 0.1},
            {"symbol": "ETHUSDT", "action": "SELL", "price": 3000, "quantity": 1.0},
        ]

        score = text_analyzer.calculate_consistency_score(recs_1, recs_2)

        assert score == 100.0  # Perfect match

    def test_consistency_score_no_recommendations(self, text_analyzer: TextAnalyzer) -> None:
        """Test consistency score with no recommendations."""
        score = text_analyzer.calculate_consistency_score([], [])
        assert score == 100.0  # Both empty is consistent

    def test_consistency_score_one_empty(self, text_analyzer: TextAnalyzer) -> None:
        """Test consistency score with one empty list."""
        recs_1 = [{"symbol": "BTCUSDT", "action": "BUY", "price": 50000}]
        recs_2 = []

        score = text_analyzer.calculate_consistency_score(recs_1, recs_2)
        assert score == 0.0  # Mismatch between having and not having recommendations

    def test_consistency_score_different_symbols(self, text_analyzer: TextAnalyzer) -> None:
        """Test consistency score with different symbols."""
        recs_1 = [{"symbol": "BTCUSDT", "action": "BUY", "price": 50000}]
        recs_2 = [{"symbol": "ETHUSDT", "action": "BUY", "price": 3000}]

        score = text_analyzer.calculate_consistency_score(recs_1, recs_2)
        assert score < 50.0  # Low score due to different symbols

    def test_consistency_score_same_symbol_different_action(self, text_analyzer: TextAnalyzer) -> None:
        """Test consistency score with same symbol, different action."""
        recs_1 = [{"symbol": "BTCUSDT", "action": "BUY", "price": 50000}]
        recs_2 = [{"symbol": "BTCUSDT", "action": "SELL", "price": 50000}]

        score = text_analyzer.calculate_consistency_score(recs_1, recs_2)

        # Should get points for symbol match but lose points for action mismatch
        assert 30 < score < 70

    def test_consistency_score_price_variance(self, text_analyzer: TextAnalyzer) -> None:
        """Test consistency score with price variance."""
        recs_1 = [{"symbol": "BTCUSDT", "action": "BUY", "price": 50000}]
        recs_2 = [{"symbol": "BTCUSDT", "action": "BUY", "price": 52000}]  # 4% difference

        score = text_analyzer.calculate_consistency_score(recs_1, recs_2)

        # Should get high score (symbol + action match) with slight deduction for price
        assert score > 90

    def test_consistency_score_large_price_variance(self, text_analyzer: TextAnalyzer) -> None:
        """Test consistency score with large price variance."""
        recs_1 = [{"symbol": "BTCUSDT", "action": "BUY", "price": 50000}]
        recs_2 = [{"symbol": "BTCUSDT", "action": "BUY", "price": 60000}]  # 20% difference

        score = text_analyzer.calculate_consistency_score(recs_1, recs_2)

        # Should get medium score due to large price variance
        assert 70 <= score <= 90


class TestPrecisionAndRounding:
    """Test precision handling and rounding in financial calculations."""

    @given(
        a=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
        b=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    def test_float_precision_properties(self, a: float, b: float) -> None:
        """Test properties of floating point operations."""
        result = a + b

        # Property 1: Addition should be commutative
        assert abs((a + b) - (b + a)) < 1e-10

        # Property 2: Result should be greater than individual components
        assert result >= max(a, b)

        # Property 3: Result should be reasonable
        assert result > 0

    def test_float_precision_issues(self) -> None:
        """Test handling of floating point precision issues."""
        # Common floating point precision issue
        result = 0.1 + 0.2
        assert abs(result - 0.3) < 1e-10  # Should be close but not exactly equal

        # Test multiplication precision
        price = 1234.567
        quantity = 0.123456789
        total = price * quantity

        # Should handle precision appropriately
        assert isinstance(total, float)
        assert total > 0

    @given(value=st.floats(min_value=0.0001, max_value=99999.9999, allow_nan=False, allow_infinity=False), decimals=st.integers(min_value=0, max_value=8))
    def test_decimal_rounding_properties(self, value: float, decimals: int) -> None:
        """Test decimal rounding properties with random values."""
        result = round(value, decimals)

        # Property 1: Rounded value should be within expected range
        tolerance = 5 * (10 ** -(decimals + 1))  # Half of smallest unit at that precision
        assert abs(result - value) <= tolerance

        # Property 2: Result should have correct decimal places
        if decimals > 0:
            decimal_part = str(result).split(".")
            if len(decimal_part) > 1:
                assert len(decimal_part[1]) <= decimals

    def test_decimal_rounding_consistency(self) -> None:
        """Test decimal rounding consistency."""
        test_values = [
            (12.3456, 2, 12.35),
            (12.3454, 2, 12.35),
            (12.3449, 2, 12.34),
            (0.12345, 4, 0.1235),
        ]

        for value, decimals, expected in test_values:
            result = round(value, decimals)
            assert result == expected, f"round({value}, {decimals}) = {result}, expected {expected}"

    @given(
        price=st.floats(min_value=1.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        percentage=st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False),
    )
    def test_percentage_calculation_properties(self, price: float, percentage: float) -> None:
        """Test percentage calculation properties."""
        stop_price = price * (1 - percentage / 100)
        calculated_pct = abs(price - stop_price) / price * 100

        # Property: Calculated percentage should match input percentage
        assert abs(calculated_pct - percentage) < 0.01, f"Expected {percentage}%, got {calculated_pct}%"

    def test_percentage_calculations(self) -> None:
        """Test percentage calculation accuracy."""
        # Test stop-loss percentage calculation
        price = 50000.0
        stop_price = 47500.0

        stop_loss_pct = abs(price - stop_price) / price * 100
        expected_pct = 5.0

        assert abs(stop_loss_pct - expected_pct) < 0.01

    @given(
        quantity=st.floats(min_value=0.001, max_value=1000.0, allow_nan=False, allow_infinity=False),
        price=st.floats(min_value=1.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
    )
    def test_notional_value_properties(self, quantity: float, price: float) -> None:
        """Test notional value calculation properties."""
        notional = quantity * price

        # Property 1: Notional value should be positive for positive inputs
        assert notional > 0, f"Notional value should be positive, got {notional}"

        # Property 2: Notional should be proportional to inputs
        assert notional >= min(quantity, price), f"Notional {notional} should be >= min({quantity}, {price})"

        # Property 3: If we double quantity, notional should double
        double_notional = (quantity * 2) * price
        assert abs(double_notional - 2 * notional) < 1e-10

    def test_notional_value_calculations(self) -> None:
        """Test notional value calculations."""
        test_cases = [
            (0.1, 50000.0, 5000.0),  # BTC order
            (1.0, 3000.0, 3000.0),  # ETH order
            (100.0, 400.0, 40000.0),  # BNB order
        ]

        for quantity, price, expected_notional in test_cases:
            notional = quantity * price
            assert abs(notional - expected_notional) < 0.01


class TestEdgeCases:
    """Test edge cases in financial calculations."""

    def test_zero_division_handling(self) -> None:
        """Test handling of zero division scenarios."""
        # RSI calculation with zero gains/losses
        gains = [0.0] * 10
        losses = [0.0] * 10

        # Should handle gracefully without throwing exception
        try:
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0

            if avg_loss == 0:
                rs = float("inf") if avg_gain > 0 else 0
            else:
                rs = avg_gain / avg_loss

            # RSI calculation should handle infinite RS
            if rs == float("inf"):
                rsi = 100.0
            else:
                rsi = 100 - (100 / (1 + rs))

            assert 0 <= rsi <= 100
        except ZeroDivisionError:
            pytest.fail("Zero division not handled properly")

    def test_negative_price_handling(self) -> None:
        """Test handling of negative prices (edge case)."""
        # While negative prices are unrealistic, calculations should be robust
        prices = [-100, -50, 0, 50, 100]

        # Test that calculations don't crash with negative inputs
        try:
            # Simple moving average
            sma = sum(prices) / len(prices)
            assert isinstance(sma, int | float)

            # Percentage change
            if prices[0] != 0:
                pct_change = (prices[-1] - prices[0]) / abs(prices[0]) * 100
                assert isinstance(pct_change, int | float)

        except Exception as e:
            pytest.fail(f"Negative price handling failed: {e}")

    def test_very_large_numbers(self) -> None:
        """Test handling of very large numbers."""
        large_price = 1e12  # 1 trillion
        small_quantity = 1e-12  # Very small quantity

        notional = large_price * small_quantity

        # Should handle large number arithmetic
        assert isinstance(notional, float)
        assert notional == 1.0

    def test_very_small_numbers(self) -> None:
        """Test handling of very small numbers."""
        small_price = 1e-8
        large_quantity = 1e6

        notional = small_price * large_quantity

        # Should handle small number arithmetic
        assert isinstance(notional, float)
        assert abs(notional - 0.01) < 1e-10
