#!/usr/bin/env python3
"""
Trading Safety Pre-commit Hook

Validates common trading safety patterns in the codebase.
"""

import re
import sys
from pathlib import Path


def check_trading_safety() -> bool:
    """Check for common trading pitfalls and safety issues."""
    issues = []

    # Check source files for trading safety patterns
    for py_file in Path("src").rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Skip files that can't be decoded as UTF-8
            continue

        # Check for hardcoded values that should be configurable
        if re.search(r"quantity\s*=\s*[0-9]+\.?[0-9]*(?![0-9a-zA-Z_])", content):
            issues.append(f"{py_file}: Hardcoded quantity values detected - should use config")

        # Check for API calls in order placement without error handling
        if "place_order" in content and "client." in content:
            # Look for the specific pattern of order placement without try/except
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "client." in line and any(keyword in line for keyword in ["place", "order", "buy", "sell"]):
                    # Check if this line or nearby lines have try/catch
                    context = "\n".join(lines[max(0, i - 5) : min(len(lines), i + 5)])
                    if "try:" not in context and "except" not in context:
                        issues.append(f"{py_file}:{i + 1}: Order placement without error handling")

        # Check for missing precision handling in financial calculations
        if ("price" in content or "amount" in content or "quantity" in content) and "float(" in content:
            # Look for financial calculations without proper precision
            if not any(keyword in content for keyword in ["round(", "Decimal", ":.2f", ":.4f", ":.8f"]):
                issues.append(f"{py_file}: Financial calculations without precision handling")

        # Check for missing rate limit handling in HTTP requests
        if "requests.post" in content and "perplexity" in py_file.name.lower():
            if "sleep" not in content and "retry" not in content:
                issues.append(f"{py_file}: HTTP requests without rate limiting")

    if issues:
        print("WARNING: Trading Safety Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("SUCCESS: Trading safety checks passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if check_trading_safety() else 1)
