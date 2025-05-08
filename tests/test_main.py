"""Tests for the main module."""

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anime_librarian.file_renamer import FileRenamer
from anime_librarian.output_writer import ConsoleOutputWriter
from anime_librarian.types import HttpClient


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


def test_output_class_verbose_mode():
    """Test the ConsoleOutputWriter class with verbose mode enabled and disabled."""
    # Redirect stdout to capture print statements
    stdout_backup = sys.stdout
    sys.stdout = io.StringIO()

    try:
        # Test with verbose mode off
        output_non_verbose = ConsoleOutputWriter(verbose=False)

        # Message (info/success) should not be printed in non-verbose mode
        output_non_verbose.message("This is a message")

        # Legacy methods should behave the same
        output_non_verbose.info("This is an info message")
        output_non_verbose.success("This is a success message")

        # Notice (error/warning) messages should always be printed
        output_non_verbose.notice("This is a notice")

        # Legacy methods should behave the same
        output_non_verbose.error("This is an error message")
        output_non_verbose.warning("This is a warning message")

        # List items should not be printed in non-verbose mode unless always_show=True
        output_non_verbose.list_items("Items:", ["item1", "item2"], always_show=False)
        output_non_verbose.list_items(
            "Always show items:", ["item3", "item4"], always_show=True
        )

        # Get the output
        non_verbose_output = sys.stdout.getvalue()
        sys.stdout = io.StringIO()  # Reset for next test

        # Test with verbose mode on
        output_verbose = ConsoleOutputWriter(verbose=True)

        # All messages should be printed in verbose mode
        output_verbose.message("This is a message")
        output_verbose.notice("This is a notice")

        # Legacy methods should behave the same
        output_verbose.info("This is an info message")
        output_verbose.success("This is a success message")
        output_verbose.error("This is an error message")
        output_verbose.warning("This is a warning message")

        # List items should be printed in verbose mode regardless of always_show
        output_verbose.list_items("Items:", ["item1", "item2"], always_show=False)
        output_verbose.list_items(
            "Always show items:", ["item3", "item4"], always_show=True
        )

        # Get the output
        verbose_output = sys.stdout.getvalue()

        # Verify non-verbose output
        assert "This is a message" not in non_verbose_output
        assert "This is an info message" not in non_verbose_output
        assert "This is a success message" not in non_verbose_output
        assert "This is a notice" in non_verbose_output
        assert "This is an error message" in non_verbose_output
        assert "This is a warning message" in non_verbose_output
        assert "Items:" not in non_verbose_output
        assert "item1" not in non_verbose_output
        assert "item2" not in non_verbose_output
        assert "Always show items:" in non_verbose_output
        assert "item3" in non_verbose_output
        assert "item4" in non_verbose_output

        # Verify verbose output
        assert "This is a message" in verbose_output
        assert "This is an info message" in verbose_output
        assert "This is a success message" in verbose_output
        assert "This is a notice" in verbose_output
        assert "This is an error message" in verbose_output
        assert "This is a warning message" in verbose_output
        assert "Items:" in verbose_output
        assert "item1" in verbose_output
        assert "item2" in verbose_output
        assert "Always show items:" in verbose_output
        assert "item3" in verbose_output
        assert "item4" in verbose_output

    finally:
        # Restore stdout
        sys.stdout = stdout_backup


def test_main_verbose_option(
    mock_source_path,
    mock_target_path,
):
    """Test the application with verbose flag using the test_application module."""
    # This test is now covered by test_application_verbose_mode in test_application.py
    # We'll keep a simplified version here for backward compatibility
    from anime_librarian.core import AnimeLibrarian
    from anime_librarian.output_writer import ConsoleOutputWriter
    from anime_librarian.types import CommandLineArgs

    # Create mock components
    mock_arg_parser = MagicMock()
    mock_arg_parser.parse_args.return_value = CommandLineArgs(
        source=None,
        target=None,
        dry_run=False,
        yes=True,
        verbose=True,
    )

    mock_input_reader = MagicMock()
    mock_config_provider = MagicMock()
    mock_config_provider.get_source_path.return_value = mock_source_path
    mock_config_provider.get_target_path.return_value = mock_target_path

    mock_file_renamer = MagicMock()
    mock_file_renamer.get_file_pairs.return_value = []

    mock_file_renamer_factory = MagicMock(return_value=mock_file_renamer)
    mock_output_writer = MagicMock(spec=ConsoleOutputWriter)
    mock_output_writer_factory = MagicMock(return_value=mock_output_writer)
    mock_set_verbose_mode = MagicMock()

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_arg_parser,
        input_reader=mock_input_reader,
        config_provider=mock_config_provider,
        file_renamer_factory=mock_file_renamer_factory,
        output_writer_factory=mock_output_writer_factory,
        set_verbose_mode_fn=mock_set_verbose_mode,
    )

    # Run the application
    app.run()

    # Verify set_verbose_mode was called with True
    mock_set_verbose_mode.assert_called_once_with(True)

    # Verify output factory was called with verbose=True
    mock_output_writer_factory.assert_called_once_with(True)
