"""Tests for the main module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anime_librarian.file_renamer import FileRenamer
from anime_librarian.http_client import HttpClient


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
def mock_file_renamer(mock_source_path, mock_target_path, mock_http_client):
    """Create a mock FileRenamer instance."""
    renamer = MagicMock(spec=FileRenamer)
    renamer.source_path = mock_source_path
    renamer.target_path = mock_target_path
    renamer.http_client = mock_http_client
    return renamer


@pytest.fixture
def mock_config():
    """Mock the config module to avoid needing a .env file."""
    with (
        patch(
            "anime_librarian.config.get_source_path", return_value=Path("/tmp/source")
        ),
        patch(
            "anime_librarian.config.get_target_path", return_value=Path("/tmp/target")
        ),
    ):
        yield


@patch("anime_librarian.main.FileRenamer")
def test_main_basic_functionality(
    mock_file_renamer_class,
    mock_source_path,
    mock_target_path,
    mock_file_renamer,
    mock_config,
):
    """Test basic functionality of the main function."""
    # Configure the mock FileRenamer class to return our mock instance
    mock_file_renamer_class.return_value = mock_file_renamer

    # Configure the mock renamer to return some file pairs
    mock_file_renamer.get_file_pairs.return_value = [
        (
            mock_source_path / "file1.mp4",
            mock_target_path / "Anime1" / "renamed_file1.mp4",
        ),
        (
            mock_source_path / "file2.mkv",
            mock_target_path / "Anime2" / "renamed_file2.mkv",
        ),
    ]

    # Mock the input function to return 'y' for all prompts and sys.argv
    with (
        patch("builtins.input", return_value="y"),
        patch("sys.argv", ["main.py", "--yes"]),
    ):
        # Import and run the main function
        from anime_librarian.main import main

        main()

    # Verify the FileRenamer was created
    mock_file_renamer_class.assert_called_once()

    # Verify get_file_pairs was called
    mock_file_renamer.get_file_pairs.assert_called_once()

    # Verify check_for_conflicts was called with the file pairs
    mock_file_renamer.check_for_conflicts.assert_called_once()
    args, _ = mock_file_renamer.check_for_conflicts.call_args
    assert args[0] == mock_file_renamer.get_file_pairs.return_value

    # Verify find_missing_directories was called with the file pairs
    mock_file_renamer.find_missing_directories.assert_called_once()
    args, _ = mock_file_renamer.find_missing_directories.call_args
    assert args[0] == mock_file_renamer.get_file_pairs.return_value

    # Verify rename_files was called with the file pairs
    mock_file_renamer.rename_files.assert_called_once()
    args, _ = mock_file_renamer.rename_files.call_args
    assert args[0] == mock_file_renamer.get_file_pairs.return_value


@patch("anime_librarian.main.FileRenamer")
def test_main_no_files_to_rename(
    mock_file_renamer_class, mock_file_renamer, mock_config
):
    """Test main function when there are no files to rename."""
    # Configure the mock FileRenamer class to return our mock instance
    mock_file_renamer_class.return_value = mock_file_renamer

    # Configure the mock renamer to return an empty list
    mock_file_renamer.get_file_pairs.return_value = []

    # Mock sys.argv to simulate command-line arguments
    with patch("sys.argv", ["main.py"]):
        # Import and run the main function
        from anime_librarian.main import main

        main()

    # Verify the FileRenamer was created
    mock_file_renamer_class.assert_called_once()

    # Verify get_file_pairs was called
    mock_file_renamer.get_file_pairs.assert_called_once()

    # Verify no other methods were called
    mock_file_renamer.check_for_conflicts.assert_not_called()
    mock_file_renamer.find_missing_directories.assert_not_called()
    mock_file_renamer.rename_files.assert_not_called()


@patch("anime_librarian.main.FileRenamer")
def test_main_dry_run(
    mock_file_renamer_class,
    mock_source_path,
    mock_target_path,
    mock_file_renamer,
    mock_config,
):
    """Test main function with --dry-run flag."""
    # Configure the mock FileRenamer class to return our mock instance
    mock_file_renamer_class.return_value = mock_file_renamer

    # Configure the mock renamer to return some file pairs
    mock_file_renamer.get_file_pairs.return_value = [
        (
            mock_source_path / "file1.mp4",
            mock_target_path / "Anime1" / "renamed_file1.mp4",
        ),
    ]

    # Mock sys.argv to simulate command-line arguments
    with patch("sys.argv", ["main.py", "--dry-run"]):
        # Import and run the main function
        from anime_librarian.main import main

        main()

    # Verify the FileRenamer was created
    mock_file_renamer_class.assert_called_once()

    # Verify get_file_pairs was called
    mock_file_renamer.get_file_pairs.assert_called_once()

    # Verify no other methods were called since it's a dry run
    mock_file_renamer.check_for_conflicts.assert_not_called()
    mock_file_renamer.find_missing_directories.assert_not_called()
    mock_file_renamer.rename_files.assert_not_called()


@patch("anime_librarian.main.FileRenamer")
def test_main_user_cancellation(
    mock_file_renamer_class,
    mock_source_path,
    mock_target_path,
    mock_file_renamer,
    mock_config,
):
    """Test main function when user cancels the operation."""
    # Configure the mock FileRenamer class to return our mock instance
    mock_file_renamer_class.return_value = mock_file_renamer

    # Configure the mock renamer to return some file pairs
    mock_file_renamer.get_file_pairs.return_value = [
        (
            mock_source_path / "file1.mp4",
            mock_target_path / "Anime1" / "renamed_file1.mp4",
        ),
    ]

    # Mock the input function to return 'n' to cancel
    # Mock sys.argv to simulate command-line arguments
    with patch("builtins.input", return_value="n"), patch("sys.argv", ["main.py"]):
        # Import and run the main function
        from anime_librarian.main import main

        main()

    # Verify the FileRenamer was created
    mock_file_renamer_class.assert_called_once()

    # Verify get_file_pairs was called
    mock_file_renamer.get_file_pairs.assert_called_once()

    # Verify no other methods were called since user cancelled
    mock_file_renamer.check_for_conflicts.assert_not_called()
    mock_file_renamer.find_missing_directories.assert_not_called()
    mock_file_renamer.rename_files.assert_not_called()
