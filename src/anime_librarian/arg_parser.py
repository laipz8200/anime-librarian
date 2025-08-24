"""Argument parser implementation for the AnimeLibrarian application."""

import argparse
from pathlib import Path

from . import config
from .types import ArgumentParser, CommandLineArgs


class DefaultArgumentParser(ArgumentParser):
    """Default implementation of ArgumentParser using argparse."""

    def parse_args(self) -> CommandLineArgs:
        """
        Parse command-line arguments.

        Returns:
            CommandLineArgs containing the parsed arguments
        """
        parser = argparse.ArgumentParser(
            description=(
                "Rename and organize video files using AI suggestions.\n"
                "\nUNIX-friendly flags: --quiet, --format, --no-color, -y."
            )
        )
        parser.add_argument(
            "--source",
            type=Path,
            help="Source directory containing files to rename "
            f"(default: {config.DEFAULT_SOURCE_PATH})",
        )
        parser.add_argument(
            "--target",
            type=Path,
            help="Target directory containing video folders "
            f"(default: {config.DEFAULT_TARGET_PATH})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually renaming files",
        )
        parser.add_argument(
            "--yes",
            "-y",
            action="store_true",
            help="Automatically answer yes to all prompts",
        )
        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            help="Quiet mode: minimize output and skip interactive prompts",
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose logging",
        )
        parser.add_argument(
            "--format",
            choices=["table", "plain", "json", "ndjson"],
            help=("Output format for listings: table (default), plain, json, ndjson"),
        )
        parser.add_argument(
            "--no-color",
            action="store_true",
            help="Disable colored/styled output (respects NO_COLOR env as well)",
        )
        parser.add_argument(
            "--version",
            action="store_true",
            help="Show version information and exit",
        )
        args = parser.parse_args()

        # Convert argparse.Namespace to CommandLineArgs
        return CommandLineArgs(
            source=args.source,
            target=args.target,
            dry_run=args.dry_run,
            yes=args.yes,
            quiet=args.quiet,
            verbose=args.verbose,
            output_format=args.format,
            no_color=args.no_color,
            version=args.version,
        )
