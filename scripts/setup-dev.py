#!/usr/bin/env python3
r"""
Development Environment Setup Script

This script sets up the complete development environment for the Crypto AI Assistant.
It handles virtual environment creation, dependency installation, and tool verification.

Usage:
    python scripts/setup-dev.py

Or on Windows:
    python scripts\setup-dev.py
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, check: bool = True, shell: bool = True) -> subprocess.CompletedProcess | subprocess.CalledProcessError:
    """Run a command and return the result."""
    print(f"📋 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=shell, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def check_python_version() -> None:
    """Verify Python version meets requirements."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python 3.10+ required, found {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")


def setup_virtual_environment() -> None:
    """Create and activate virtual environment."""
    print("🏗️ Setting up virtual environment...")

    venv_path = Path("venv")
    if not venv_path.exists():
        run_command(f"{sys.executable} -m venv venv")
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")


def get_pip_command() -> str:
    """Get the correct pip command for the current platform."""
    if os.name == "nt":  # Windows
        return "venv\\Scripts\\python.exe -m pip"
    else:  # Unix/Linux/Mac
        return "venv/bin/python -m pip"


def install_dependencies() -> None:
    """Install project dependencies."""
    print("📦 Installing dependencies...")

    pip_cmd = get_pip_command()

    # Upgrade pip first
    run_command(f"{pip_cmd} install --upgrade pip")

    # Install project in editable mode with dev dependencies
    run_command(f'{pip_cmd} install -e ".[dev,test]"')

    # Install pre-commit hooks
    if os.name == "nt":  # Windows
        precommit_cmd = "venv\\Scripts\\pre-commit.exe install"
    else:  # Unix/Linux/Mac
        precommit_cmd = "venv/bin/pre-commit install"

    run_command(precommit_cmd)
    print("✅ Dependencies installed and pre-commit hooks configured")


def verify_installation() -> None:
    """Verify that all tools are properly installed."""
    print("🔍 Verifying installation...")

    if os.name == "nt":  # Windows
        python_cmd = "venv\\Scripts\\python.exe"
    else:  # Unix/Linux/Mac
        python_cmd = "venv/bin/python"

    # Test imports
    test_imports = [
        "import sys; print(f'Python: {sys.version_info[:2]}')",
        "import ruff; print('✅ ruff')",
        "import pytest; print('✅ pytest')",
        "import mypy; print('✅ mypy')",
        "import src.api.client; print('✅ src imports')",
    ]

    for test_import in test_imports:
        run_command(f'{python_cmd} -c "{test_import}"', check=False)


def create_development_shortcuts() -> None:
    """Create convenient development command shortcuts."""
    print("🔧 Creating development shortcuts...")

    # Create a simple dev runner script
    dev_script_content = '''#!/usr/bin/env python3
"""Development task runner - simple automation for common tasks."""

import subprocess
import sys
import os

def run_cmd(cmd: str) -> None:
    """Run command with proper virtual environment."""
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\\\Scripts\\\\python.exe"
        precommit_cmd = "venv\\\\Scripts\\\\pre-commit.exe"
    else:  # Unix/Linux/Mac
        python_cmd = "venv/bin/python"
        precommit_cmd = "venv/bin/pre-commit"

    commands = {
        "test": f"{python_cmd} -m pytest",
        "test-fast": f"{python_cmd} -m pytest -x --tb=short",
        "cov": f"{python_cmd} -m pytest --cov=src --cov-report=html",
        "lint": f"ruff check . --fix && ruff format .",
        "type": f"{python_cmd} -m mypy src/ tests/",
        "check": f"{precommit_cmd} run --all-files",
        "clean": "find . -type d -name __pycache__ -delete 2>/dev/null || true",
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("🚀 Available commands:")
        for name, cmd in commands.items():
            print(f"  python scripts/dev.py {name:<10} - {cmd}")
        sys.exit(1)

    task = sys.argv[1]
    subprocess.run(commands[task], shell=True)
'''

    with open("scripts/dev.py", "w") as f:
        f.write(dev_script_content)

    print("✅ Created scripts/dev.py for common tasks")


def main() -> None:
    """Main setup process."""
    print("🚀 Setting up Crypto AI Assistant development environment...")
    print("=" * 60)

    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    check_python_version()
    setup_virtual_environment()
    install_dependencies()
    verify_installation()
    create_development_shortcuts()

    print("\n" + "=" * 60)
    print("🎉 Development environment setup complete!")
    print("\n📋 Next steps:")
    print("   1. Activate virtual environment:")
    if os.name == "nt":  # Windows
        print("      .\\venv\\Scripts\\Activate.ps1")
    else:  # Unix/Linux/Mac
        print("      source venv/bin/activate")
    print("   2. Run tests: python scripts/dev.py test")
    print("   3. Run quality checks: python scripts/dev.py check")
    print("   4. See all commands: python scripts/dev.py")


if __name__ == "__main__":
    main()
