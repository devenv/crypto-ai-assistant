"""Core Perplexity AI service for trading analysis and recommendations."""

import json
import logging
import os
import time
from typing import Any, cast

import requests
from dotenv import load_dotenv

from api.exceptions import (
    PerplexityAPIError,
    PerplexityAuthenticationError,
    PerplexityModelError,
    PerplexityRateLimitError,
    PerplexityServerError,
    PerplexityTimeoutError,
)

from .analysis_generator import AnalysisGenerator
from .cost_tracker import CostTracker
from .models import CostBreakdown, ParallelAnalysisResult, SessionCostSummary
from .quality_validator import QualityValidator
from .text_analyzer import TextAnalyzer

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class PerplexityService:
    """Service for interacting with Perplexity AI API."""

    def __init__(self, model: str = "sonar"):
        """Initialize the Perplexity service with API key from environment.

        Args:
            model: Perplexity model to use. Options:
                - "sonar": Fast model for monitoring (30-60 seconds)
                - "sonar-pro": Premium model for comprehensive strategy development (2-5 minutes)
                - "sonar-large": High-performing model for complex multi-source analysis
        """
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise PerplexityAuthenticationError(
                "PERPLEXITY_API_KEY not found in environment variables.\n"
                + "\n"
                + "To set up your Perplexity API key:\n"
                + "1. Create a .env file in the project root\n"
                + "2. Add the following line to the .env file:\n"
                + '   PERPLEXITY_API_KEY="your_perplexity_api_key_here"\n'  # pragma: allowlist secret
                + "3. Get your API key from https://perplexity.ai\n"
                + "\n"
                + "Example .env file content:\n"
                + 'BINANCE_API_KEY="your_binance_api_key"\n'  # pragma: allowlist secret
                + 'BINANCE_API_SECRET="your_binance_secret"\n'  # pragma: allowlist secret
                + 'PERPLEXITY_API_KEY="your_perplexity_api_key"\n'  # pragma: allowlist secret
            )

        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        self.model = model

        # Set appropriate timeout based on model complexity
        if model in ["sonar-pro", "sonar-large", "sonar-deep-research"]:  # Include legacy name for compatibility
            self.timeout = 300  # 5 minutes for comprehensive analysis
        else:
            self.timeout = 60  # 1 minute for quick monitoring

        # Retry configuration
        self.max_retries = 3
        self.base_retry_delay = 2  # seconds

        # Initialize components
        self._cost_tracker = CostTracker()
        self._quality_validator = QualityValidator()
        self._text_analyzer = TextAnalyzer()
        self._analysis_generator = AnalysisGenerator(self.call_api, self.model)

    def call_api(self, messages: list[dict[str, str]], temperature: float = 0.1, max_tokens: int = 1000, retry_count: int = 0) -> dict[str, Any]:
        """Make a call to Perplexity API with enhanced error handling and retry logic.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Randomness in response generation (0.0-1.0)
            max_tokens: Maximum tokens in response (default: 1000)
            retry_count: Current retry attempt (used internally)

        Returns:
            API response as dictionary

        Raises:
            PerplexityAuthenticationError: When API key is invalid
            PerplexityRateLimitError: When rate limit is exceeded
            PerplexityTimeoutError: When request times out
            PerplexityServerError: When server returns 5xx error
            PerplexityModelError: When model is invalid or unavailable
            PerplexityAPIError: For other API errors
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "presence_penalty": 0.1,  # Slight preference for new financial topics
            "top_p": 0.9,  # Focus on high probability tokens for accuracy
            "stream": False,
        }

        try:
            logger.debug(f"Making Perplexity API call (attempt {retry_count + 1}/{self.max_retries + 1})")

            response: requests.Response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )

            # Handle different HTTP status codes
            if response.status_code == 200:
                api_response = cast(dict[str, Any], response.json())

                # Calculate and track costs
                self._cost_tracker.calculate_cost(api_response, self.model)

                return api_response
            elif response.status_code == 401:
                raise PerplexityAuthenticationError(
                    "Invalid API key or authentication failed.\n"
                    + "\n"
                    + "Please check:\n"
                    + "1. Your PERPLEXITY_API_KEY in the .env file is correct\n"
                    + "2. The API key is valid and not expired\n"
                    + "3. You have access to the Perplexity API\n"
                    + "\n"
                    + "Get your API key from: https://perplexity.ai\n"
                )
            elif response.status_code == 429:
                # Extract retry-after header if available
                retry_after = None
                if "retry-after" in response.headers:
                    try:
                        retry_after = int(response.headers["retry-after"])
                    except ValueError:
                        retry_after = None
                raise PerplexityRateLimitError(retry_after=retry_after)
            elif response.status_code in [500, 502, 503, 504]:
                raise PerplexityServerError(f"Server error: {response.text[:200]}", status_code=response.status_code)
            elif response.status_code == 400:
                # Parse error details for model-related errors
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", response.text)
                    if "model" in error_message.lower():
                        raise PerplexityModelError(f"Model error: {error_message}", model=self.model)
                    else:
                        raise PerplexityAPIError(f"Bad request: {error_message}", status_code=400)
                except json.JSONDecodeError:
                    raise PerplexityAPIError(f"Bad request: {response.text[:200]}", status_code=400) from None
            else:
                # Other HTTP errors
                raise PerplexityAPIError(f"Unexpected error: {response.text[:200]}", status_code=response.status_code)

        except requests.exceptions.Timeout:
            raise PerplexityTimeoutError(timeout_duration=self.timeout) from None
        except requests.exceptions.ConnectionError as e:
            raise PerplexityAPIError(f"Connection error: {str(e)}") from e
        except PerplexityRateLimitError as e:
            # Handle rate limiting with retry logic
            if retry_count < self.max_retries:
                wait_time = e.retry_after or (self.base_retry_delay * (2**retry_count))
                logger.warning(f"Rate limit hit, waiting {wait_time} seconds before retry {retry_count + 1}")
                time.sleep(wait_time)
                return self.call_api(messages, temperature, max_tokens, retry_count + 1)
            else:
                logger.error(f"Rate limit exceeded after {self.max_retries} retries")
                raise
        except (PerplexityServerError, PerplexityAPIError) as e:
            # Retry server errors but not authentication or model errors
            if retry_count < self.max_retries and isinstance(e, PerplexityServerError):
                wait_time = self.base_retry_delay * (2**retry_count)
                logger.warning(f"Server error, retrying in {wait_time} seconds (attempt {retry_count + 1})")
                time.sleep(wait_time)
                return self.call_api(messages, temperature, max_tokens, retry_count + 1)
            else:
                raise
        except requests.exceptions.RequestException as e:
            # Catch any other requests exceptions
            raise PerplexityAPIError(f"Request failed: {str(e)}") from e
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error in Perplexity API call: {str(e)}")
            raise PerplexityAPIError(f"Unexpected error: {str(e)}") from e

    # Delegate methods to components
    def get_session_cost_summary(self) -> SessionCostSummary:
        """Get a summary of costs for the current session."""
        return self._cost_tracker.get_session_cost_summary()

    def format_cost_report(self) -> str:
        """Format a human-readable cost report for the current session."""
        return self._cost_tracker.format_cost_report()

    def generate_portfolio_analysis(
        self,
        portfolio_data: str,
        market_data: str,
        order_data: str,
        protection_analysis: str | None = None,
        balance_analysis: str | None = None,
        risk_context: str | None = None,
        recent_activity_context: str | None = None,
        source_focus: str = "institutional",
        synthesis_context: str | None = None,
    ) -> str:
        """Generate comprehensive portfolio analysis."""
        return self._analysis_generator.generate_portfolio_analysis(
            portfolio_data,
            market_data,
            order_data,
            protection_analysis,
            balance_analysis,
            risk_context,
            recent_activity_context,
            source_focus,
            synthesis_context,
        )

    def generate_market_timing_analysis(self, portfolio_data: str, market_data: str) -> str:
        """Generate focused market timing analysis."""
        return self._analysis_generator.generate_market_timing_analysis(portfolio_data, market_data)

    def generate_parallel_portfolio_analysis(
        self,
        portfolio_data: str,
        market_data: str,
        order_data: str,
        protection_analysis: str | None = None,
        balance_analysis: str | None = None,
        risk_context: str | None = None,
        recent_activity_context: str | None = None,
    ) -> ParallelAnalysisResult:
        """Generate two-stage portfolio analysis."""
        return self._analysis_generator.generate_parallel_portfolio_analysis(
            portfolio_data,
            market_data,
            order_data,
            protection_analysis,
            balance_analysis,
            risk_context,
            recent_activity_context,
        )

    def generate_parallel_market_timing_analysis(self, portfolio_data: str, market_data: str) -> ParallelAnalysisResult:
        """Generate parallel market timing analysis."""
        return self._analysis_generator.generate_parallel_market_timing_analysis(portfolio_data, market_data)

    # Delegate text analysis methods for backward compatibility
    def calculate_text_consistency_score(self, analysis_1: str, analysis_2: str) -> float:
        """Calculate text consistency score between two analyses."""
        # Convert from 0-100 scale to 0-1 scale for backward compatibility
        return self._text_analyzer.calculate_text_consistency_score(analysis_1, analysis_2) / 100.0

    def _identify_text_discrepancies(self, analysis_1: str, analysis_2: str) -> list[str]:
        """Identify discrepancies between two text analyses."""
        return self._text_analyzer.identify_text_discrepancies(analysis_1, analysis_2)

    def _get_asset_sentiment(self, text: str, asset_short: str, asset_long: str) -> str | None:
        """Get sentiment for a specific asset from text."""
        return self._text_analyzer._get_asset_sentiment(text, asset_short, asset_long)

    def get_sentiment_scores(self, text: str) -> dict[str, float]:
        """Get sentiment scores from text."""
        if not text:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        # Define sentiment terms
        bullish_terms = ["bullish", "buy", "up", "green", "positive", "strong", "excellent", "momentum"]
        bearish_terms = ["bearish", "sell", "down", "red", "negative", "weak", "crash", "terrible", "loss"]
        neutral_terms = ["neutral", "sideways", "stable", "hold", "wait", "currently", "price"]

        # Get raw counts
        raw_scores = self._text_analyzer._get_sentiment_scores(text, bullish_terms, bearish_terms, neutral_terms)
        total_words = len(text.split())

        if total_words == 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        # Normalize to 0.0-1.0 range based on text length
        return {
            "positive": min(1.0, raw_scores["bullish"] / max(1, total_words / 10)),
            "negative": min(1.0, raw_scores["bearish"] / max(1, total_words / 10)),
            "neutral": min(1.0, raw_scores["neutral"] / max(1, total_words / 10)),
        }

    def _calculate_cost(self, response: dict[str, Any], model: str) -> CostBreakdown:
        """Calculate cost for API response."""
        return self._cost_tracker.calculate_cost(response, model)

    def get_current_timestamp(self) -> str:
        """Get current timestamp."""
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def calculate_consistency_score_recommendations(self, recs_1: list[dict[str, Any]] | None, recs_2: list[dict[str, Any]] | None) -> float:
        """Calculate consistency score between recommendation lists."""
        return self._text_analyzer.calculate_consistency_score(recs_1, recs_2)

    def validate_perplexity_response_quality(self, response: str) -> dict[str, Any]:
        """Validate the quality of a Perplexity response."""
        is_valid, failure_reason = self._quality_validator.validate_perplexity_response_quality(response)
        return {
            "is_valid": is_valid,
            "failure_reason": failure_reason if not is_valid else "",
            "score": 1.0 if is_valid else 0.0,  # Simple scoring for backward compatibility
        }
