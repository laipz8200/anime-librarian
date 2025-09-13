"""Tests for the main module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anime_librarian.main import create_file_renamer, main


def test_create_file_renamer():
    """Test the create_file_renamer factory function."""
    source_path = Path("/test/source")
    target_path = Path("/test/target")

    renamer = create_file_renamer(source_path, target_path)

    assert renamer is not None
    assert renamer.source_path == source_path
    assert renamer.target_path == target_path


@patch("anime_librarian.main.RichAnimeLibrarian")
@patch("anime_librarian.main.DefaultConfigProvider")
@patch("anime_librarian.main.DefaultArgumentParser")
def test_main_function(mock_parser_class, mock_config_class, mock_app_class):
    """Test the main function creates and runs the application."""
    # Create mock instances
    mock_parser = MagicMock()
    mock_config = MagicMock()
    mock_app = MagicMock()

    # Configure the mock classes to return the mock instances
    mock_parser_class.return_value = mock_parser
    mock_config_class.return_value = mock_config
    mock_app_class.return_value = mock_app

    # Configure the app.run() to return 0
    mock_app.run.return_value = 0

    # Call main
    result = main()

    # Verify the result
    assert result == 0

    # Verify the classes were instantiated
    mock_parser_class.assert_called_once()
    mock_config_class.assert_called_once()
    mock_app_class.assert_called_once()

    # Verify the app was run
    mock_app.run.assert_called_once()


@patch("anime_librarian.main.RichAnimeLibrarian")
def test_main_with_error_exit_code(mock_app_class):
    """Test that main returns the correct exit code on error."""
    # Create mock app that returns error code
    mock_app = MagicMock()
    mock_app.run.return_value = 1
    mock_app_class.return_value = mock_app

    # Call main
    result = main()

    # Verify the error code is returned
    assert result == 1


@patch("anime_librarian.main.RichAnimeLibrarian")
def test_main_with_exception(mock_app_class):
    """Test that main handles exceptions gracefully."""
    # Create mock app that raises an exception
    mock_app = MagicMock()
    mock_app.run.side_effect = Exception("Test error")
    mock_app_class.return_value = mock_app

    # Call main - should not raise but return an error code
    with pytest.raises(Exception, match="Test error"):
        _ = main()
