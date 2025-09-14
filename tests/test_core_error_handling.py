"""Tests for error handling in the core module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anime_librarian.rich_core import RichAnimeLibrarian as AnimeLibrarian
from anime_librarian.types import CommandLineArgs


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for the AnimeLibrarian class."""
    source_path = Path("/mock/source")
    target_path = Path("/mock/target")

    # Create mock components
    mock_arg_parser = MagicMock()
    mock_arg_parser.parse_args.return_value = CommandLineArgs(
        source=None,
        target=None,
        dry_run=False,
        yes=False,
        version=False,
    )

    mock_config_provider = MagicMock()
    mock_config_provider.get_source_path.return_value = source_path
    mock_config_provider.get_target_path.return_value = target_path

    mock_file_renamer = MagicMock()
    # Add source_path and target_path attributes for the renamer
    mock_file_renamer.source_path = source_path
    mock_file_renamer.target_path = target_path
    mock_file_renamer_factory = MagicMock(return_value=mock_file_renamer)

    return {
        "arg_parser": mock_arg_parser,
        "config_provider": mock_config_provider,
        "file_renamer": mock_file_renamer,
        "file_renamer_factory": mock_file_renamer_factory,
        "source_path": source_path,
        "target_path": target_path,
    }


def test_get_file_pairs_error_handling(mock_dependencies):
    """Test error handling when get_file_pairs fails."""
    # Configure the mock renamer to raise a specific exception
    mock_dependencies["file_renamer"].get_file_pairs.side_effect = ValueError(
        "API error"
    )

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 1


@patch("anime_librarian.rich_output_writer.Confirm.ask")
def test_conflicts_with_user_cancellation(mock_confirm, mock_dependencies):
    """Test handling of conflicts with user cancellation."""
    # Configure the mock arg parser to return args with yes=False
    mock_dependencies["arg_parser"].parse_args.return_value = CommandLineArgs(
        source=None,
        target=None,
        dry_run=False,
        yes=False,
        version=False,
    )

    # Configure the mock renamer to return file pairs and conflicts
    file_pairs = [
        (
            mock_dependencies["source_path"] / "file1.mp4",
            mock_dependencies["target_path"] / "Anime1" / "renamed_file1.mp4",
        ),
    ]
    mock_dependencies["file_renamer"].get_file_pairs.return_value = file_pairs
    mock_dependencies["file_renamer"].check_for_conflicts.return_value = [
        mock_dependencies["target_path"] / "Anime1" / "renamed_file1.mp4"
    ]

    # Configure the confirm dialog to return False for conflict confirmation
    # First yes for continue, then no for conflicts
    mock_confirm.side_effect = [True, False]

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
    )

    # Run the application
    result = app.run()

    # Verify the result - should exit gracefully
    assert result == 0


@patch("anime_librarian.rich_output_writer.Confirm.ask")
def test_missing_directories_with_user_cancellation(mock_confirm, mock_dependencies):
    """Test handling of missing directories with user cancellation."""
    # Configure the mock arg parser to return args with yes=False
    mock_dependencies["arg_parser"].parse_args.return_value = CommandLineArgs(
        source=None,
        target=None,
        dry_run=False,
        yes=False,
        version=False,
    )

    # Configure the mock renamer to return file pairs and missing directories
    file_pairs = [
        (
            mock_dependencies["source_path"] / "file1.mp4",
            mock_dependencies["target_path"] / "Anime1" / "renamed_file1.mp4",
        ),
    ]
    mock_dependencies["file_renamer"].get_file_pairs.return_value = file_pairs
    mock_dependencies["file_renamer"].check_for_conflicts.return_value = []
    mock_dependencies["file_renamer"].find_missing_directories.return_value = [
        mock_dependencies["target_path"] / "Anime1"
    ]

    # Configure confirm to return True for continue, then False for directory creation
    mock_confirm.side_effect = [True, False]

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
    )

    # Run the application
    result = app.run()

    # Verify the result - should exit gracefully
    assert result == 0


def test_directory_creation_failure(mock_dependencies):
    """Test handling of directory creation failure."""
    # Configure the mock renamer to return file pairs and missing directories
    file_pairs = [
        (
            mock_dependencies["source_path"] / "file1.mp4",
            mock_dependencies["target_path"] / "Anime1" / "renamed_file1.mp4",
        ),
    ]
    mock_dependencies["file_renamer"].get_file_pairs.return_value = file_pairs
    mock_dependencies["file_renamer"].check_for_conflicts.return_value = []
    mock_dependencies["file_renamer"].find_missing_directories.return_value = [
        mock_dependencies["target_path"] / "Anime1"
    ]
    # Configure create_directories to return False (failure)
    mock_dependencies["file_renamer"].create_directories.return_value = False

    # Configure the arg parser to auto-confirm (yes mode)
    mock_dependencies["arg_parser"].parse_args.return_value = CommandLineArgs(
        source=None,
        target=None,
        dry_run=False,
        yes=True,
        version=False,
    )

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
    )

    # Run the application
    result = app.run()

    # Verify the result - should return error
    assert result == 1


def test_file_rename_errors(mock_dependencies):
    """Test handling of errors during file renaming."""
    # Configure the mock renamer to return file pairs
    file_pairs = [
        (
            mock_dependencies["source_path"] / "file1.mp4",
            mock_dependencies["target_path"] / "Anime1" / "renamed_file1.mp4",
        ),
        (
            mock_dependencies["source_path"] / "file2.mp4",
            mock_dependencies["target_path"] / "Anime2" / "renamed_file2.mp4",
        ),
    ]
    mock_dependencies["file_renamer"].get_file_pairs.return_value = file_pairs
    mock_dependencies["file_renamer"].check_for_conflicts.return_value = []
    mock_dependencies["file_renamer"].find_missing_directories.return_value = []

    # Configure rename_files to return errors for the first file
    mock_dependencies["file_renamer"].rename_files.side_effect = [
        [(file_pairs[0][0], file_pairs[0][1], "Permission denied")],
        [],
    ]

    # Configure the arg parser to auto-confirm (yes mode)
    mock_dependencies["arg_parser"].parse_args.return_value = CommandLineArgs(
        source=None,
        target=None,
        dry_run=False,
        yes=True,
        version=False,
    )

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
    )

    # Run the application
    result = app.run()

    # Verify the result - should return error due to failed file move
    assert result == 1
