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
            description="Rename and organize video files using AI suggestions."
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
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose logging",
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
            verbose=args.verbose,
            version=args.version,
        )
