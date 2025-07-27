import functools
import os
import sys
from collections.abc import Callable
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch
from hypothesis import Phase, Verbosity, settings
from typer import Typer

from src.api.exceptions import APIError

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add src directory to Python path (like main.py does) - CRITICAL for coverage
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Configure Hypothesis for fast test execution and timeout prevention
settings.register_profile(
    "fast",
    max_examples=10,  # Reduced from default 100
    deadline=1000,  # 1 second deadline per test
    phases=[Phase.generate],  # Skip shrinking phase to prevent timeouts
    verbosity=Verbosity.normal,
    suppress_health_check=[],
)
settings.load_profile("fast")


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: MonkeyPatch) -> None:
    """Mocks environment variables for tests - UPDATED with Perplexity key."""
    monkeypatch.setenv("BINANCE_API_KEY", "test_api_key")
    monkeypatch.setenv("BINANCE_API_SECRET", "test_api_secret")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test_perplexity_key")

    # Block any attempt to use real API keys
    monkeypatch.setenv("REAL_API_TESTING", "false")


@pytest.fixture(autouse=True)
def mock_time_sleep(monkeypatch: MonkeyPatch) -> None:
    """
    CRITICAL PERFORMANCE: Override time.sleep globally to prevent test timeouts.
    This eliminates delays from retry logic, rate limiting, and property tests.
    """
    import time

    def mock_sleep(seconds):
        # Do nothing - tests should run instantly without sleeping
        pass

    monkeypatch.setattr(time, "sleep", mock_sleep)


# 🚨 CRITICAL API ISOLATION: Prevent real network calls during tests
@pytest.fixture(autouse=True)
def block_real_network_calls(monkeypatch: MonkeyPatch) -> None:
    """
    MANDATORY: Block real network calls with helpful error messages.
    This prevents accidental API calls while allowing proper test mocking.
    """
    import requests

    def mock_network_error(*args, **kwargs):
        raise RuntimeError(
            "❌ BLOCKED: Real network call detected in tests!\n"
            "Tests must use proper mocking. Add @patch('requests.get') or similar.\n"
            f"Attempted call: args={args}, kwargs={kwargs}"
        )

    # Only block if the request looks like a real API call
    original_request = requests.Session.request

    def safe_request(self, method, url, *args, **kwargs):
        # Block real API URLs
        if isinstance(url, str) and any(
            domain in url.lower() for domain in ["api.binance.com", "perplexity.ai", "api.perplexity.ai", "testnet.binance.vision"]
        ):
            raise RuntimeError(f"❌ BLOCKED: Real API call to {url} in tests!\nUse @patch('requests.Session') or @patch('requests.get') in your test.")
        # Allow other requests (for potential test utilities)
        return original_request(self, method, url, *args, **kwargs)

    monkeypatch.setattr(requests.Session, "request", safe_request)


def handle_api_error(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to catch and handle APIErrors gracefully for tests."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except APIError as e:
            # In a real app, we might log this. For tests, we can re-raise
            # or handle as needed. Here, we'll simulate the CLI's exit.
            print(f"Intercepted APIError: {e}")
            raise

    return wrapper


def patch_all_commands(app: Typer, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Recursively find all Typer commands and apply a patch.
    """
    for command_info in app.registered_commands:
        if command_info.callback:
            original_callback = command_info.callback
            target_path = f"{original_callback.__module__}.{original_callback.__name__}"
            decorated_callback = handle_api_error(original_callback)
            monkeypatch.setattr(target_path, decorated_callback)

    for group in app.registered_groups:
        if group.typer_instance:
            patch_all_commands(group.typer_instance, monkeypatch)


@pytest.fixture(scope="function")
def patch_api_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Fixture to automatically wrap all Typer commands with an API error handler.
    """
    from main import app  # Import app here to avoid circular dependencies

    patch_all_commands(app, monkeypatch)


@pytest.fixture(autouse=True, scope="session")
def apply_api_error_handling_to_all_tests(request: pytest.FixtureRequest) -> None:
    """
    Apply the patch_api_error_handling fixture to all tests.
    """
    if "patch_api_error_handling" in request.fixturenames:
        request.getfixturevalue("patch_api_error_handling")
