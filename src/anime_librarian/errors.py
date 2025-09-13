"""
Custom error classes for the AnimeLibrarian application.

This module provides custom error classes used throughout the application.
"""

from typing import NoReturn


class AIParseError(ValueError):
    """Error raised when parsing the AI response fails."""

    def __init__(self, details: str | None = None) -> None:
        message = "Failed to parse AI response"
        if details is not None:
            message = f"{message}: {details}"
        super().__init__(message)


class FilePairsNotFoundError(RuntimeError):
    """Error raised when file pairs are expected but not found."""

    def __init__(self):
        message = "File pairs result is None when it was expected to be not None"
        super().__init__(message)


def raise_parse_error(error: Exception) -> NoReturn:
    """Raise an AIParseError with the given error as the cause."""
    # Using a separate function to abstract the raise statement
    # This satisfies TRY301 (raise-within-try)
    raise AIParseError(str(error)) from error
