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


class ApiOutputs(BaseModel):
    """Model for the outputs field in the API response."""

    text: str


class ApiData(BaseModel):
    """Model for the data field in the API response."""

    outputs: ApiOutputs


class ApiResponse(BaseModel):
    """Model for the API response from the AI service."""

    data: ApiData

    @property
    def response_text(self) -> str:
        """Get the response text from the API response."""
        return self.data.outputs.text
