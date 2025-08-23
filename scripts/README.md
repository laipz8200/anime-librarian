# Development Scripts

This directory contains helpful scripts for development and maintenance of the AnimeLibrarian project.

## Lint Scripts

### Python Script (`lint.py`)

A Python-based linting script that runs both formatting and checking:

```bash
# Run directly with Python
uv run python scripts/lint.py

# Or make it executable and run
./scripts/lint.py
```

### Shell Script (`lint.sh`)

A bash script alternative for Unix-like systems:

```bash
# Make executable (first time only)
chmod +x scripts/lint.sh

# Run the script
./scripts/lint.sh
```

### Using Make

The easiest way to run linting is through the Makefile:

```bash
# Run full linting (format + check with fixes)
make lint

# Just format code
make format

# Just check code (no fixes)
make check
```

## What the Lint Scripts Do

1. **Format Code**: Runs `ruff format` to automatically format all Python code according to project standards
1. **Fix Issues**: Runs `ruff check --fix` to automatically fix common issues
1. **Report Remaining Issues**: Shows any issues that couldn't be automatically fixed

## Common Remaining Issues

Some issues can't be automatically fixed and require manual intervention:

- **E402**: Module level imports not at top of file (often needed for path manipulation)
- **E501**: Line too long (may require restructuring code)
- **SIM117**: Nested `with` statements (can be combined but needs careful review)

## Other Make Commands

```bash
# Show all available commands
make help

# Run all tests
make test

# Run mock server tests only
make test-mock

# Install/update dependencies
make install

# Clean up generated files
make clean
```
