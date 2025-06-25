# Coding Conventions

This document outlines the coding standards and conventions for the Crypto AI Assistant project. Adhering to these guidelines ensures consistency, readability, and maintainability of the codebase.

---

## Table of Contents

- [General Coding Style](#general-coding-style)
- [Python-Specific Conventions](#python-specific-conventions)
- [Testing Conventions](#testing-conventions)
- [Documentation Conventions](#documentation-conventions)
- [Commit Message Conventions](#commit-message-conventions)

---

## General Coding Style

-   **Don't Repeat Yourself (DRY):** Strive to abstract and reuse code. Avoid duplicating logic. The `BinanceClient` is a primary example of centralizing common functionality.
-   **Separation of Concerns:** Keep distinct functionalities in separate modules to create a clear and logical structure.
    -   `src/api`: All direct interaction logic with external APIs (e.g., Binance).
    -   `src/core`: Core application logic, such as data processing, calculations, and strategy implementation.
    -   `main.py`: The main entry point for the CLI application.
-   **Clarity and Readability:** Write code that is easy for others to understand.
    -   Use clear and descriptive names for variables, functions, and classes.
    -   Keep functions short and focused on a single task.

## Python-Specific Conventions

-   **Style Guide:** Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for all Python code. Use a linter and formatter like `ruff` or a combination of `black` and `isort` to enforce this automatically.
-   **Complete Type Hinting:** All new code, including all function signatures (arguments and return types) and variable declarations, **must** be fully type-hinted as specified in [PEP 484](https://www.python.org/dev/peps/pep-0484/). This is not optional and will be enforced during code review.
-   **Logging:** Use the `logging` module for all informational or debug output. **Do not use `print()`** for application output, as it cannot be easily configured or silenced.
-   **Configuration:** Manage configuration (e.g., API keys, settings) using environment variables or dedicated configuration files (`.env`, `config.toml`), not hardcoded values.

## Testing Conventions

The project uses `pytest` for testing.

-   **Test Coverage:** A minimum of **90% test coverage** is required. The CI pipeline will fail if coverage drops below this threshold. All new code must be accompanied by corresponding tests.
-   **Directory Structure:** The `tests/` directory should mirror the structure of the `src/` directory. For a module at `src/core/trader.py`, its tests should be at `tests/core/test_trader.py`.
-   **File Naming:** Test files must be named `test_*.py` or `*_test.py`. The former is preferred.
-   **Test Function Naming:** Test functions must be prefixed with `test_`. Use descriptive names that explain what the test covers (e.g., `test_trader_calculates_correct_moving_average`).
-   **Fixtures:** Use `pytest` fixtures for setup and teardown logic (e.g., creating a client instance). Define reusable, project-wide fixtures in `tests/conftest.py`. This file can also be used for other test setup, like modifying `sys.path` to ensure tests can find the source code.
-   **Mocking:** Use the `pytest-mock` plugin (which provides the `mocker` fixture) for all mocking and patching.
-   **Assertions:** Write clear and simple `assert` statements. Avoid complex expressions in a single assertion.
-   **Excluding Code from Coverage:** In rare cases where a line of code is untestable (e.g., a defensive `raise` that should never be hit), you can exclude it from coverage metrics by adding a `# pragma: no cover` comment to the line. This should be used sparingly and requires a clear justification.

### Handling TypedDict Unions in Tests

When a function's return type is a `Union` of different `TypedDict` types (e.g., `Optional[Union[Order, OcoOrder]]`), `mypy` may not be able to correctly infer the specific type within a test, even with type guards like `if "key" in result:`. This can lead to false positive "has no key" errors.

To resolve this, use `typing.cast` to explicitly tell `mypy` which `TypedDict` you are asserting against.

**Example:**

```python
# tests/core/test_orders.py
from typing import cast
from api.models import Order, OcoOrder
from core.orders import OrderService

def test_place_limit_order_success(order_service: OrderService, mock_client: MagicMock) -> None:
    """Test successful placement of a LIMIT order."""
    mock_client.place_limit_order.return_value = {"symbol": "BTCUSDT", "orderId": 123}
    order_result = order_service.place_order("BTCUSDT", OrderSide.BUY, OrderType.LIMIT, 0.1, price=50000)
    assert order_result is not None
    # Cast the result to the expected TypedDict
    order = cast(Order, order_result)
    assert order["orderId"] == 123
```

### Example Test Structure

```python
# tests/core/test_trader.py

import pytest
from core.trader import Trader

def test_trader_initialization(mocker):
    """
    Tests that the Trader class initializes correctly.
    """
    mock_client = mocker.patch('api.client.BinanceClient')
    trader = Trader(client=mock_client)
    assert trader.client is mock_client

def test_trader_buy_logic_success(mocker):
    """
    Tests the successful execution of the buy logic.
    """
    # ... setup mocks and state ...
    # ... call the method ...
    # ... assert the expected outcome ...
    pass
```

## Documentation Conventions

-   **Docstrings:** All modules, classes, and functions should have docstrings. Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstring formatting.
-   **Workflow Documentation:** When a change impacts the user workflow (e.g., adding a CLI command), the following files **must** be updated:
    -   `crypto-workflow.md`
    -   `crypto-monitoring-workflow.md`

## Commit Message Conventions

This project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This leads to more readable messages that are easy to follow when looking through the project history.

## Format

Each commit message consists of a **header**.

`<type>[optional scope]: <description>`

The **header** is mandatory and the **scope** of the header is optional.

## Type

Must be one of the following:

*   **feat**: A new feature
*   **fix**: A bug fix
*   **docs**: Documentation only changes
*   **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
*   **refactor**: A code change that neither fixes a bug nor adds a feature
*   **perf**: A code change that improves performance
*   **test**: Adding missing tests or correcting existing tests
*   **chore**: Changes to the build process or auxiliary tools and libraries such as documentation generation
*   **revert**: Reverts a previous commit

## Scope

The scope provides additional contextual information and is contained within parenthesis, e.g., `feat(parser): add ability to parse arrays`.

## Description

The description contains a concise summary of the change.

-   The entire commit message should be a single line.
-   Use the imperative, present tense: "change" not "changed" nor "changes".
-   Don't capitalize the first letter.
-   No dot (.) at the end.
-   Do not use backticks (`) in the commit message.

### Example Commit Message

```
feat(cli): add command to fetch order history
```

## Directory Structure

The project follows a standard structure for Python applications. All source code resides in the `src/` directory.

-   `src/api`: All direct interaction logic with external APIs (e.g., Binance).
-   `src/core`: Core application logic, such as data processing, calculations, and strategy implementation.
-   `main.py`: The main entry point for the CLI application.
-   `tests/`: Contains all the unit and integration tests.

### Test Directory Layout

-   **Directory Structure:** The `tests/` directory should mirror the structure of the `src/` directory. For a module at `src/core/trader.py`, its tests should be at `tests/core/test_trader.py`.

## Mocking and Patching

When writing tests, it's often necessary to mock external dependencies, especially API clients. This project uses `pytest-mock`, which provides the `mocker` fixture.

-   **Target for Patching:** Always patch where the object is *looked up*, not where it's defined. If `main.py` imports `BinanceClient` from `api.client`, you should patch it there.

    ```python
    # In a test file for a module that uses 'Trader'
    from core.trader import Trader

    def test_trader_action(mocker):
        # Patch the client where it is used by the Trader class
        mock_client = mocker.patch('api.client.BinanceClient')
        # ... rest of your test
    ```

## Style Conventions

- prefer `ruff` over `black`, `isort`, etc.
- use `pyproject.toml` for configuration
- use `src` layout
