# Crypto AI Assistant - Development Makefile
#
# Common development tasks made simple
#
# Usage:
#   make setup     - Set up development environment
#   make check     - Run all quality checks
#   make test      - Run tests
#   make fix       - Auto-fix formatting and linting
#   make clean     - Clean build artifacts

.PHONY: help setup check test test-fast fix lint format type clean install

# Default target
help:
	@echo "🚀 Crypto AI Assistant Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup     - Set up complete development environment"
	@echo "  make install   - Install dependencies only"
	@echo ""
	@echo "Quality Checks:"
	@echo "  make check     - Run all staged quality checks"
	@echo "  make fix       - Auto-fix formatting and linting issues"
	@echo "  make lint      - Run linting checks only"
	@echo "  make format    - Run formatting checks only"
	@echo "  make type      - Run type checking only"
	@echo ""
	@echo "Testing:"
	@echo "  make test      - Run full test suite with coverage"
	@echo "  make test-fast - Run tests with fail-fast mode"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean     - Clean build artifacts and cache"
	@echo ""
	@echo "💡 For more advanced options, see scripts/staged-check.py --help"

# Environment setup
setup:
	@echo "🛠️ Setting up development environment..."
	python scripts/setup-dev.py

install:
	@echo "📦 Installing dependencies..."
	python -m pip install -e ".[dev,test]"

# Quality checks
check:
	@echo "🔍 Running staged quality checks..."
	python scripts/staged-check.py

fix:
	@echo "🔧 Auto-fixing formatting and linting issues..."
	python scripts/staged-check.py --stage format --fix

lint:
	@echo "🧹 Running linting checks..."
	python scripts/staged-check.py --stage format

format:
	@echo "🎨 Checking code formatting..."
	ruff format . --check

type:
	@echo "📝 Running type checks..."
	python scripts/staged-check.py --stage types

# Testing
test:
	@echo "🧪 Running full test suite..."
	python scripts/staged-check.py --stage tests

test-fast:
	@echo "⚡ Running fast tests..."
	python scripts/dev.py test-fast

# Maintenance
clean:
	@echo "🧽 Cleaning build artifacts..."
	@find . -type d -name "__pycache__" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -delete 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -delete 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -delete 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf build/ dist/ *.egg-info/ 2>/dev/null || true
	@echo "✅ Clean complete"

# Quick shortcuts for common workflows
dev-setup: setup
	@echo "🎉 Development environment ready!"

pre-commit: fix check
	@echo "✅ Ready to commit!"
