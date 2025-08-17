"""Tests for the input reader module."""

from unittest.mock import patch

from anime_librarian.rich_output_writer import RichInputReader as ConsoleInputReader


def test_console_input_reader():
    """Test ConsoleInputReader.read_input method."""
    with patch("builtins.input", return_value="test input"):
        reader = ConsoleInputReader()
        result = reader.read_input("Enter input: ")
        assert result == "test input"


def test_console_input_reader_empty_input():
    """Test ConsoleInputReader.read_input method with empty input."""
    with patch("builtins.input", return_value=""):
        reader = ConsoleInputReader()
        result = reader.read_input("Enter input: ")
        assert result == ""
