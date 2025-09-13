"""Tests for error handling in the file renamer module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anime_librarian.errors import AIParseError
from anime_librarian.file_renamer import FileRenamer


def test_get_name_pairs_from_ai_error_handling():
    """Test error handling in _get_name_pairs_from_ai method."""
    # Setup
    source_path = Path("/test/source")
    target_path = Path("/test/target")

    # Create a mock HTTP client that raises an exception
    mock_http_client = MagicMock()
    mock_http_client.post.side_effect = Exception("API connection error")

    # Create the FileRenamer instance
    renamer = FileRenamer(
        source_path=source_path,
        target_path=target_path,
        http_client=mock_http_client,
        console=None,  # No console for tests
    )

    # Call the method and verify it raises an exception
    with pytest.raises(Exception, match="API connection error"):
        _ = renamer._get_name_pairs_from_ai(
            source_files_list=["file1.mp4", "file2.mkv"],
            target_files_list=["Anime1", "Anime2"],
        )


def test_get_name_pairs_from_ai_parse_error():
    """Test error handling for JSON parsing in _get_name_pairs_from_ai method."""
    # Setup
    source_path = Path("/test/source")
    target_path = Path("/test/target")

    # Create a mock HTTP client that returns invalid JSON
    mock_http_client = MagicMock()
    mock_http_client.post.return_value = {"data": {"outputs": {"text": "invalid json"}}}

    # Create the FileRenamer instance
    renamer = FileRenamer(
        source_path=source_path,
        target_path=target_path,
        http_client=mock_http_client,
        console=None,  # No console for tests
    )

    # Call the method and verify it raises an AIParseError
    with pytest.raises(AIParseError):
        _ = renamer._get_name_pairs_from_ai(
            source_files_list=["file1.mp4", "file2.mkv"],
            target_files_list=["Anime1", "Anime2"],
        )


def test_create_directories_error():
    """Test error handling in create_directories method."""
    # Setup
    source_path = Path("/test/source")
    target_path = Path("/test/target")

    # Create the FileRenamer instance
    renamer = FileRenamer(
        source_path=source_path,
        target_path=target_path,
        console=None,  # No console for tests
    )

    # Mock the Path.mkdir method to raise an exception
    with patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")):
        # Call the method and verify it returns False
        result = renamer.create_directories([Path("/test/target/Anime1")])
        assert result is False
