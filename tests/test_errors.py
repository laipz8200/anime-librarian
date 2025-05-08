"""Tests for the errors module."""

import pytest

from anime_librarian.errors import AIParseError, raise_parse_error


def test_ai_parse_error_without_details():
    """Test AIParseError initialization without details."""
    error = AIParseError()
    assert str(error) == "Failed to parse AI response"


def test_ai_parse_error_with_details():
    """Test AIParseError initialization with details."""
    error = AIParseError("Invalid JSON")
    assert str(error) == "Failed to parse AI response: Invalid JSON"


def test_raise_parse_error():
    """Test raise_parse_error function."""
    original_error = ValueError("Invalid JSON format")

    # Verify that the function raises AIParseError with the original error as cause
    with pytest.raises(AIParseError) as excinfo:
        raise_parse_error(original_error)

    # Check the error message
    assert str(excinfo.value) == "Failed to parse AI response: Invalid JSON format"

    # Check that the original error is the cause
    assert excinfo.value.__cause__ == original_error
