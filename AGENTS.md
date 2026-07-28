# AGENTS.md

## Project overview

AnimeLibrarian is a Python 3.13 CLI that asks a Dify workflow to rename and
organize media files. Keep the implementation small, typed, and safe at the AI
and filesystem boundaries.

## Development workflow

Always use TDD:

1. **Red:** add the smallest failing test for the behavior.
1. **Green:** implement only enough code to pass.
1. **Refactor:** simplify while keeping the suite green.
1. Run `make lint`, `make type-check`, and `make test`.

Do not create new documentation files unless explicitly requested. Update
existing documentation when behavior or public interfaces change.

## Architecture

The runtime flow is deliberately linear:

1. `main.py` parses `CliOptions`, loads settings, constructs dependencies, and
   runs plan → review → move.
1. `config.py` resolves CLI overrides and environment values into immutable
   runtime `Settings`.
1. `dify.py` uses an injected `httpx.Client` to call Dify and validates its
   response.
1. `file_renamer.py` uses `FileOrganizer` to scan, validate `FileMove` values,
   preflight, and apply moves.
1. `console.py` exposes one Rich `Terminal` boundary. Plans use stdout; status,
   progress, warnings, errors, and confirmation use stderr.

`models.py` contains the small data shapes shared across these boundaries.
Expected user-facing failures belong in `errors.py`.

## Runtime behavior

- Scan only direct, regular files in the source directory; do not recurse or
  follow symlinks.
- Require existing source and target directories.
- Require at least one direct child directory in the target catalog before
  calling Dify.
- Validate all Dify suggestions: known source, relative destination inside the
  target root, unchanged extension, unique source and target, and no directory
  destination.
- Show one plan and ask once. Confirmation defaults to false when any target
  conflict exists.
- `--dry-run` must never prompt or mutate the filesystem.
- Keep table, plain, and JSON Lines plan output clean on stdout.

## Configuration

Required:

- `ANIMELIBRARIAN_DIFY_API_KEY`
- `ANIMELIBRARIAN_SOURCE_PATH` unless `--source` is supplied
- `ANIMELIBRARIAN_TARGET_PATH` unless `--target` is supplied

Optional:

- `ANIMELIBRARIAN_DIFY_WORKFLOW_RUN_ENDPOINT`
- `ANIMELIBRARIAN_API_TIMEOUT`
- `ANIMELIBRARIAN_USER_NAME`

## Supported formats

- Video: `.mkv`, `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`,
  `.mpg`, `.mpeg`
- Subtitle: `.srt`, `.ass`, `.ssa`, `.sub`, `.idx`, `.vtt`

## Code and tests

- Use complete type hints and avoid `Any`.
- Use Google-style docstrings for production code.
- Validate external data with Pydantic and raise domain errors from `errors.py`.
- Prefer composition and existing standard-library or installed-library
  features over new abstractions.
- Keep tests focused and deterministic. Use `httpx.MockTransport` for
  socket-free Dify request tests.
- Use the real Make targets shown by `make help`; there is no mock-server test
  target.
