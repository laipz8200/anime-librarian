# Makefile for AnimeLibrarian project

.PHONY: help lint format check type-check test install clean

help:  ## Show this help message
	@echo "AnimeLibrarian Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

lint:  ## Run all linters with Python-only fixes
	@echo "============================================================"
	@echo "🚀 AnimeLibrarian Lint"
	@echo "============================================================"
	@echo ""
	@echo "🔧 Formatting Python code"
	@uv run ruff format src tests
	@echo ""
	@echo "🔧 Applying Ruff autofixes"
	@uv run ruff check --fix src tests
	@echo ""
	@echo "🔍 Verifying Python code"
	@uv run ruff check src tests
	@echo ""
	@echo "============================================================"
	@echo "✨ Lint complete"
	@echo "============================================================"

format:  ## Format Python code with ruff format
	@echo "🔧 Formatting Python code..."
	@uv run ruff format src tests

check:  ## Check Python code with ruff (no fixes)
	@echo "🔍 Checking Python code..."
	@uv run ruff check src tests

type-check:  ## Run type checking with basedpyright
	@echo "🔍 Running type checking with basedpyright..."
	@uv run basedpyright

test:  ## Run all tests
	@echo "🧪 Running tests..."
	@uv run pytest -v

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
