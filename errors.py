"""
Custom error classes for the AnimeLibrarian application.

This module provides custom error classes used throughout the application.
"""

from typing import NoReturn


class AIParseError(ValueError):
    """Error raised when parsing the AI response fails."""

    def __init__(self, details=None):
        message = "Failed to parse AI response"
        if details is not None:
            message = f"{message}: {details}"
        super().__init__(message)


def raise_parse_error(error) -> NoReturn:
    """Raise an AIParseError with the given error as the cause."""
    # Using a separate function to abstract the raise statement
    # This satisfies TRY301 (raise-within-try)
    raise AIParseError(str(error)) from error
