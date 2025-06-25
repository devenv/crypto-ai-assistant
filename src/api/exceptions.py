"""
Custom exception classes for the API client.
"""

from __future__ import annotations


class APIError(Exception):
    """
    Base exception for all API-related errors.

    Attributes:
        status_code: The HTTP status code of the error response, if available.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code

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
