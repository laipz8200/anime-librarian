"""Tests for the logger module."""

import sys
from pathlib import Path
from unittest.mock import patch

from anime_librarian.logger import set_verbose_mode


@patch("anime_librarian.logger.logger")
def test_set_verbose_mode_true(mock_logger):
    """Test set_verbose_mode with verbose=True."""
    # Call the function with verbose=True
    set_verbose_mode(True)

    # Verify logger.remove was called
    mock_logger.remove.assert_called_once()

    # Verify logger.add was called twice (once for file, once for stdout)
    assert mock_logger.add.call_count == 2

    # Verify the first call was for file logging
    file_call_args = mock_logger.add.call_args_list[0][0]
    file_call_kwargs = mock_logger.add.call_args_list[0][1]
    assert isinstance(file_call_args[0], Path)
    assert file_call_kwargs["level"] == "DEBUG"

    # Verify the second call was for stdout
    stdout_call_args = mock_logger.add.call_args_list[1][0]
    stdout_call_kwargs = mock_logger.add.call_args_list[1][1]
    assert stdout_call_args[0] == sys.stdout
    assert stdout_call_kwargs["level"] == "DEBUG"

    # Verify debug message was logged
    mock_logger.debug.assert_called_once_with("Verbose logging enabled")


@patch("anime_librarian.logger.logger")
def test_set_verbose_mode_false(mock_logger):
    """Test set_verbose_mode with verbose=False."""
    # Call the function with verbose=False
    set_verbose_mode(False)

    # Verify logger.remove was not called
    mock_logger.remove.assert_not_called()

    # Verify logger.add was not called
    mock_logger.add.assert_not_called()

    # Verify debug message was not logged
    mock_logger.debug.assert_not_called()
