"""
Comprehensive error handling tests for core modules using property-based testing.

Tests various error scenarios including API failures, network issues,
validation errors, and error recovery mechanisms.
"""

from unittest.mock import Mock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from requests.exceptions import ConnectionError, Timeout

from api.exceptions import (
    APIError,
    BinanceException,
    PerplexityAPIError,
    PerplexityAuthenticationError,
    PerplexityModelError,
    PerplexityRateLimitError,
    PerplexityServerError,
    PerplexityTimeoutError,
)
from src.api.client import BinanceClient
from src.api.enums import OrderSide, OrderType
from src.core.account import AccountService
from src.core.indicators import IndicatorService
from src.core.order_validator import OrderValidator
from src.core.orders import OrderErrorHandler, OrderService
from src.core.perplexity_service import PerplexityService


@pytest.fixture
def mock_env_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture to set up environment with valid API key."""
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test_perplexity_key")


@pytest.fixture
def perplexity_service(mock_env_with_key: None) -> PerplexityService:
    """Fixture to create a PerplexityService instance."""
    return PerplexityService()


class TestAccountServiceErrorHandling:
    """Test error handling in AccountService."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def account_service(self, mock_client: Mock) -> AccountService:
        """Create AccountService with mock client."""
        return AccountService(mock_client)

    @given(st.text(min_size=1, max_size=100))
    def test_get_account_info_api_error_properties(self, error_message: str) -> None:
        """Test account info API error handling with random error messages."""
        # Create inline mocks to avoid fixture issues with hypothesis
        mock_client = Mock()
        mock_client.get_account_info.side_effect = BinanceException(error_message, code=-1000)
        account_service = AccountService(mock_client)

        result = account_service.get_account_info()

        # Property: Should always return None on API error
        assert result is None, f"Should return None on API error, got {result}"

    @given(
        st.lists(
            st.dictionaries(
                keys=st.sampled_from(["asset", "free", "locked"]),
                values=st.one_of(
                    st.none(),  # None values
                    st.text(min_size=0, max_size=5),  # Empty or short strings
                    st.integers(min_value=-100, max_value=100),  # Invalid types
                    st.floats(allow_nan=True, allow_infinity=True),  # Invalid floats
                ),
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_process_balances_invalid_data_properties(self, invalid_balances: list[dict]) -> None:
        """Test balance processing with various invalid data structures."""
        # Create inline mocks to avoid fixture issues with hypothesis
        mock_client = Mock()
        account_service = AccountService(mock_client)
        mock_client.get_account_info.return_value = {"balances": invalid_balances}
        mock_client.get_all_tickers.return_value = []

        result = account_service.get_account_info()

        # Property: Should handle invalid data gracefully (return None or valid structure)
        if result is not None:
            assert isinstance(result, dict), f"Result should be dict or None, got {type(result)}"
            if "balances" in result:
                assert isinstance(result["balances"], list), "Balances should be a list"

    def test_get_account_info_api_error(self, account_service: AccountService, mock_client: Mock) -> None:
        """Test get_account_info when API call fails."""
        mock_client.get_account_info.side_effect = BinanceException("API Error", code=-1000)

        result = account_service.get_account_info()
        assert result is None

    def test_get_account_info_empty_response(self, account_service: AccountService, mock_client: Mock) -> None:
        """Test get_account_info with empty API response."""
        mock_client.get_account_info.return_value = None

        result = account_service.get_account_info()
        assert result is None

    def test_get_account_info_malformed_balances(self, account_service: AccountService, mock_client: Mock) -> None:
        """Test get_account_info with malformed balance data."""
        mock_client.get_account_info.return_value = {"balances": [{"asset": "BTC"}]}  # Missing free/locked
        mock_client.get_all_tickers.return_value = []

        result = account_service.get_account_info()
        assert result is not None  # Returns malformed data, validation happens in format_account_display
        assert result == {"balances": [{"asset": "BTC"}]}

    def test_get_account_info_ticker_api_error(self, account_service: AccountService, mock_client: Mock) -> None:
        """Test get_account_info when ticker API call fails (should not affect get_account_info)."""
        mock_client.get_account_info.return_value = {"balances": [{"asset": "BTC", "free": "1.0", "locked": "0.0"}]}
        mock_client.get_all_tickers.side_effect = BinanceException("Ticker API Error", code=-1000)

        result = account_service.get_account_info()
        assert result is not None  # get_account_info doesn't call ticker API
        assert result == {"balances": [{"asset": "BTC", "free": "1.0", "locked": "0.0"}]}


class TestIndicatorServiceErrorHandling:
    """Test error handling in IndicatorService."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def mock_config(self) -> dict:
        """Create mock configuration."""
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
    def indicator_service(self, mock_client: Mock, mock_config: dict) -> IndicatorService:
        """Create IndicatorService with mocks."""
        return IndicatorService(mock_client, mock_config)

    @given(
        st.lists(
            st.one_of(
                st.none(),
                st.text(max_size=5),
                st.integers(),
                st.floats(allow_nan=True, allow_infinity=True),
                st.dictionaries(keys=st.text(max_size=3), values=st.integers()),
            ),
            min_size=0,
            max_size=10,
        )
    )
    @settings(max_examples=3, deadline=100)  # Optimize for performance
    def test_calculate_indicators_invalid_symbols_properties(self, invalid_symbols: list) -> None:
        """Test calculate_indicators with various invalid symbol types."""
        # Create service inline to avoid fixture issues with hypothesis
        mock_client = Mock()
        mock_config = {"analysis": {"ema_periods": [10, 21, 50], "rsi_period": 14, "ema_short_period": 12, "ema_long_period": 26, "ema_signal_period": 9}}
        indicator_service = IndicatorService(mock_client, mock_config)

        result = indicator_service.calculate_indicators(invalid_symbols)

        # Property: Should always return a dictionary
        assert isinstance(result, dict), f"Result should be dict, got {type(result)}"

        # Property: Should handle invalid inputs gracefully (empty result or error messages)
        if result:
            for symbol_result in result.values():
                assert isinstance(symbol_result, dict), "Each symbol result should be a dict"

    @given(
        st.lists(
            st.dictionaries(
                keys=st.sampled_from(["close", "open", "high", "low", "volume"]),
                values=st.one_of(
                    st.none(),
                    st.text(max_size=10),
                    st.floats(min_value=-1000000, max_value=1000000),
                    st.just(float("nan")),
                    st.just(float("inf")),
                    st.just(float("-inf")),
                ),
            ),
            min_size=5,
            max_size=30,
        )
    )
    def test_calculate_indicators_invalid_kline_data_properties(self, invalid_klines: list[dict]) -> None:
        """Test calculate_indicators with various invalid kline data structures."""
        # Create service inline to avoid fixture issues with hypothesis
        mock_client = Mock()
        mock_config = {"analysis": {"ema_periods": [10, 21, 50], "rsi_period": 14, "ema_short_period": 12, "ema_long_period": 26, "ema_signal_period": 9}}
        indicator_service = IndicatorService(mock_client, mock_config)
        mock_client.get_klines.return_value = invalid_klines

        result = indicator_service.calculate_indicators(["TEST"])

        # Property: Should handle invalid kline data gracefully
        assert isinstance(result, dict), f"Result should be dict, got {type(result)}"

        if "TEST" in result:
            # Should either have error or valid data structure
            test_result = result["TEST"]
            assert isinstance(test_result, dict), "Result should be a dictionary"

            # If there's an error, it should be a string
            if "error" in test_result:
                assert isinstance(test_result["error"], str), "Error should be a string"

    def test_calculate_indicators_empty_symbols(self, indicator_service: IndicatorService) -> None:
        """Test calculate_indicators with empty symbol list."""
        result = indicator_service.calculate_indicators([])
        assert result == {}

    def test_calculate_indicators_invalid_symbols(self, indicator_service: IndicatorService) -> None:
        """Test calculate_indicators with invalid symbols."""
        result = indicator_service.calculate_indicators([None, "", 123])

        # Should filter out None and empty strings, but may still process the integer
        # The integer will cause an error during processing
        assert isinstance(result, dict)
        # Allow for partial results with errors
        if result:
            for _symbol, data in result.items():
                if "error" in data:
                    assert "failed" in data["error"].lower()

    def test_calculate_indicators_api_error(self, indicator_service: IndicatorService, mock_client: Mock) -> None:
        """Test calculate_indicators when API call fails."""
        mock_client.get_klines.side_effect = BinanceException("API Error", code=-1000)

        result = indicator_service.calculate_indicators(["BTC"])

        # After refactoring, errors are collected in errors.error_list
        assert "errors" in result
        assert "error_list" in result["errors"]
        error_list = result["errors"]["error_list"]
        assert any("BTC:" in error for error in error_list)

    def test_calculate_indicators_insufficient_data(self, indicator_service: IndicatorService, mock_client: Mock) -> None:
        """Test calculate_indicators with insufficient kline data."""
        mock_client.get_klines.return_value = [
            ["1672531200000", "100", "100", "100", "100", "1000", "1672617599999", "100000", 100, "500", "50000", "0"]
        ] * 10  # Only 10 klines, need 50

        result = indicator_service.calculate_indicators(["BTC"])

        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: Insufficient data" in result["errors"]["error_list"]

    def test_calculate_indicators_invalid_price_data(self, indicator_service: IndicatorService, mock_client: Mock) -> None:
        """Test calculate_indicators with invalid price data."""
        invalid_klines = [["1672531200000", "invalid", "invalid", "invalid", "invalid", "1000", "1672617599999", "100000", 100, "500", "50000", "0"]] * 25
        mock_client.get_klines.return_value = invalid_klines

        result = indicator_service.calculate_indicators(["BTC"])

        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: Insufficient data" in result["errors"]["error_list"]

    def test_calculate_indicators_zero_prices(self, indicator_service: IndicatorService, mock_client: Mock) -> None:
        """Test calculate_indicators with zero prices."""
        zero_klines = [["1672531200000", "0", "0", "0", "0", "1000", "1672617599999", "100000", 100, "500", "50000", "0"]] * 25
        mock_client.get_klines.return_value = zero_klines

        result = indicator_service.calculate_indicators(["BTC"])

        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: Insufficient data" in result["errors"]["error_list"]

    def test_calculate_indicators_rsi_calculation_error(self, indicator_service: IndicatorService, mock_client: Mock) -> None:
        """Test calculate_indicators when RSI calculation fails."""
        # Create proper Binance klines format: [open_time, open, high, low, close, volume, close_time, ...]
        valid_klines = [
            [1672531200000 + i * 86400000, 100 + i, 101 + i, 99 + i, 100 + i, 1000, 1672617599999 + i * 86400000, 100000, 100, 500, 50000, 0] for i in range(50)
        ]
        mock_client.get_klines.return_value = valid_klines

        # Mock the RSI calculation to fail by patching the calculations component
        with patch.object(indicator_service._calculations, "calculate_rsi", side_effect=Exception("RSI calc failed")):
            result = indicator_service.calculate_indicators(["BTC"])

        # When calculation fails with exception, the symbol gets added to error list
        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: RSI calc failed" in result["errors"]["error_list"]
        assert "BTC" not in result  # Symbol is not included when there are errors

    def test_calculate_indicators_ema_calculation_error(self, indicator_service: IndicatorService, mock_client: Mock) -> None:
        """Test calculate_indicators when EMA calculation fails."""
        # Create proper Binance klines format: [open_time, open, high, low, close, volume, close_time, ...]
        valid_klines = [
            [1672531200000 + i * 86400000, 100 + i, 101 + i, 99 + i, 100 + i, 1000, 1672617599999 + i * 86400000, 100000, 100, 500, 50000, 0] for i in range(50)
        ]
        mock_client.get_klines.return_value = valid_klines

        # Mock the EMA calculation to fail by patching the calculations component
        with patch.object(indicator_service._calculations, "calculate_emas", side_effect=Exception("EMA calc failed")):
            result = indicator_service.calculate_indicators(["BTC"])

        # When calculation fails with exception, the symbol gets added to error list
        assert "errors" in result
        assert "error_list" in result["errors"]
        assert "BTC: EMA calc failed" in result["errors"]["error_list"]
        assert "BTC" not in result  # Symbol is not included when there are errors


class TestPerplexityServiceErrorHandling:
    """Test error handling in PerplexityService."""

    def test_init_missing_api_key(self) -> None:
        """Test PerplexityService initialization without API key."""
        # Patch os.getenv to return None for PERPLEXITY_API_KEY
        with patch("src.core.perplexity.service.os.getenv") as mock_getenv:
            mock_getenv.return_value = None
            with pytest.raises(PerplexityAuthenticationError):
                PerplexityService()

    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_authentication_error(self, mock_post: Mock) -> None:
        """Test handling of 401 authentication error."""
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test_key"}):
            service = PerplexityService()

        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "test"}]

        with pytest.raises(PerplexityAuthenticationError, match="Invalid API key"):
            service.call_api(messages)

    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_rate_limit_error(self, mock_post: Mock) -> None:
        """Test handling of 429 rate limit error."""
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test_key"}):
            service = PerplexityService()
            service.max_retries = 0  # Prevent recursion in test

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "60"}
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "test"}]

        with pytest.raises(PerplexityRateLimitError):
            service.call_api(messages)

    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_server_error(self, mock_post: Mock) -> None:
        """Test handling of 500 server error."""
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test_key"}):
            service = PerplexityService()
            service.max_retries = 0  # Prevent recursion in test

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "test"}]

        with pytest.raises(PerplexityServerError, match="Server error"):
            service.call_api(messages)

    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_timeout_error(self, mock_post: Mock, perplexity_service: PerplexityService) -> None:
        """Test handling of timeout error."""
        mock_post.side_effect = Timeout("Request timed out")

        messages = [{"role": "user", "content": "test"}]

        with pytest.raises(PerplexityTimeoutError):
            perplexity_service.call_api(messages)

    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_connection_error(self, mock_post: Mock, perplexity_service: PerplexityService) -> None:
        """Test handling of connection error."""
        mock_post.side_effect = ConnectionError("Network error")

        messages = [{"role": "user", "content": "test"}]

        with pytest.raises(PerplexityAPIError, match="Connection error"):
            perplexity_service.call_api(messages)

    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_model_error(self, mock_post: Mock, perplexity_service: PerplexityService) -> None:
        """Test handling of model-related 400 error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Invalid model specified"}}
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "test"}]

        with pytest.raises(PerplexityModelError, match="Model error"):
            perplexity_service.call_api(messages)

    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_retry_mechanism(self, mock_post: Mock, perplexity_service: PerplexityService) -> None:
        """Test retry mechanism on server errors."""
        # First call fails with server error, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Server error"

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"choices": [{"message": {"content": "success"}}]}

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        messages = [{"role": "user", "content": "test"}]

        # Should not raise exception due to retry
        with patch("src.core.perplexity.service.time.sleep"):  # Speed up test by mocking sleep
            result = perplexity_service.call_api(messages)

        assert result["choices"][0]["message"]["content"] == "success"
        assert mock_post.call_count == 2


class TestOrderServiceErrorHandling:
    """Test error handling in OrderService."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def order_service(self, mock_client: Mock) -> OrderService:
        """Create OrderService with mock client."""
        return OrderService(mock_client)

    def test_place_order_validation_failure(self, order_service: OrderService) -> None:
        """Test order placement with validation failure."""
        # Mock the validator to return failure
        with patch.object(order_service, "_order_validator") as mock_validator:
            mock_validator.validate_order_placement.return_value = (False, ["Validation error"])

            result = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.LIMIT, 0.1, price=50000)

            assert result is None

    def test_place_order_binance_exception(self, order_service: OrderService, mock_client: Mock) -> None:
        """Test order placement with Binance exception."""
        # Mock successful validation
        with patch.object(order_service, "_order_validator") as mock_validator:
            mock_validator.validate_order_placement.return_value = (True, [])

            # Mock Binance error
            mock_client.place_market_order.side_effect = BinanceException("Insufficient funds", code=-2010)

            # The order service should catch the exception and handle it gracefully by returning None
            result = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.1)
            assert result is None

    def test_place_order_api_error(self, order_service: OrderService, mock_client: Mock) -> None:
        """Test order placement with API error."""
        # Mock successful validation
        with patch.object(order_service, "_order_validator") as mock_validator:
            mock_validator.validate_order_placement.return_value = (True, [])

            # Mock API error
            mock_client.place_market_order.side_effect = APIError("API Error", status_code=400)

            # The order service should catch the exception and handle it gracefully by returning None
            result = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.1)
            assert result is None


class TestOrderValidatorErrorHandling:
    """Test error handling in OrderValidator."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    @pytest.fixture
    def order_validator(self, mock_client: Mock) -> OrderValidator:
        """Create OrderValidator with mock client."""
        return OrderValidator(mock_client)

    def test_validate_oco_order_missing_symbol_info(self, order_validator: OrderValidator, mock_client: Mock) -> None:
        """Test OCO validation when exchange info is unavailable."""
        mock_client.get_exchange_info.return_value = None
        mock_client.get_all_tickers.return_value = []

        is_valid, errors = order_validator.validate_oco_order("BTCUSDT", 1.0, 50000.0, 49000.0)

        assert not is_valid
        assert any("Could not retrieve symbol information" in error for error in errors)

    def test_validate_oco_order_api_exception(self, order_validator: OrderValidator, mock_client: Mock) -> None:
        """Test OCO validation when API call throws exception."""
        mock_client.get_exchange_info.side_effect = BinanceException("API Error", code=-1000)

        is_valid, errors = order_validator.validate_oco_order("BTCUSDT", 1.0, 50000.0, 49000.0)

        assert not is_valid
        assert any("Symbol validation data error" in error for error in errors)

    def test_get_current_price_api_error(self, order_validator: OrderValidator, mock_client: Mock) -> None:
        """Test current price retrieval with API error."""
        mock_client.get_all_tickers.side_effect = Exception("API Error")

        price = order_validator._get_current_price("BTCUSDT")

        assert price is None

    def test_validate_with_network_error(self, order_validator: OrderValidator, mock_client: Mock) -> None:
        """Test validation with network connectivity issues."""
        mock_client.get_exchange_info.side_effect = ConnectionError("Network error")

        is_valid, errors = order_validator.validate_oco_order("BTCUSDT", 1.0, 50000.0, 49000.0)

        assert not is_valid
        assert any("Symbol validation data error" in error for error in errors)


class TestOrderErrorHandler:
    """Test OrderErrorHandler utility functions."""

    def test_format_validation_error(self) -> None:
        """Test validation error formatting."""
        result = OrderErrorHandler.format_validation_error("BTCUSDT", ["Error 1", "Error 2"])

        assert "❌ ORDER VALIDATION FAILED for BTCUSDT" in result
        assert "• Error 1" in result
        assert "• Error 2" in result

    def test_format_parameter_error(self) -> None:
        """Test parameter error formatting."""
        result = OrderErrorHandler.format_parameter_error(OrderType.LIMIT, "price")

        assert "❌ PARAMETER ERROR" in result
        assert "price is required for LIMIT orders" in result

    def test_format_api_error_with_details(self) -> None:
        """Test API error formatting with details."""
        details = {"symbol": "BTCUSDT", "error_code": -1000}
        result = OrderErrorHandler.format_api_error("ORDER PLACEMENT", "BTCUSDT", details)

        assert "❌ API ERROR during ORDER PLACEMENT for BTCUSDT" in result
        assert "symbol: BTCUSDT" in result
        assert "error_code: -1000" in result

    def test_format_api_error_without_details(self) -> None:
        """Test API error formatting without details."""
        result = OrderErrorHandler.format_api_error("ORDER PLACEMENT", "BTCUSDT")

        assert "❌ API ERROR during ORDER PLACEMENT for BTCUSDT" in result


class TestCascadingErrorScenarios:
    """Test complex error scenarios involving multiple components."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock BinanceClient."""
        return Mock(spec=BinanceClient)

    def test_complete_service_unavailable_scenario(self, mock_client: Mock) -> None:
        """Test scenario where all services are unavailable."""
        # Mock all API calls to fail
        mock_client.get_account_info.side_effect = ConnectionError("Network error")
        mock_client.get_exchange_info.side_effect = ConnectionError("Network error")
        mock_client.get_all_tickers.side_effect = ConnectionError("Network error")
        mock_client.get_klines.side_effect = ConnectionError("Network error")

        # Test AccountService
        account_service = AccountService(mock_client)
        account_result = account_service.get_account_info()
        assert account_result is None

        # Test IndicatorService
        mock_config = {"analysis": {"min_data_points": 21}}
        indicator_service = IndicatorService(mock_client, mock_config)
        indicator_result = indicator_service.calculate_indicators(["BTC"])
        assert "errors" in indicator_result
        assert "error_list" in indicator_result["errors"]
        assert any("BTC" in error for error in indicator_result["errors"]["error_list"])

        # Test OrderValidator
        validator = OrderValidator(mock_client)
        is_valid, errors = validator.validate_oco_order("BTCUSDT", 1.0, 50000.0, 49000.0)
        assert not is_valid
        assert len(errors) > 0

    def test_partial_service_degradation(self, mock_client: Mock) -> None:
        """Test scenario with partial service availability."""
        # Account service works, but exchange info fails
        mock_client.get_account_info.return_value = {"balances": []}
        mock_client.get_exchange_info.side_effect = BinanceException("Rate limited", code=-1003)
        mock_client.get_all_tickers.return_value = [{"symbol": "BTCUSDT", "price": "50000.0"}]

        # AccountService should work
        account_service = AccountService(mock_client)
        account_result = account_service.get_account_info()
        assert account_result is not None

        # OrderValidator should fail gracefully
        validator = OrderValidator(mock_client)
        is_valid, errors = validator.validate_oco_order("BTCUSDT", 1.0, 50000.0, 49000.0)
        assert not is_valid
        assert any("Symbol validation data error" in error for error in errors)

    def test_error_recovery_after_retry(self, mock_client: Mock) -> None:
        """Test error recovery scenarios after retries."""
        # First call fails, second succeeds
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise BinanceException("Temporary error", code=-1001)
            return {"balances": []}

        mock_client.get_account_info.side_effect = side_effect

        account_service = AccountService(mock_client)

        # First call should fail
        result1 = account_service.get_account_info()
        assert result1 is None

        # Second call should succeed
        result2 = account_service.get_account_info()
        assert result2 is not None
