# Vulture Configuration

This project uses [vulture](https://github.com/jendrikseipp/vulture) to detect unused code.

## Configuration Strategy

Instead of maintaining a hard-to-update whitelist file, we use:

1. **High confidence threshold (85%)** - Only flags confident unused code while avoiding false positives
2. **Smart decorator ignoring** - Automatically ignores code used by:
   - `@app.command` (Typer CLI commands)
   - `@pytest.fixture` (Test fixtures)
   - `@patch` (Test mocking)
   - `@given` (Hypothesis property tests)
3. **Pattern-based ignoring** - Ignores test-related patterns automatically

## When to Use Inline Comments

Use `# noqa: vulture` only for:

- **TypedDict classes** - API response schemas that define structure but fields may not be directly accessed
- **Config fields** - Loaded from TOML but might not be used yet
- **Entry points** - Functions that are called externally but vulture can't detect

## Example Usage

```python
class ApiResponse(TypedDict):  # noqa: vulture
    """API response schema - fields used dynamically"""
    field1: str
    field2: int

@app.command()  # Automatically ignored by vulture config
def cli_command():
    pass

def regular_function():
    unused_var = "this will be caught"  # Will be flagged if unused
```

## Configuration Location

See `.pre-commit-config.yaml` for the vulture hook configuration.
