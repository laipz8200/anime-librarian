# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Types of changes

- **Added** for new features.
- **Changed** for changes in existing functionality.
- **Deprecated** for soon-to-be removed features.
- **Removed** for now removed features.
- **Fixed** for any bug fixes.
- **Security** in case of vulnerabilities.

## [Unreleased]

## [0.4.0] - 2026-07-28

### Added

- Add Rich move-plan tables while retaining plain and JSON Lines output for
  scripts.
- Add strict validation for AI-proposed sources, destinations, extensions, and
  target-root containment.
- Add support for `.m4v`, `.mpg`, `.mpeg`, and `.idx` media files.

### Changed

- Replace the layered application stack with a linear CLI workflow, runtime
  `Settings`, an `httpx` Dify adapter, `FileOrganizer`, and one Rich `Terminal`.
- Send plans to stdout and all status, progress, warnings, errors, and
  confirmation to stderr.
- Use one move confirmation, defaulting to no when destination conflicts exist.
- Limit source discovery to direct files and require an existing target catalog
  with at least one direct child folder.
- Ignore source symlinks so moves cannot silently relocate or break links instead
  of their media payloads.
- Replace the live mock server with deterministic, socket-free
  `httpx.MockTransport` tests and consolidate duplicate CI workflows.

### Removed

- Remove legacy protocol, provider, output-writer, Rich-wrapper, and mock-server
  layers plus their FastAPI, Uvicorn, and pytest-asyncio dependencies.

### Fixed

- Align the bundled Dify prompts with the `result` field required by their
  structured-output schemas and the CLI.
- Refuse source, destination, or target-root replacements made after a move plan
  is reviewed.

## [0.3.1] - 2026-07-28

### Added

- Add installable CLI packaging and the `anime-librarian` console entry point.
- Add `--format {table,plain,json}` output for move plans.

### Changed

- Simplify the CLI output, confirmation prompts, and application architecture.
- Update the bundled Dify workflow and improve season matching and output
  aggregation.
- Improve error handling, dependency injection, type safety, and integration tests.

### Removed

- Remove the `--verbose`, `--quiet`, and `--yes` options.
- Remove log files and logging instrumentation.

### Fixed

- Prevent duplicate log output.
- Standardize the confirmation prompt to `[Y/n]`.

## [0.3.0] - 2025-05-27

### Changed

- Upgrade Dify DSL to version 0.3.0 to support fetch information from TMDB.

## [0.2.0] - 2025-05-17

### Added

- Sorts file pairs before displaying planned moves
- Media extension filtering to file renaming
- Custom error handling for missing file pairs
- DSL updates to handle OVA files and JSON output

### Changed

- Enhanced API response validation and logging

## [0.1.0] - 2025-05-08

### Added

- Initial release of AnimeLibrarian
- Pre-commit hooks for code quality checks
- Comprehensive test coverage for core modules
- Mock config fixture to test environment
- USER_NAME config for API requests
- CODEOWNERS, PR template, and CI workflow
- LICENSE file
