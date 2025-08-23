# Makefile for AnimeLibrarian project

.PHONY: help lint format check typecheck test test-mock install clean

help:  ## Show this help message
	@echo "AnimeLibrarian Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

lint:  ## Run all linters (Python and Markdown) with fixes
	@uv run python scripts/lint.py

format:  ## Format Python code with ruff format
	@echo "🔧 Formatting Python code..."
	@uv run ruff format src tests

format-md:  ## Format Markdown files with mdformat
	@echo "📝 Formatting Markdown files..."
	@uv run python scripts/lint_markdown.py

check:  ## Check Python code with ruff (no fixes)
	@echo "🔍 Checking Python code..."
	@uv run ruff check src tests

check-md:  ## Check Markdown files (no fixes)
	@echo "🔍 Checking Markdown files..."
	@uv run python scripts/lint_markdown.py --check

typecheck:  ## Run type checking with ty
	@echo "🔍 Running type checking with ty..."
	@uv run ty check

test:  ## Run all tests
	@echo "🧪 Running tests..."
	@uv run pytest -v

test-mock:  ## Run mock server tests only
	@echo "🧪 Running mock server tests..."
	@uv run pytest tests/test_mock_server.py tests/test_integration_with_mock_server.py -v

install:  ## Install dependencies
	@echo "📦 Installing dependencies..."
	@uv sync

clean:  ## Clean up generated files
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.coverage" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✨ Clean complete"