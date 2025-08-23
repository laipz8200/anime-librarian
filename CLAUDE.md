# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AnimeLibrarian is an AI-powered CLI tool that automatically renames and organizes video files using LLM technology through Dify workflows. Follows DDD and Clean Architecture with comprehensive type safety.

## Development Workflow

**ALWAYS follow this workflow:**

### 1. Apply TDD

- **Red**: Write failing tests first
- **Green**: Implement minimum code to pass
- **Refactor**: Improve while keeping tests green

### 2. Ensure Quality

- Run `make lint` and `make test`
- Fix all issues before proceeding

### 3. Documentation

- **DO NOT create new docs without explicit request**
- Only update existing docs when necessary

## Key Principles

- **DDD**: Domain-Driven Design
- **TDD**: Test-Driven Development
- **Clean Architecture**: Dependency injection, Protocol-based abstractions
- **Type Safety**: Always use type hints, avoid `Any`
- **SOLID**: Apply all SOLID principles

## Development Commands

See `make help` for all commands. Key ones:

- `make lint` - Format and fix code
- `make test` - Run all tests
- `uv add <package>` - Add dependencies

## Testing with Mock Server

```python
from tests.fixtures.mock_server_fixtures import run_mock_server
with run_mock_server() as server_url:
    # Test code here
```

## Architecture

### Module Structure

- **`main.py`**: Entry point with DI setup
- **`core.py`**: Main orchestrator (`AnimeLibrarian` class)
- **`types.py`**: Protocol definitions
- **`models.py`**: Pydantic models
- **`errors.py`**: Domain exceptions
- **`file_renamer.py`**: Core business logic

### Key Patterns

- **Protocol-First**: Define in `types.py` before implementing
- **Pydantic Validation**: All external data
- **Domain Exceptions**: Use `errors.py`
- **Environment Config**: Via `ConfigProvider`

## Code Style

- Google docstrings
- `@property` for computed attributes
- Implement `__repr__`, `__str__`
- Composition over inheritance

## Integration Points

### Dify AI

- Endpoint: `DIFY_API_ENDPOINT` env var
- API key: `DIFY_API_KEY` env var

### Supported Formats

- Video: `.mkv`, `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.mpg`, `.mpeg`
- Subtitle: `.srt`, `.ass`, `.ssa`, `.sub`, `.idx`, `.vtt`

## Testing

- Mock server: `tests/mock_dify_server.py`
- 98+ tests with comprehensive coverage
- See `tests/README_MOCK_SERVER.md` for mock server details
