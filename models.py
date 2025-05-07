"""
Pydantic models for the AnimeLibrarian application.

This module provides Pydantic models used throughout the application.
"""

from pydantic import BaseModel


class NamePair(BaseModel):
    """Model for a name pair in the AI response."""

    original_name: str
    new_name: str


class AIResponse(BaseModel):
    """Model for the AI response."""

    result: list[NamePair]
