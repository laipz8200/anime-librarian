"""Output writer implementation for the AnimeLibrarian application."""

from collections.abc import Sequence
from typing import Any

from .types import OutputWriter


class ConsoleOutputWriter(OutputWriter):
    """Default implementation of OutputWriter using print statements."""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize with verbosity setting.

        Args:
            verbose: If True, show verbose output
        """
        self.verbose = verbose

    def message(self, message: str) -> None:
        """
        Print informational or success message only in verbose mode.

        Args:
            message: The message to print
        """
        if self.verbose:
            print(message)

    def notice(self, message: str) -> None:
        """
        Always print error or warning message.

        Args:
            message: The message to print
        """
        print(message)

    def list_items(
        self, header: str, items: Sequence[Any], always_show: bool = False
    ) -> None:
        """
        Print a list of items with a header.

        Args:
            header: The header to display
            items: The items to list
            always_show: If True, show even in non-verbose mode
        """
        if not self.verbose and not always_show:
            return

        print(header)
        for item in items:
            print(f"  {item}")

    # Legacy methods for backward compatibility
    def info(self, message: str) -> None:
        """
        Legacy method: Use message() instead.

        Args:
            message: The message to print
        """
        self.message(message)

    def success(self, message: str) -> None:
        """
        Legacy method: Use message() instead.

        Args:
            message: The message to print
        """
        self.message(message)

    def error(self, message: str) -> None:
        """
        Legacy method: Use notice() instead.

        Args:
            message: The message to print
        """
        self.notice(message)

    def warning(self, message: str) -> None:
        """
        Legacy method: Use notice() instead.

        Args:
            message: The message to print
        """
        self.notice(message)
