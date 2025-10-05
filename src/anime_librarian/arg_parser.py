"""Argument parser implementation for the AnimeLibrarian application."""

import argparse
from pathlib import Path
from typing import override

from . import config
from .types import ArgumentParser, CommandLineArgs


class DefaultArgumentParser(ArgumentParser):
    """Default implementation of ArgumentParser using argparse."""

    @override
    def parse_args(self) -> CommandLineArgs:
        """
        Parse command-line arguments.

        Returns:
            CommandLineArgs containing the parsed arguments
        """
        parser = argparse.ArgumentParser(
            description="Rename and organize video files using AI suggestions."
        )
        _ = parser.add_argument(
            "--source",
            type=Path,
            help=(
                "Source directory containing files to rename "
                f"(default: {config.DEFAULT_SOURCE_PATH})"
            ),
        )
        _ = parser.add_argument(
            "--target",
            type=Path,
            help=(
                "Target directory containing video folders "
                f"(default: {config.DEFAULT_TARGET_PATH})"
            ),
        )
        _ = parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually renaming files",
        )
        _ = parser.add_argument(
            "--format",
            choices=["table", "plain", "json"],
            help="Output format for listings: table (default), plain, json",
        )
        _ = parser.add_argument(
            "--version",
            action="store_true",
            help="Show version information and exit",
        )
        args = parser.parse_args()

        # Convert argparse.Namespace to CommandLineArgs
        return CommandLineArgs(
            source=args.source,  # type: ignore[attr-defined]
            target=args.target,  # type: ignore[attr-defined]
            dry_run=args.dry_run,  # type: ignore[attr-defined]
            version=args.version,  # type: ignore[attr-defined]
            output_format=args.format,  # type: ignore[attr-defined]
        )
