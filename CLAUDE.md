# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AnimeLibrarian is an AI-powered CLI tool that automatically renames and organizes video files using LLM technology through Dify workflows. The codebase follows Domain-Driven Design (DDD) and Clean Architecture principles with comprehensive type safety.

## Development Commands

### Package Management

```bash
uv add <package>        # Add new dependency
uv sync                 # Sync dependencies with lock file
```

### Quality Checks

```bash
uv run ruff check .            # Run linting
uv run ruff format .           # Format code
uv run pytest                  # Run tests
uv run pytest --cov            # Run tests with coverage
uv run pytest tests/test_core.py::TestAnimeLibrarian::test_specific  # Run single test
uv run mypy .                  # Type checking (consider using pyrefly as well)
```

### Pre-commit

```bash
pre-commit install      # Install git hooks
pre-commit run --all-files  # Run all checks manually
```

## Architecture

### Core Design Patterns

1. **Dependency Injection**: All dependencies are injected through constructors using Protocol interfaces
2. **Protocol-Based Architecture**: Use protocols (`HttpClient`, `ArgumentParser`, `InputReader`, `OutputWriter`, `ConfigProvider`) for abstraction
3. **Factory Pattern**: Create instances through factory functions when appropriate
4. **Repository Pattern**: Abstract data access behind interfaces

### Module Structure

- **`main.py`**: Application entry point with dependency injection setup
- **`core.py`**: Main orchestrator (`AnimeLibrarian` class) implementing the workflow
- **`types.py`**: Protocol definitions - all new abstractions should be defined here
- **`models.py`**: Pydantic models for data validation and API responses
- **`errors.py`**: Custom domain exceptions - add new domain-specific exceptions here
- **`file_renamer.py`**: Core business logic for file operations and AI integration

### Key Architectural Decisions

1. **Protocol-First Development**: Define protocols in `types.py` before implementing concrete classes
2. **Pydantic for Data Validation**: All external data should be validated through Pydantic models
3. **Custom Exceptions**: Use domain-specific exceptions from `errors.py` rather than generic ones
4. **Configuration via Environment**: All configuration through environment variables via `ConfigProvider`

## Development Guidelines

### Type Safety Requirements

- **Always use type hints** - avoid `Any` type
- **Use protocols for abstractions** instead of abstract base classes
- **Define type aliases** for complex types in `types.py`
- **Validate external data** with Pydantic models

### Testing Approach

Follow TDD cycle:

1. Write failing test in appropriate `tests/test_*.py` file
2. Implement minimal code to pass
3. Refactor while keeping tests green

Test naming convention: `test_<module>_<function>_<scenario>`

### Error Handling

- Create domain-specific exceptions in `errors.py`
- Catch and re-raise with context at appropriate layers
- Log errors using loguru logger configuration

### Code Style

- Google-style docstrings (enforced by ruff)
- Use `@property` for computed attributes
- Implement special methods (`__repr__`, `__str__`) for domain objects
- Prefer composition over inheritance

## Integration Points

### Dify AI Workflow

- API endpoint configured via `DIFY_API_ENDPOINT` environment variable
- API key via `DIFY_API_KEY`
- Workflow handles filename parsing and media identification

### File Processing

- Supports video formats: `.mkv`, `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.mpg`, `.mpeg`
- Subtitle formats: `.srt`, `.ass`, `.ssa`, `.sub`, `.idx`, `.vtt`

## Important Notes

- The codebase already follows DDD and Clean Architecture - maintain these patterns
- All new features should include comprehensive tests
- Use dependency injection for all new components
- Maintain protocol-based abstractions for testability
- Follow existing patterns in the codebase rather than introducing new ones
