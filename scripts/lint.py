#!/usr/bin/env python
"""
Lint script for AnimeLibrarian project.

This script runs ruff format, ruff check, and mdformat with automatic fixes
to maintain code quality and consistency for Python and Markdown files.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> int:
    """
    Run a command and return its exit code.

    Args:
        cmd: Command to run as list of strings
        description: Description of what the command does

    Returns:
        Exit code from the command
    """
    print(f"\n🔧 {description}")
    print(f"   Running: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode == 0:
        print(f"✅ {description} completed successfully")
    else:
        print(f"❌ {description} failed with exit code {result.returncode}")

    return result.returncode


def main():
    """Main function to run linting tools."""
    print("=" * 60)
    print("🚀 AnimeLibrarian Linting Script")
    print("=" * 60)

    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent

    # Change to project root directory
    import os

    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")

    # Define paths to lint
    paths_to_lint = [
        "src",
        "tests",
    ]

    # Find all markdown files (excluding .venv and other common directories)
    markdown_files = []
    exclude_dirs = {
        ".venv",
        "venv",
        "node_modules",
        ".git",
        "__pycache__",
        ".pytest_cache",
    }
    for ext in ["*.md", "**/*.md"]:
        for f in project_root.glob(ext):
            # Skip files in excluded directories
            if not any(part in exclude_dirs for part in f.parts):
                markdown_files.append(str(f))
    markdown_files = sorted(set(markdown_files))  # Remove duplicates and sort

    # Track if any command fails
    any_failed = False

    # Run ruff format
    format_cmd = ["uv", "run", "ruff", "format", *paths_to_lint]
    exit_code = run_command(format_cmd, "Formatting Python code with ruff format")
    if exit_code != 0:
        any_failed = True

    # Run ruff check with fix
    check_cmd = ["uv", "run", "ruff", "check", "--fix", *paths_to_lint]
    exit_code = run_command(check_cmd, "Running ruff check with automatic fixes")
    if exit_code != 0:
        any_failed = True

    # Run ruff check without fix to show remaining issues
    check_remaining_cmd = ["uv", "run", "ruff", "check", *paths_to_lint]
    exit_code = run_command(check_remaining_cmd, "Checking for remaining Python issues")

    # Run mdformat on markdown files if any exist
    if markdown_files:
        mdformat_cmd = ["uv", "run", "mdformat", *markdown_files]
        md_exit_code = run_command(
            mdformat_cmd, "Formatting Markdown files with mdformat"
        )
        if md_exit_code != 0:
            any_failed = True
    else:
        print("\n📝 No Markdown files found to format")

    # Summary
    print("\n" + "=" * 60)
    if any_failed:
        print("⚠️  Some linting steps had issues")
        print("   Please review the output above")
    else:
        if exit_code == 0:
            print("✨ All linting completed successfully!")
            print("   Your code is clean and formatted")
        else:
            print("⚠️  Code is formatted but some issues remain")
            print("   Please review the remaining issues above")
    print("=" * 60)

    # Return non-zero if any issues remain
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
