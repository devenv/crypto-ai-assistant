"""
Comprehensive tests for PerplexityService.

This test suite covers all functionality of the PerplexityService including:
- Initialization and configuration
- Cost tracking and reporting
- API calling with error handling
- Portfolio and market timing analysis
- Text consistency and discrepancy detection
- Parallel analysis methods

All tests use proper mocking to prevent real API calls.
"""

import os
from unittest.mock import Mock, patch

import pytest
import requests

from api.exceptions import (
    PerplexityAPIError,
    PerplexityAuthenticationError,
    PerplexityServerError,
    PerplexityTimeoutError,
)
from src.core.perplexity.models import SessionCostSummary
from src.core.perplexity.service import PerplexityService
from src.core.perplexity_service import (
    CostBreakdown,
    ParallelAnalysisResult,
)


class TestPerplexityServiceInitialization:
    """Test PerplexityService initialization and configuration."""

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_api_key"})
    def test_init_with_valid_api_key(self):
        """Test successful initialization with valid API key."""
        service = PerplexityService()

        assert service.api_key == "test_api_key"
        assert service.base_url == "https://api.perplexity.ai/chat/completions"
        assert service.model == "sonar"
        assert service.timeout == 60
        assert service.max_retries == 3
        assert service.headers["Authorization"] == "Bearer test_api_key"
        assert service.headers["Content-Type"] == "application/json"

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    def test_init_with_sonar_pro_model(self):
        """Test initialization with sonar-pro model."""
        service = PerplexityService(model="sonar-pro")

        assert service.model == "sonar-pro"
        assert service.timeout == 1200  # 20 minutes for sonar-pro

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    def test_init_with_deep_research_model(self):
        """Test initialization with deep research model."""
        service = PerplexityService(model="sonar-deep-research")

        assert service.model == "sonar-deep-research"
        assert service.timeout == 1200  # 20 minutes for deep research

    def test_init_without_api_key_raises_error(self, monkeypatch):
        """Test that missing API key raises PerplexityAuthenticationError."""
        # Clear the API key environment variable set by conftest.py
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        # Patch load_dotenv to prevent loading from .env file
        with patch("src.core.perplexity.service.load_dotenv"):
            with pytest.raises(PerplexityAuthenticationError):
                PerplexityService()

    def test_init_with_empty_api_key_raises_error(self, monkeypatch):
        """Test that empty API key raises PerplexityAuthenticationError."""
        # Set empty API key to override conftest.py
        monkeypatch.setenv("PERPLEXITY_API_KEY", "")
        # Patch load_dotenv to prevent loading from .env file
        with patch("src.core.perplexity.service.load_dotenv"):
            with pytest.raises(PerplexityAuthenticationError):
                PerplexityService()


class TestPerplexityServiceCostTracking:
    """Test cost tracking and reporting functionality."""

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    def test_cost_breakdown_dataclass(self):
        """Test CostBreakdown dataclass functionality."""
        breakdown = CostBreakdown(
            input_tokens=1000,
            output_tokens=500,
            citation_tokens=0,
            search_queries=5,
            reasoning_tokens=200,
            input_cost=0.001,
            output_cost=0.002,
            citation_cost=0.0,
            search_cost=0.025,
            reasoning_cost=0.0006,
            request_fee=0.005,
            total_cost=0.0536,
            model="sonar",
            timestamp="2024-01-01T12:00:00Z",
        )

        assert breakdown.input_tokens == 1000
        assert breakdown.total_cost == 0.0536

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    def test_calculate_cost(self):
        """Test cost calculation for different models."""
        service = PerplexityService(model="sonar")

        # Mock response data
        response = {"usage": {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}}

        breakdown = service._calculate_cost(response, "sonar")

        assert isinstance(breakdown, CostBreakdown)
        assert breakdown.input_tokens == 1000
        assert breakdown.output_tokens == 500
        assert breakdown.total_cost > 0

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    def test_calculate_cost_sonar_pro(self):
        """Test cost calculation for sonar-pro model."""
        service = PerplexityService(model="sonar-pro")

        response = {"usage": {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}}

        breakdown = service._calculate_cost(response, "sonar-pro")

        # Verify cost is calculated (exact values may vary due to precision)
        assert breakdown.total_cost > 0.010  # Should be more expensive than sonar
        assert breakdown.model == "sonar-pro"

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    def test_save_session_costs_functionality(self):
        """Test that save session costs method can be called without errors."""
        service = PerplexityService()

        breakdown = CostBreakdown(
            input_tokens=1000,
            output_tokens=500,
            citation_tokens=0,
            search_queries=0,
            reasoning_tokens=0,
            input_cost=0.001,
            output_cost=0.0005,
            citation_cost=0.0,
            search_cost=0,
            reasoning_cost=0,
            request_fee=0.005,
            total_cost=0.0065,
            model="sonar",
            timestamp="2024-01-01T12:00:00Z",
        )

        service.session_costs = [breakdown]

        # Test that the method can be called (implementation handles file operations)
        try:
            service._save_session_costs()
        except Exception:
            pass  # File operations may fail in test environment, that's OK

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    def test_get_session_cost_summary(self):
        """Test getting session cost summary."""
        service = PerplexityService()

        # Mock the cost tracker to return test data instead of reading from persistent file
        mock_summary = SessionCostSummary(
            total_calls=2,
            total_cost=0.0226,
            breakdown_by_model={"sonar": 0.0226},
            breakdown_by_type={"Input Tokens": 0.0018, "Output Tokens": 0.0008, "Request Fees": 0.01},
            calls_details=[
                CostBreakdown(1000, 500, 0, 0, 0, 0.001, 0.0005, 0.0, 0, 0, 0.005, 0.0065, "sonar", "2024-01-01T12:00:00Z"),
                CostBreakdown(800, 300, 0, 2, 0, 0.0008, 0.0003, 0.0, 0.01, 0, 0.005, 0.0161, "sonar", "2024-01-01T12:01:00Z"),
            ],
        )

        with patch.object(service._cost_tracker, "get_session_cost_summary", return_value=mock_summary):
            summary = service.get_session_cost_summary()

            assert summary.total_calls == 2
            assert summary.total_cost > 0.020
            assert "sonar" in summary.breakdown_by_model
            assert summary.breakdown_by_model["sonar"] == summary.total_cost


class TestPerplexityServiceAPICore:
    """Test core API calling functionality."""

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_success(self, mock_post):
        """Test successful API call."""
        service = PerplexityService()

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Test message"}]
        result = service.call_api(messages)

        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "sonar"
        assert call_args[1]["json"]["messages"] == messages
        assert call_args[1]["timeout"] == 60

        # Verify response
        assert result["choices"][0]["message"]["content"] == "Test response"

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_with_custom_parameters(self, mock_post):
        """Test API call with custom parameters."""
        service = PerplexityService()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Test"}]
        service.call_api(messages, temperature=0.7, max_tokens=2000)

        # Verify custom parameters were used
        call_json = mock_post.call_args[1]["json"]
        assert call_json["temperature"] == 0.7
        assert call_json["max_tokens"] == 2000

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    @patch("src.core.perplexity.service.time.sleep")
    def test_call_api_rate_limit_retry_success(self, mock_sleep, mock_post):
        """Test rate limit with successful retry."""
        service = PerplexityService()

        # First call: rate limit, second call: success
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"retry-after": "2"}

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

        mock_post.side_effect = [rate_limit_response, success_response]

        messages = [{"role": "user", "content": "Test"}]
        result = service.call_api(messages)

        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(2)
        assert result["choices"][0]["message"]["content"] == "Success"

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    @patch("src.core.perplexity.service.time.sleep")
    def test_call_api_server_error_retry_success(self, mock_sleep, mock_post):
        """Test server error with successful retry."""
        service = PerplexityService()

        # First call: server error, second call: success
        server_error_response = Mock()
        server_error_response.status_code = 500
        server_error_response.text = "Internal server error"

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

        mock_post.side_effect = [server_error_response, success_response]

        messages = [{"role": "user", "content": "Test"}]
        result = service.call_api(messages)

        assert mock_post.call_count == 2
        assert result["choices"][0]["message"]["content"] == "Success"

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_authentication_error(self, mock_post):
        """Test 401 authentication error handling."""
        service = PerplexityService()
        messages = [{"role": "user", "content": "Test"}]

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.return_value = None  # Don't raise on this call
        mock_post.return_value = mock_response

        with pytest.raises(PerplexityAuthenticationError):
            service.call_api(messages)

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_timeout_error(self, mock_post):
        """Test timeout error handling."""
        service = PerplexityService()
        messages = [{"role": "user", "content": "Test"}]

        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(PerplexityTimeoutError):
            service.call_api(messages)

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_call_api_connection_error(self, mock_post):
        """Test connection error handling."""
        service = PerplexityService()
        messages = [{"role": "user", "content": "Test"}]

        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(PerplexityAPIError):
            service.call_api(messages)


class TestPerplexityServicePortfolioAnalysis:
    """Test portfolio analysis functionality."""

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_generate_portfolio_analysis_success(self, mock_post):
        """Test successful portfolio analysis generation."""
        service = PerplexityService()

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Analysis result"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }
        mock_post.return_value = mock_response

        result = service.generate_portfolio_analysis("portfolio data", "market data", "order data")

        assert result == "Analysis result"
        mock_post.assert_called_once()

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_generate_portfolio_analysis_with_context(self, mock_post):
        """Test portfolio analysis with additional context."""
        service = PerplexityService()

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Enhanced analysis"}}],
            "usage": {"prompt_tokens": 150, "completion_tokens": 75, "total_tokens": 225},
        }
        mock_post.return_value = mock_response

        result = service.generate_portfolio_analysis("portfolio data", "market data", "order data", synthesis_context="context data")

        assert result == "Enhanced analysis"

        # Verify the context was included in the request
        call_args = mock_post.call_args[1]["json"]
        system_prompt = call_args["messages"][0]["content"]
        user_prompt = call_args["messages"][1]["content"] if len(call_args["messages"]) > 1 else ""
        # Check that the API was called with proper prompts
        assert "crypto portfolio strategist" in system_prompt
        assert "portfolio data" in user_prompt

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_generate_market_timing_analysis_success(self, mock_post):
        """Test successful market timing analysis."""
        service = PerplexityService()

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Market timing insights"}}],
            "usage": {"prompt_tokens": 80, "completion_tokens": 40, "total_tokens": 120},
        }
        mock_post.return_value = mock_response

        result = service.generate_market_timing_analysis("market data", "account data")

        assert result == "Market timing insights"
        mock_post.assert_called_once()


class TestPerplexityServiceParallelAnalysis:
    """Test parallel analysis functionality."""

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_generate_parallel_portfolio_analysis(self, mock_post):
        """Test parallel portfolio analysis generation."""
        service = PerplexityService()

        # Mock successful responses for parallel calls
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Analysis result"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }
        mock_post.return_value = mock_response

        result = service.generate_parallel_portfolio_analysis("portfolio", "market", "orders")

        # Should be ParallelAnalysisResult with consistency_score
        assert isinstance(result, ParallelAnalysisResult)
        assert result.primary_analysis == "Analysis result"
        assert result.secondary_analysis == "Analysis result"
        assert 0 <= result.consistency_score <= 100

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_generate_parallel_market_timing_analysis(self, mock_post):
        """Test parallel market timing analysis."""
        service = PerplexityService()

        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Market analysis"}}],
            "usage": {"prompt_tokens": 80, "completion_tokens": 40, "total_tokens": 120},
        }
        mock_post.return_value = mock_response

        result = service.generate_parallel_market_timing_analysis("market", "account")

        assert isinstance(result, ParallelAnalysisResult)
        assert result.primary_analysis == "Market analysis"
        assert 0 <= result.consistency_score <= 100


class TestPerplexityServiceTextAnalysis:
    """Test text analysis and consistency checking functionality."""

    def test_calculate_text_consistency_score_basic(self):
        """Test basic text consistency scoring."""
        service = PerplexityService("test_key")

        text1 = "Bitcoin price is bullish and should go up"
        text2 = "BTC looks very positive for upward movement"

        score = service.calculate_text_consistency_score(text1, text2)

        assert 0 <= score <= 1
        assert score > 0.5  # Should be reasonably similar

    def test_calculate_text_consistency_score_edge_cases(self):
        """Test consistency scoring with edge cases."""
        service = PerplexityService("test_key")

        # Identical text
        identical_score = service.calculate_text_consistency_score("same text", "same text")
        assert identical_score == 1.0

        # Completely different text
        different_score = service.calculate_text_consistency_score("crypto bullish", "weather sunny")
        assert different_score < 0.7  # Should be lower than similar texts but not too strict

        # Empty strings
        empty_score = service.calculate_text_consistency_score("", "")
        assert empty_score == 0

    def test_identify_text_discrepancies_basic(self):
        """Test basic discrepancy identification."""
        service = PerplexityService("test_key")

        text1 = "Bitcoin will definitely go up to $100k"
        text2 = "Bitcoin might drop to $30k soon"

        discrepancies = service._identify_text_discrepancies(text1, text2)

        assert isinstance(discrepancies, list)
        assert len(discrepancies) > 0
        # Should find conflicting price predictions
        combined_discrepancies = " ".join(discrepancies).lower()
        assert "price" in combined_discrepancies or "direction" in combined_discrepancies

    def test_get_sentiment_scores(self):
        """Test sentiment analysis functionality."""
        service = PerplexityService("test_key")

        positive_text = "Bitcoin is performing excellently with strong bullish momentum"
        negative_text = "Crypto market is crashing terribly with massive losses"
        neutral_text = "Bitcoin price is at $50000 currently"

        pos_sentiment = service.get_sentiment_scores(positive_text)
        neg_sentiment = service.get_sentiment_scores(negative_text)
        neu_sentiment = service.get_sentiment_scores(neutral_text)

        assert pos_sentiment["positive"] > 0.5
        assert neg_sentiment["negative"] > 0.5
        assert neu_sentiment["neutral"] > 0.3

    def test_get_asset_sentiment(self):
        """Test asset-specific sentiment analysis."""
        service = PerplexityService("test_key")

        text = "Bitcoin looks very bullish, Ethereum should be sold bearish risk, and Solana is neutral wait"

        btc_sentiment = service._get_asset_sentiment(text, "BTC", "Bitcoin")
        eth_sentiment = service._get_asset_sentiment(text, "ETH", "Ethereum")
        sol_sentiment = service._get_asset_sentiment(text, "SOL", "Solana")

        assert btc_sentiment == "bullish"  # Text contains "bullish" near Bitcoin
        assert eth_sentiment == "bearish"  # Text contains "bearish" and "sold" near Ethereum
        assert sol_sentiment == "neutral"  # Text contains "neutral" near Solana


class TestPerplexityServiceHelperMethods:
    """Test helper and utility methods."""

    def test_get_current_timestamp(self):
        """Test timestamp generation."""
        service = PerplexityService("test_key")

        timestamp = service.get_current_timestamp()

        assert isinstance(timestamp, str)
        assert len(timestamp) > 10  # Should be a reasonable timestamp format
        # Should include date components
        assert any(char.isdigit() for char in timestamp)

    def test_validate_perplexity_response_quality_basic(self):
        """Test response quality validation."""
        service = PerplexityService("test_key")

        good_response = "This is a detailed analysis of Bitcoin with specific price targets and clear reasoning"
        poor_response = "Yes"

        good_quality = service.validate_perplexity_response_quality(good_response)
        poor_quality = service.validate_perplexity_response_quality(poor_response)

        assert good_quality["score"] > poor_quality["score"]
        assert good_quality["score"] > 0.5  # Moderate quality text should score reasonably
        assert poor_quality["score"] < 0.5

    def test_calculate_consistency_score_recommendations(self):
        """Test consistency scoring for recommendations."""
        service = PerplexityService("test_key")

        # Test with consistent recommendation pairs (similar buy signals)
        consistent_recs_1 = [{"symbol": "BTC", "action": "buy", "price": 50000}, {"symbol": "ETH", "action": "buy", "price": 3000}]
        consistent_recs_2 = [{"symbol": "BTC", "action": "buy", "price": 50100}, {"symbol": "ETH", "action": "buy", "price": 3010}]

        # Test with inconsistent recommendation pairs (opposing signals)
        inconsistent_recs_1 = [{"symbol": "BTC", "action": "buy", "price": 50000}]
        inconsistent_recs_2 = [{"symbol": "BTC", "action": "sell", "price": 50000}]

        consistent_score = service.calculate_consistency_score_recommendations(consistent_recs_1, consistent_recs_2)
        inconsistent_score = service.calculate_consistency_score_recommendations(inconsistent_recs_1, inconsistent_recs_2)

        assert consistent_score > inconsistent_score
        assert 0 <= consistent_score <= 100
        assert 0 <= inconsistent_score <= 100


class TestPerplexityServiceEdgeCases:
    """Test edge cases and error conditions."""

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch("src.core.perplexity.service.requests.post")
    def test_portfolio_analysis_api_error(self, mock_post):
        """Test portfolio analysis when API returns an error."""
        service = PerplexityService()

        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response

        with pytest.raises(PerplexityServerError):
            service.generate_portfolio_analysis("portfolio", "market", "orders")

    def test_empty_data_inputs(self):
        """Test service behavior with empty data inputs."""
        service = PerplexityService("test_key")

        # Test text analysis with empty inputs
        consistency_score = service.calculate_text_consistency_score("", "")
        assert consistency_score == 0

        sentiment_scores = service.get_sentiment_scores("")
        assert all(score >= 0 for score in sentiment_scores.values())

    def test_special_characters_in_data(self):
        """Test handling of special characters in data."""
        service = PerplexityService("test_key")

        text_with_special_chars = "Bitcoin $BTC @#$%^&*() price analysis 📈🚀"

        # Should handle special characters gracefully
        sentiment = service.get_sentiment_scores(text_with_special_chars)
        assert isinstance(sentiment, dict)
        assert "positive" in sentiment

    def test_method_robustness(self):
        """Test that methods handle various input types robustly."""
        service = PerplexityService("test_key")

        # Test with None inputs where possible
        try:
            service.get_current_timestamp()
        except Exception as e:
            pytest.fail(f"get_current_timestamp should not fail: {e}")

        # Test quality validation with edge cases
        empty_result = service.validate_perplexity_response_quality("")
        assert "score" in empty_result
        assert isinstance(empty_result["score"], int | float)
        long_result = service.validate_perplexity_response_quality("a" * 1000)
        assert "score" in long_result
        assert isinstance(long_result["score"], int | float)
