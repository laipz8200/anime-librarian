"""Command-line entry point and application workflow."""

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast

import httpx

from . import __version__
from .config import load_settings
from .console import Terminal
from .dify import DifyClient
from .errors import AnimeLibrarianError, ConfigurationError
from .file_renamer import FileOrganizer


class OutputFormat(StrEnum):
    """Supported move-plan formats."""

    TABLE = "table"
    PLAIN = "plain"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class CliOptions:
    """Typed command-line options."""

    source: Path | None = None
    target: Path | None = None
    dry_run: bool = False
    output_format: OutputFormat = OutputFormat.TABLE


def build_parser() -> argparse.ArgumentParser:
    """Build the public CLI parser."""
    parser = argparse.ArgumentParser(
        description="Turn incoming media filenames into an organized library.",
        epilog=(
            "Example:\n"
            "  anime-librarian --source ~/Downloads --target ~/Media --dry-run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _ = parser.add_argument(
        "-s",
        "--source",
        type=_directory_path,
        metavar="DIR",
        help="directory containing incoming media (or ANIMELIBRARIAN_SOURCE_PATH)",
    )
    _ = parser.add_argument(
        "-t",
        "--target",
        type=_directory_path,
        metavar="DIR",
        help="library directory with existing show folders "
        "(or ANIMELIBRARIAN_TARGET_PATH)",
    )
    _ = parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="preview the move plan without changing files",
    )
    _ = parser.add_argument(
        "--format",
        dest="output_format",
        type=OutputFormat,
        choices=OutputFormat,
        default=OutputFormat.TABLE,
        help="plan output: table, minimal plain text, or script-safe JSON Lines",
    )
    _ = parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def run(
    options: CliOptions,
    organizer: FileOrganizer,
    terminal: Terminal,
) -> int:
    """Plan, review, and apply one organization run."""
    with terminal.status("Asking Dify to build a move plan"):
        moves = sorted(
            organizer.plan_moves(),
            key=lambda move: move.source.name.casefold(),
        )

    if not moves:
        terminal.info(
            "Nothing to organize. Add supported media files and at least one "
            "library folder."
        )
        return 0

    terminal.show_plan(moves, organizer.target_path, options.output_format)
    conflicts = organizer.conflicts(moves)
    missing_directories = organizer.missing_directories(moves)
    if conflicts:
        terminal.show_paths(
            f"{len(conflicts)} existing {_plural(len(conflicts), 'destination')}",
            conflicts,
            warning=True,
        )
    if missing_directories:
        terminal.show_paths(
            f"{len(missing_directories)} new "
            f"{_plural(len(missing_directories), 'directory')}",
            missing_directories,
            warning=False,
        )

    if options.dry_run:
        terminal.info("Dry run complete; no files were moved.")
        return 0

    question = f"Move {len(moves)} {_plural(len(moves), 'file')}?"
    if conflicts:
        question = (
            f"Overwrite {len(conflicts)} "
            f"{_plural(len(conflicts), 'destination')} and {question.lower()}"
        )
    if not terminal.confirm(question, default=not conflicts):
        terminal.info("Cancelled; no files were moved.")
        return 0

    organizer.create_directories(missing_directories)
    failures: list[tuple[Path, OSError]] = []
    approved_conflicts = set(conflicts)
    for move in terminal.track(moves):
        try:
            organizer.move(move, overwrite=move.target in approved_conflicts)
        except OSError as error:
            failures.append((move.source, error))

    if failures:
        terminal.error(
            f"Moved {len(moves) - len(failures)} files; {len(failures)} failed."
        )
        for source, error in failures:
            terminal.error(f"{source.name}: {error}")
        return 1

    terminal.success(f"Moved {len(moves)} {_plural(len(moves), 'file')}.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Parse settings, construct dependencies, and handle expected failures."""
    namespace = build_parser().parse_args(argv)
    options = CliOptions(
        source=cast("Path | None", namespace.source),
        target=cast("Path | None", namespace.target),
        dry_run=cast("bool", namespace.dry_run),
        output_format=cast("OutputFormat", namespace.output_format),
    )
    terminal = Terminal()

    try:
        settings = load_settings(options.source, options.target)
        with httpx.Client() as http:
            dify = DifyClient(settings, http)
            organizer = FileOrganizer(
                settings.source_path,
                settings.target_path,
                dify.suggest_names,
            )
            return run(options, organizer, terminal)
    except ConfigurationError as error:
        terminal.error(str(error))
        return 2
    except httpx.InvalidURL as error:
        terminal.error(f"Invalid HTTP configuration: {error}")
        return 2
    except AnimeLibrarianError as error:
        terminal.error(str(error))
        return 1
    except OSError as error:
        terminal.error(f"File operation failed: {error}")
        return 1
    except EOFError:
        terminal.error("Input closed; no files were moved.")
        return 1
    except KeyboardInterrupt:
        terminal.warning("Interrupted; no further files were moved.")
        return 130


def _plural(count: int, noun: str) -> str:
    return noun if count == 1 else f"{noun}s"


def _directory_path(value: str) -> Path:
    if not value.strip():
        message = "directory path cannot be empty"
        raise argparse.ArgumentTypeError(message)
    return Path(value)


if __name__ == "__main__":
    sys.exit(main())
