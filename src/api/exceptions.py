"""
Custom exception classes for the API client.
"""

from __future__ import annotations

from typing import override


class APIError(Exception):
    """
    Base exception for all API-related errors.

    Attributes:
        status_code: The HTTP status code of the error response, if available.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code

    @override
    def __str__(self) -> str:
        if self.status_code:
            return f"APIError (HTTP {self.status_code}): {super().__str__()}"
        return f"APIError: {super().__str__()}"


class BinanceException(APIError):
    """
    Raised for errors returned by the Binance API.

    This is a subclass of `APIError` and includes a specific Binance error code.

    Attributes:
        code: The Binance-specific error code.
    """

    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code

    @override
    def __str__(self) -> str:
        return f"BinanceException (code: {self.code}): {self.__cause__ or super().__str__()}"


class InvalidSymbolError(BinanceException):
    """
    Raised when an invalid or unknown symbol is used in a request.
    """


class InsufficientFundsError(BinanceException):
    """
    Raised when an action cannot be completed due to insufficient funds.
    """


# Perplexity API Exception Classes
class PerplexityAPIError(APIError):
    """
    Base exception for Perplexity AI API errors.

    Attributes:
        error_type: The type of Perplexity error (if available).
        retry_after: Seconds to wait before retrying (for rate limit errors).
    """

    def __init__(self, message: str, status_code: int | None = None, error_type: str | None = None, retry_after: int | None = None) -> None:
        super().__init__(message, status_code)
        self.error_type = error_type
        self.retry_after = retry_after

    @override
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.error_type:
            base_msg += f" (Type: {self.error_type})"
        if self.retry_after:
            base_msg += f" - Retry after {self.retry_after} seconds"
        return base_msg


class PerplexityRateLimitError(PerplexityAPIError):
    """
    Raised when Perplexity API rate limit is exceeded.
    """

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None) -> None:
        super().__init__(message, status_code=429, error_type="rate_limit", retry_after=retry_after)


class PerplexityAuthenticationError(PerplexityAPIError):
    """
    Raised when Perplexity API authentication fails.
    """

    def __init__(self, message: str = "Authentication failed - check API key") -> None:
        super().__init__(message, status_code=401, error_type="authentication")


class PerplexityTimeoutError(PerplexityAPIError):
    """
    Raised when Perplexity API request times out.
    """

    def __init__(self, message: str = "Request timed out", timeout_duration: int | None = None) -> None:
        msg = message
        if timeout_duration:
            msg += f" after {timeout_duration} seconds"
        super().__init__(msg, error_type="timeout")


class PerplexityServerError(PerplexityAPIError):
    """
    Raised when Perplexity API returns a server error (5xx).
    """

    def __init__(self, message: str = "Server error", status_code: int | None = None) -> None:
        super().__init__(message, status_code=status_code, error_type="server_error")


class PerplexityModelError(PerplexityAPIError):
    """
    Raised when there's an issue with the specified model.
    """

    def __init__(self, message: str = "Model error", model: str | None = None) -> None:
        msg = message
        if model:
            msg += f" (Model: {model})"
        super().__init__(msg, error_type="model_error")
        self.model = model
