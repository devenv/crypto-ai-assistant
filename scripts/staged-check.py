#!/usr/bin/env python3
"""
Staged Quality Check Runner

Runs quality checks in stages to provide fast feedback and better error isolation.
Each stage must pass before proceeding to the next.

Usage:
    python scripts/staged-check.py [--stage STAGE] [--fix]

Stages:
    env     - Environment and dependency verification
    arch    - Architectural integrity validation
    format  - Code formatting and linting
    types   - Static type checking
    tests   - Unit tests and coverage
    all     - Run all stages (default)
"""

import argparse
import ast
import os
import subprocess
import sys
import time
from pathlib import Path

# Set UTF-8 encoding for Windows
if os.name == "nt":
    os.environ["PYTHONIOENCODING"] = "utf-8"


class QualityChecker:
    """Orchestrates staged quality checks with detailed feedback."""

    def __init__(self, fix_issues: bool = False, verbose: bool = True):
        self.fix_issues = fix_issues
        self.verbose = verbose
        self.python_cmd = self._get_python_cmd()
        self.precommit_cmd = self._get_precommit_cmd()

    def _get_python_cmd(self) -> str:
        """Get the correct Python command for virtual environment."""
        if os.name == "nt":  # Windows
            return "venv\\Scripts\\python.exe"
        else:  # Unix/Linux/Mac
            return "venv/bin/python"

    def _get_precommit_cmd(self) -> str:
        """Get the correct pre-commit command."""
        if os.name == "nt":  # Windows
            return "venv\\Scripts\\pre-commit.exe"
        else:  # Unix/Linux/Mac
            return "venv/bin/pre-commit"

    def _get_ruff_cmd(self) -> str:
        """Get the correct ruff command."""
        if os.name == "nt":  # Windows
            return "venv\\Scripts\\ruff.exe"
        else:  # Unix/Linux/Mac
            return "venv/bin/ruff"

    def run_command(self, cmd: str, stage: str, description: str) -> bool:
        """Run a command and provide structured feedback."""
        print(f"\n[RUN] {stage.upper()}: {description}")
        print(f"   Command: {cmd}")

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            duration = time.time() - start_time
            print(f"   [PASS] Passed ({duration:.1f}s)")

            if self.verbose and result.stdout:
                # Show brief output for successful commands
                lines = result.stdout.strip().split("\n")
                if len(lines) <= 3:
                    print(f"   Output: {result.stdout.strip()}")
                else:
                    print(f"   Output: {lines[0]}... ({len(lines)} lines)")

            return True

        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            print(f"   [FAIL] Failed ({duration:.1f}s)")
            print(f"   Exit code: {e.returncode}")

            if e.stdout:
                print(f"   Stdout:\n{self._indent_output(e.stdout)}")
            if e.stderr:
                print(f"   Stderr:\n{self._indent_output(e.stderr)}")

            return False

        except subprocess.TimeoutExpired:
            print("   ⏰ Timeout (5 minutes)")
            return False

    def _indent_output(self, output: str) -> str:
        """Indent command output for better readability."""
        lines = output.strip().split("\n")
        return "\n".join(f"      {line}" for line in lines)

    def stage_environment(self) -> bool:
        """Stage 1: Verify environment and basic dependencies."""
        print("\n" + "=" * 60)
        print("STAGE 1: Environment Verification")
        print("=" * 50)

        checks = [
            (f"{self.python_cmd} --version", "env", "Python version check"),
            (f"{self.python_cmd} -c \"import src.api.client; print('Core imports OK')\"", "env", "Core module imports"),
            (f"{self.python_cmd} -c \"import ruff, pytest, mypy; print('Dev tools available')\"", "env", "Development tools"),
        ]

        for cmd, stage, desc in checks:
            if not self.run_command(cmd, stage, desc):
                print("\n[FAIL] Environment check failed. Run: python scripts/setup-dev.py")
                return False

        return True

    def stage_architecture(self) -> bool:
        """Stage 2: Architectural integrity validation."""
        print("\n" + "=" * 60)
        print("STAGE 2: Architectural Integrity")
        print("=" * 60)

        issues = []
        issues.extend(self._check_import_patterns())
        issues.extend(self._check_package_structure())
        issues.extend(self._check_entry_points())

        if issues:
            print(f"   [FAIL] Found {len(issues)} architectural violations:")
            for i, issue in enumerate(issues, 1):
                print(f"      {i:2d}. {issue}")

            if self.fix_issues:
                print("   💡 Architectural fixes require manual intervention")
                print("   💡 See .cursor/rules/ai-developer.mdc for guidance")
            else:
                print("   💡 Architectural violations must be fixed manually")
                print("   💡 See .cursor/rules/ai-developer.mdc for patterns")

            return False
        else:
            print("   [PASS] Architectural integrity verified")
            return True

    def _check_import_patterns(self) -> list[str]:
        """Check import patterns across the codebase."""
        issues = []

        # Check src/ modules use direct imports (not src. prefix)
        for file_path in Path("src").rglob("*.py"):
            if file_path.name == "__init__.py":
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        if node.module.startswith("src."):
                            issues.append(f'{file_path}: Bad import "{node.module}" (remove src. prefix)')

            except (SyntaxError, UnicodeDecodeError):
                # Skip files that can't be parsed
                continue

        return issues

    def _check_package_structure(self) -> list[str]:
        """Check required package structure exists."""
        issues = []

        required_files = {
            "src/__init__.py": "Source package marker",
            "src/api/__init__.py": "API package marker",
            "src/core/__init__.py": "Core package marker",
            "tests/conftest.py": "Test configuration",
            "pyproject.toml": "Package configuration",
            "main.py": "CLI entry point",
        }

        for file_path, description in required_files.items():
            if not Path(file_path).exists():
                issues.append(f"Missing: {file_path} ({description})")

        return issues

    def _check_entry_points(self) -> list[str]:
        """Check that entry points work correctly."""
        issues = []

        try:
            # Test main app import
            subprocess.run([self.python_cmd, "-c", 'from main import app; print("OK")'], check=True, capture_output=True, text=True, timeout=10)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            issues.append("Main entry point import failing")

        try:
            # Test core module imports (using proper import pattern)
            subprocess.run(
                [self.python_cmd, "-c", 'import sys; sys.path.insert(0, "src"); from core.config import get_config; print("OK")'],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            issues.append("Core module imports failing")

        return issues

    def stage_formatting(self) -> bool:
        """Stage 3: Code formatting and linting."""
        print("\n" + "=" * 60)
        print("STAGE 3: Code Formatting & Linting")
        print("=" * 60)

        ruff_cmd = self._get_ruff_cmd()

        if self.fix_issues:
            # Auto-fix mode with aggressive fixing
            checks = [
                (f"{ruff_cmd} format .", "format", "Auto-format code"),
                (f"{ruff_cmd} check . --fix --unsafe-fixes", "lint", "Auto-fix all fixable issues"),
                (f"{ruff_cmd} check . --output-format=concise", "lint", "Show remaining issues"),
            ]
        else:
            # Check-only mode
            checks = [
                (f"{ruff_cmd} format . --check", "format", "Code formatting check"),
                (f"{ruff_cmd} check . --output-format=concise", "lint", "Linting check"),
            ]

        for cmd, stage, desc in checks:
            if not self.run_command(cmd, stage, desc):
                if not self.fix_issues:
                    print("\n💡 Try running with --fix to automatically resolve formatting issues")
                return False

        return True

    def stage_types(self) -> bool:
        """Stage 4: Static type checking."""
        print("\n" + "=" * 60)
        print("STAGE 4: Static Type Checking")
        print("=" * 60)

        # Run MyPy first
        cmd = f"{self.python_cmd} -m mypy src/ tests/"
        if not self.run_command(cmd, "types", "MyPy static type analysis"):
            print("\n💡 MyPy type checking failed. Check CONVENTIONS.md for TypedDict guidance")
            return False

        # Run Pyright for strict type validation (MUST PASS - zero tolerance)
        # Check if npx/pyright is available first
        try:
            subprocess.run(["npx", "--version"], capture_output=True, check=True, timeout=5)
            npx_available = True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            npx_available = False

        if npx_available:
            cmd = "npx pyright"
            if not self.run_command(cmd, "types", "Pyright strict type validation"):
                print("\n💡 Pyright type checking FAILED - ZERO TOLERANCE for type issues")
                print("💡 All errors and warnings must be fixed before proceeding")
                print("💡 Check @ai-developer.mdc for type fixing patterns")
                return False
        else:
            print("   [WARN] Pyright not available (npx/node not found)")
            print("   [WARN] Install Node.js to enable strict pyright type checking")
            # Don't fail if pyright is not available, but warn strongly

        return True

    def stage_tests(self) -> bool:
        """Stage 5: Unit tests and coverage."""
        print("\n" + "=" * 60)
        print("STAGE 5: Tests & Coverage")
        print("=" * 60)

        # Fast test run first
        if not self.run_command(f"{self.python_cmd} -m pytest --tb=short -x", "test", "Fast test run (fail on first error)"):
            print("\n💡 Tests failing. Fix issues before checking coverage")
            return False

        # Full coverage check
        if not self.run_command(f"{self.python_cmd} -m pytest --cov=src --cov-report=term-missing", "coverage", "Full test suite with coverage"):
            print("\n💡 Coverage below threshold. See ai-developer.mdc Step 1.4.1 for guidance")
            return False

        return True

    def run_stage(self, stage: str) -> bool:
        """Run a specific stage."""
        stage_map = {
            "env": self.stage_environment,
            "arch": self.stage_architecture,
            "format": self.stage_formatting,
            "types": self.stage_types,
            "tests": self.stage_tests,
        }

        if stage not in stage_map:
            print(f"[ERROR] Unknown stage: {stage}")
            return False

        return stage_map[stage]()

    def run_all_stages(self) -> bool:
        """Run all quality check stages in order."""
        stages = ["env", "arch", "format", "types", "tests"]

        print("🚀 Running staged quality checks...")
        start_time = time.time()

        for stage in stages:
            if not self.run_stage(stage):
                duration = time.time() - start_time
                print(f"\n💥 Quality checks failed at {stage.upper()} stage ({duration:.1f}s total)")
                print("Fix the issues above and re-run: python scripts/staged-check.py")
                return False

        duration = time.time() - start_time
        print(f"\n🎉 All quality checks passed! ({duration:.1f}s total)")
        print("Ready to commit your changes.")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Staged quality check runner")
    parser.add_argument("--stage", choices=["env", "arch", "format", "types", "tests", "all"], default="all", help="Run specific stage (default: all)")
    parser.add_argument("--fix", action="store_true", help="Automatically fix formatting and linting issues")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    checker = QualityChecker(fix_issues=args.fix, verbose=not args.quiet)

    if args.stage == "all":
        success = checker.run_all_stages()
    else:
        success = checker.run_stage(args.stage)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
