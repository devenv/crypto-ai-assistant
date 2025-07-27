#!/usr/bin/env python3
"""Development task runner - simple automation for common tasks."""

import os
import subprocess
import sys


def run_cmd(cmd: str) -> None:
    """Run command with proper virtual environment."""
    if os.name == "nt":  # Windows
        python_cmd = "venv\\Scripts\\python.exe"
    else:  # Unix/Linux/Mac
        python_cmd = "venv/bin/python"

    commands = {
        "test": f"{python_cmd} -m pytest",
        "test-fast": f"{python_cmd} -m pytest -x --tb=short",
        "cov": f"{python_cmd} -m pytest --cov=src --cov-report=html",
        "lint": "ruff check . --fix && ruff format .",
        "type": f"{python_cmd} -m mypy src/ tests/",
        "check": "python scripts/staged-check.py",
        "clean": "find . -type d -name __pycache__ -delete 2>/dev/null || true",
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("🚀 Available commands:")
        for name, cmd in commands.items():
            print(f"  python scripts/dev.py {name:<10} - {cmd}")
        sys.exit(1)

    task = sys.argv[1]
    subprocess.run(commands[task], shell=True)


if __name__ == "__main__":
    run_cmd("")
