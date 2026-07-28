<div align="center">

# AnimeLibrarian

[![Code Quality](https://github.com/laipz8200/anime-librarian/actions/workflows/code-quality.yml/badge.svg)](https://github.com/laipz8200/anime-librarian/actions/workflows/code-quality.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

**Turn release filenames into library-ready paths with one reviewed move.**

</div>

AnimeLibrarian sends the filenames in an incoming folder and the existing folders
in a media library to a Dify workflow. It validates the returned move plan, shows
exactly what will change, and moves the files only after confirmation.

```text
Before                                      After
Downloads/                                  Media/
└── [SubsPlease] Frieren - 01.mkv    →      └── Frieren/
                                                └── Season 01/
                                                    └── Frieren - S01E01.mkv
```

## Why AnimeLibrarian?

- A polished Rich table for people, minimal plain text, and script-safe JSON
  Lines
- A true dry run that never prompts or changes the filesystem
- One confirmation for the whole plan, defaulting to **no** when files would be
  overwritten
- Strict validation of AI-proposed sources, destinations, extensions, and paths
- Clean pipelines: plans go to stdout; status, progress, warnings, and prompts go
  to stderr

## Quick start

Requires Python 3.13, [uv](https://docs.astral.sh/uv/), a published Dify workflow,
and a Dify API key.

```bash
git clone https://github.com/laipz8200/anime-librarian.git
cd anime-librarian
uv sync

cp .env.example .env
# Edit .env and set ANIMELIBRARIAN_DIFY_API_KEY.

mkdir -p ~/Downloads ~/Media/Frieren
uv run anime-librarian \
  --source ~/Downloads \
  --target ~/Media \
  --dry-run
```

The source and target must already be directories. The source scan is
non-recursive. The target must contain at least one direct child folder so Dify
has an existing library catalog to work from.

When the plan looks right, rerun without `--dry-run`.

## Set up the Dify workflow

1. In Dify Studio, import
   [`Dify DSL File/Anime Librarian.yml`](Dify%20DSL%20File/Anime%20Librarian.yml).
1. Configure the imported OpenAI model nodes.
1. Optionally set the workflow secret `TMDB_API_TOKEN` for richer TMDB metadata;
   the workflow falls back to model-only matching when it is absent.
1. Publish the workflow, open **API Access**, and create an API key.
1. Put that key in `.env`. Keep the default workflow endpoint unless your Dify
   deployment uses another URL.

The CLI supplies the workflow's `files` and `directories` inputs and expects its
published `text` output to contain `{"result": [...]}` filename pairs.

## Configuration

CLI paths override environment paths. `.env` is loaded automatically.

| Variable                                    | Required?                 | Default / purpose                      |
| ------------------------------------------- | ------------------------- | -------------------------------------- |
| `ANIMELIBRARIAN_DIFY_API_KEY`               | Yes                       | Dify workflow API key                  |
| `ANIMELIBRARIAN_SOURCE_PATH`                | Unless `--source` is used | Existing incoming directory            |
| `ANIMELIBRARIAN_TARGET_PATH`                | Unless `--target` is used | Existing media-library root            |
| `ANIMELIBRARIAN_DIFY_WORKFLOW_RUN_ENDPOINT` | No                        | `https://api.dify.ai/v1/workflows/run` |
| `ANIMELIBRARIAN_API_TIMEOUT`                | No                        | Positive timeout in seconds; `300`     |
| `ANIMELIBRARIAN_USER_NAME`                  | No                        | Dify request user; `Anime Librarian`   |

## CLI

| Option                   | What it does                                               |
| ------------------------ | ---------------------------------------------------------- |
| `-s DIR`, `--source DIR` | Use an incoming directory instead of the environment value |
| `-t DIR`, `--target DIR` | Use a library root instead of the environment value        |
| `-n`, `--dry-run`        | Print the plan without prompting or moving files           |
| `--format table`         | Render the default Rich move table                         |
| `--format plain`         | Print one `source -> target` line per move                 |
| `--format json`          | Print one JSON object per move (JSON Lines)                |
| `-V`, `--version`        | Print the installed version                                |
| `-h`, `--help`           | Show all options                                           |

For example, stream a machine-readable preview while keeping status messages
separate:

```bash
uv run anime-librarian --dry-run --format json > move-plan.jsonl
```

## Safety and supported files

AnimeLibrarian considers only direct, regular files in the source directory. It
ignores symlinks, other extensions, and nested directories.

- Video: `.mkv`, `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`,
  `.mpg`, `.mpeg`
- Subtitle: `.srt`, `.ass`, `.ssa`, `.sub`, `.idx`, `.vtt`

Every Dify suggestion must name a scanned source exactly, preserve its extension,
stay within the target root, and have a unique source and destination. Absolute
paths, traversal, duplicate moves, source-as-target moves, and directory
destinations are rejected. Source and destination identities are checked again
before each move, so late file swaps are refused.
Missing destination folders are listed before the prompt and created only after
approval.

A normal run asks once and defaults to yes. If any destination already exists,
the conflict list is shown and that same prompt defaults to no. A dry run never
asks.

## Architecture

The application is intentionally small and linear:

| Module            | Responsibility                                                               |
| ----------------- | ---------------------------------------------------------------------------- |
| `main.py`         | `argparse` interface, dependency setup, and plan → review → move workflow    |
| `config.py`       | Load and validate immutable runtime `Settings`                               |
| `dify.py`         | `httpx` adapter for the blocking Dify workflow API                           |
| `file_renamer.py` | `FileOrganizer` scanning, validated `FileMove` plans, and filesystem changes |
| `console.py`      | One Rich `Terminal` boundary for stdout, stderr, prompts, and progress       |
| `models.py`       | Validated Dify `NamePair` values and immutable `FileMove` values             |

## Development

```bash
make install      # Sync dependencies
make lint         # Format and autofix Python, then run Ruff
make check        # Run Ruff without fixes
make type-check   # Run strict basedpyright
make test         # Run the test suite
make clean        # Remove generated Python caches and coverage files
make help         # List every target
```

The focused suite exercises Dify with `httpx.MockTransport`, so tests do not
open network sockets.

Changes should follow red → green → refactor, then pass:

```bash
make lint
make type-check
make test
```

Contributions are welcome under the [MIT License](LICENSE).
