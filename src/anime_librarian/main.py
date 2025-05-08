"""
Main module for the AnimeLibrarian application.

This module provides the command-line interface for the AnimeLibrarian application,
which uses AI to rename and organize video files. It uses dependency injection
to make the code more testable and maintainable.
"""

import sys
from pathlib import Path

from .arg_parser import DefaultArgumentParser
from .config_provider import DefaultConfigProvider
from .core import AnimeLibrarian
from .file_renamer import FileRenamer
from .input_reader import ConsoleInputReader
from .output_writer import ConsoleOutputWriter
from .types import HttpClient


def create_file_renamer(
    source_path: Path, target_path: Path, http_client: HttpClient | None = None
) -> FileRenamer:
    """
    Create a FileRenamer instance.

    Args:
        source_path: The source path
        target_path: The target path
        http_client: Optional HTTP client to use

    Returns:
        A FileRenamer instance
    """
    return FileRenamer(
        source_path=source_path, target_path=target_path, http_client=http_client
    )


def create_output_writer(verbose: bool) -> ConsoleOutputWriter:
    """
    Create an OutputWriter instance.

    Args:
        verbose: Whether to enable verbose output

    Returns:
        A ConsoleOutputWriter instance
    """
    return ConsoleOutputWriter(verbose=verbose)


def main() -> int:
    """
    Execute the main program flow for renaming and organizing video files.

    This function creates the application with all its dependencies and runs it.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    app = AnimeLibrarian(
        arg_parser=DefaultArgumentParser(),
        input_reader=ConsoleInputReader(),
        config_provider=DefaultConfigProvider(),
        file_renamer_factory=create_file_renamer,
        output_writer_factory=create_output_writer,
    )
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
