"""Tests for the FileRenamer class."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from file_renamer import FileRenamer
from http_client import HttpClient


@pytest.fixture
def mock_source_path(tmp_path):
    """Create a temporary source directory with mock files."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # Create some test files
    (source_dir / "file1.mp4").touch()
    (source_dir / "file2.mkv").touch()
    (source_dir / "file3.avi").touch()

    return source_dir


@pytest.fixture
def mock_target_path(tmp_path):
    """Create a temporary target directory with mock subdirectories."""
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    # Create some target directories
    (target_dir / "Anime1").mkdir()
    (target_dir / "Anime2").mkdir()

    return target_dir


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client that implements the HttpClient protocol."""
    client = MagicMock(spec=HttpClient)
    # Configure the mock to return a valid response
    client.post.return_value = {"data": {"outputs": {"text": '{"result": []}'}}}
    return client


@pytest.fixture
def file_renamer(mock_source_path, mock_target_path, mock_http_client):
    """Create a FileRenamer instance with mock paths and client."""
    return FileRenamer(
        source_path=mock_source_path,
        target_path=mock_target_path,
        http_client=mock_http_client,
    )


def test_get_name_pairs_from_ai(file_renamer, mock_http_client):
    """Test that _get_name_pairs_from_ai correctly processes the AI response."""
    # Configure the mock client to return a specific response
    mock_http_client.post.return_value = {
        "data": {
            "outputs": {
                "text": (
                    '{"result": ['
                    '{"original_name": "test.mp4", "new_name": "renamed.mp4"}'
                    "]}"
                )
            }
        }
    }

    # Call the method
    result = file_renamer._get_name_pairs_from_ai(
        source_files_list=["test.mp4"],
        target_files_list=["videos"],
    )

    # Verify the client was called with the correct arguments
    mock_http_client.post.assert_called_once()
    _, kwargs = mock_http_client.post.call_args
    assert kwargs["json"]["inputs"]["files"] == "test.mp4"
    assert kwargs["json"]["inputs"]["directories"] == "videos"

    # Verify the result
    assert len(result) == 1
    assert result[0] == ("test.mp4", "renamed.mp4")


def test_get_file_pairs_basic(file_renamer, mock_source_path, mock_target_path):
    """Test basic functionality of get_file_pairs."""
    # Mock the _get_name_pairs_from_ai method to return predefined pairs
    file_renamer._get_name_pairs_from_ai = MagicMock(
        return_value=[
            ("file1.mp4", "Anime1/renamed_file1.mp4"),
            ("file2.mkv", "Anime2/renamed_file2.mkv"),
            ("file3.avi", "renamed_file3.avi"),
        ]
    )

    # Call the method
    result = file_renamer.get_file_pairs()

    # Verify the mock was called with the correct arguments
    file_renamer._get_name_pairs_from_ai.assert_called_once()
    _, kwargs = file_renamer._get_name_pairs_from_ai.call_args
    assert set(kwargs["source_files_list"]) == {"file1.mp4", "file2.mkv", "file3.avi"}
    assert set(kwargs["target_files_list"]) == {"Anime1", "Anime2"}

    # Verify the result contains the expected path pairs
    assert len(result) == 3

    # Check each pair individually
    source_file1, target_file1 = result[0]
    assert source_file1 == mock_source_path / "file1.mp4"
    assert target_file1 == mock_target_path / "Anime1" / "renamed_file1.mp4"

    source_file2, target_file2 = result[1]
    assert source_file2 == mock_source_path / "file2.mkv"
    assert target_file2 == mock_target_path / "Anime2" / "renamed_file2.mkv"

    source_file3, target_file3 = result[2]
    assert source_file3 == mock_source_path / "file3.avi"
    assert target_file3 == mock_target_path / "renamed_file3.avi"


def test_check_for_conflicts(file_renamer, mock_source_path, mock_target_path):
    """Test the check_for_conflicts method."""
    # Create a file that will cause a conflict
    conflict_file = mock_target_path / "Anime1" / "existing.mp4"
    conflict_file.parent.mkdir(exist_ok=True)
    conflict_file.touch()

    # Create file pairs with one that conflicts
    file_pairs = [
        (mock_source_path / "file1.mp4", mock_target_path / "Anime1" / "new_file.mp4"),
        (mock_source_path / "file2.mkv", mock_target_path / "Anime1" / "existing.mp4"),
    ]

    # Check for conflicts
    conflicts = file_renamer.check_for_conflicts(file_pairs)

    # Verify the conflict was detected
    assert len(conflicts) == 1
    assert conflicts[0] == conflict_file


def test_find_missing_directories(file_renamer, mock_source_path, mock_target_path):
    """Test the find_missing_directories method."""
    # Create file pairs with directories that don't exist
    file_pairs = [
        (mock_source_path / "file1.mp4", mock_target_path / "Anime1" / "new_file.mp4"),
        (mock_source_path / "file2.mkv", mock_target_path / "NonExistent" / "file.mp4"),
        (
            mock_source_path / "file3.avi",
            mock_target_path / "Anime2" / "SubDir" / "file.avi",
        ),
    ]

    # Find missing directories
    missing_dirs = file_renamer.find_missing_directories(file_pairs)

    # Verify the missing directories were detected
    assert len(missing_dirs) == 2
    assert mock_target_path / "NonExistent" in missing_dirs
    assert mock_target_path / "Anime2" / "SubDir" in missing_dirs


def test_create_directories(file_renamer, mock_target_path):
    """Test the create_directories method."""
    # Define directories to create
    dirs_to_create = [
        mock_target_path / "NewDir1",
        mock_target_path / "NewDir2" / "SubDir",
    ]

    # Create the directories
    result = file_renamer.create_directories(dirs_to_create)

    # Verify the directories were created
    assert result is True
    assert (mock_target_path / "NewDir1").exists()
    assert (mock_target_path / "NewDir2" / "SubDir").exists()


@patch("file_renamer.shutil.move")
def test_rename_files(mock_move, file_renamer, mock_source_path, mock_target_path):
    """Test the rename_files method."""
    # Create file pairs
    file_pairs = [
        (mock_source_path / "file1.mp4", mock_target_path / "Anime1" / "new_file1.mp4"),
        (mock_source_path / "file2.mkv", mock_target_path / "Anime2" / "new_file2.mkv"),
    ]

    # Rename the files
    errors = file_renamer.rename_files(file_pairs)

    # Verify shutil.move was called for each pair
    assert mock_move.call_count == 2
    mock_move.assert_any_call(
        str(mock_source_path / "file1.mp4"),
        str(mock_target_path / "Anime1" / "new_file1.mp4"),
    )
    mock_move.assert_any_call(
        str(mock_source_path / "file2.mkv"),
        str(mock_target_path / "Anime2" / "new_file2.mkv"),
    )

    # Verify no errors were returned
    assert not errors


@patch("file_renamer.shutil.move")
def test_rename_files_with_error(
    mock_move, file_renamer, mock_source_path, mock_target_path
):
    """Test the rename_files method when an error occurs."""
    # Configure the mock to raise an exception for the second call
    mock_move.side_effect = [None, OSError("Permission denied")]

    # Create file pairs
    file_pairs = [
        (mock_source_path / "file1.mp4", mock_target_path / "Anime1" / "new_file1.mp4"),
        (mock_source_path / "file2.mkv", mock_target_path / "Anime2" / "new_file2.mkv"),
    ]

    # Rename the files
    errors = file_renamer.rename_files(file_pairs)

    # Verify shutil.move was called for each pair
    assert mock_move.call_count == 2

    # Verify the error was returned
    assert len(errors) == 1
    source, target, error_msg = errors[0]
    assert source == mock_source_path / "file2.mkv"
    assert target == mock_target_path / "Anime2" / "new_file2.mkv"
    assert "Permission denied" in error_msg
