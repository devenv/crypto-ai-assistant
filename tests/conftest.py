import functools
import os
import sys
from typing import Any, Callable

import pytest
from _pytest.monkeypatch import MonkeyPatch
from typer import Typer

from api.exceptions import APIError

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: MonkeyPatch) -> None:
    """Mocks environment variables for tests."""
    monkeypatch.setenv("BINANCE_API_KEY", "test_api_key")
    monkeypatch.setenv("BINANCE_API_SECRET", "test_api_secret")


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
