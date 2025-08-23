#!/bin/bash
# Lint script for AnimeLibrarian project
# This script runs ruff format and ruff check with automatic fixes

set -e  # Exit on error

echo "======================================================"
echo "🚀 AnimeLibrarian Linting Script"
echo "======================================================"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project root is parent of scripts directory
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root
cd "$PROJECT_ROOT"
echo "📁 Working directory: $PROJECT_ROOT"

# Define paths to lint
PATHS="src tests"

echo ""
echo "🔧 Formatting code with ruff format"
echo "   Running: uv run ruff format $PATHS"
echo "------------------------------------------------------"
uv run ruff format $PATHS

echo ""
echo "✅ Formatting completed"

echo ""
echo "🔧 Running ruff check with automatic fixes"
echo "   Running: uv run ruff check --fix $PATHS"
echo "------------------------------------------------------"
uv run ruff check --fix $PATHS || true

echo ""
echo "🔍 Checking for remaining issues"
echo "   Running: uv run ruff check $PATHS"
echo "------------------------------------------------------"
if uv run ruff check $PATHS; then
    echo ""
    echo "======================================================"
    echo "✨ All linting completed successfully!"
    echo "   Your code is clean and formatted"
    echo "======================================================"
    exit 0
else
    echo ""
    echo "======================================================"
    echo "⚠️  Code is formatted but some issues remain"
    echo "   Please review the issues above"
    echo "======================================================"
    exit 1
fi