"""Type definitions and interfaces for the AnimeLibrarian application."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass
class CommandLineArgs:
    """Command line arguments for the AnimeLibrarian application."""

    source: Path | None
    """Source directory containing files to rename."""

    target: Path | None
    """Target directory containing video folders."""

    dry_run: bool
    """Whether to show what would be done without actually renaming files."""

    yes: bool
    """Whether to automatically answer yes to all prompts."""

    verbose: bool
    """Whether to enable verbose logging."""

    version: bool
    """Whether to show the version information and exit."""


@runtime_checkable
class HttpClient(Protocol):
    """Protocol for HTTP clients used in the application."""

    def post(
        self, url: str, *, headers: dict[str, str], json: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        """
        Send a POST request to the specified URL.

        Args:
            url: The URL to send the request to
            headers: HTTP headers to include in the request
            json: JSON payload to send in the request body
            timeout: Request timeout in seconds

        Returns:
            The parsed JSON response as a dictionary

        Raises:
            Exception: If the request fails
        """
        ...


@runtime_checkable
class ArgumentParser(Protocol):
    """Protocol for argument parsing."""

    def parse_args(self) -> CommandLineArgs:
        """
        Parse command-line arguments.

        Returns:
            CommandLineArgs containing the parsed arguments
        """
        ...


@runtime_checkable
class InputReader(Protocol):
    """Protocol for reading user input."""

    def read_input(self, prompt: str) -> str:
        """
        Read user input with the given prompt.

        Args:
            prompt: The prompt to display to the user

        Returns:
            The user's input as a string
        """
        ...


@runtime_checkable
class OutputWriter(Protocol):
    """Protocol for writing output."""

    def message(self, message: str) -> None:
        """Print informational or success message (only in verbose mode)."""
        ...

    def notice(self, message: str) -> None:
        """Print error or warning message (always shown)."""
        ...

    def list_items(
        self, header: str, items: Sequence[Any], always_show: bool = False
    ) -> None:
        """Print a list of items with a header."""
        ...


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for configuration providers."""

    def get_source_path(self) -> Path:
        """
        Get the source path.

        Returns:
            The source path
        """
        ...

    def get_target_path(self) -> Path:
        """
        Get the target path.

        Returns:
            The target path
        """
        ...
