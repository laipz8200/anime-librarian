#!/usr/bin/env python
"""
Markdown lint script for AnimeLibrarian project.

This script runs mdformat on all Markdown files in the project.
"""

import subprocess
import sys
from pathlib import Path


def find_markdown_files(project_root: Path) -> list[str]:
    """
    Find all markdown files in the project, excluding common directories.

    Args:
        project_root: Root directory of the project

    Returns:
        List of markdown file paths
    """
    exclude_dirs = {
        ".venv",
        "venv",
        "node_modules",
        ".git",
        "__pycache__",
        ".pytest_cache",
    }
    markdown_files = []

    for ext in ["*.md", "**/*.md"]:
        for f in project_root.glob(ext):
            # Skip files in excluded directories
            if not any(part in exclude_dirs for part in f.parts):
                markdown_files.append(str(f))

    return sorted(set(markdown_files))  # Remove duplicates and sort


def run_mdformat(files: list[str], check_only: bool = False) -> int:
    """
    Run mdformat on the specified files.

    Args:
        files: List of file paths to format
        check_only: If True, only check files without modifying them

    Returns:
        Exit code from mdformat
    """
    if not files:
        print("📝 No Markdown files found to format")
        return 0

    cmd = ["uv", "run", "mdformat"]
    if check_only:
        cmd.append("--check")
    cmd.extend(files)

    action = "🔍 Checking" if check_only else "🔧 Formatting"
    print(f"{action} {len(files)} Markdown file(s)...")
    print(f"   Running: mdformat{' --check' if check_only else ''} <files>")
    print("-" * 60)

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode == 0:
        if check_only:
            print("✅ All Markdown files are properly formatted")
        else:
            print("✅ Markdown formatting completed successfully")
    else:
        if check_only:
            print("❌ Some Markdown files need formatting")
            print("   Run 'make format-md' to fix them")
        else:
            print(f"❌ Markdown formatting failed with exit code {result.returncode}")

    return result.returncode


def main():
    """Main function to run markdown linting."""
    print("=" * 60)
    print("📝 AnimeLibrarian Markdown Linting Script")
    print("=" * 60)

    # Check if --check flag is provided
    check_only = "--check" in sys.argv

    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    print(f"📁 Working directory: {project_root}")
    print()

    # Find markdown files
    markdown_files = find_markdown_files(project_root)

    if markdown_files:
        print(f"📋 Found {len(markdown_files)} Markdown file(s):")
        for f in markdown_files[:5]:  # Show first 5 files
            print(f"   • {Path(f).relative_to(project_root)}")
        if len(markdown_files) > 5:
            print(f"   ... and {len(markdown_files) - 5} more")
        print()

    # Run mdformat
    exit_code = run_mdformat(markdown_files, check_only)

    print("=" * 60)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
