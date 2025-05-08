"""Tests for error handling in the core module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from anime_librarian.core import AnimeLibrarian
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
        verbose=False,
    )

    mock_input_reader = MagicMock()
    mock_config_provider = MagicMock()
    mock_config_provider.get_source_path.return_value = source_path
    mock_config_provider.get_target_path.return_value = target_path

    mock_file_renamer = MagicMock()
    mock_file_renamer_factory = MagicMock(return_value=mock_file_renamer)

    mock_output_writer = MagicMock()
    mock_output_writer_factory = MagicMock(return_value=mock_output_writer)

    mock_set_verbose_mode = MagicMock()

    return {
        "arg_parser": mock_arg_parser,
        "input_reader": mock_input_reader,
        "config_provider": mock_config_provider,
        "file_renamer": mock_file_renamer,
        "file_renamer_factory": mock_file_renamer_factory,
        "output_writer": mock_output_writer,
        "output_writer_factory": mock_output_writer_factory,
        "set_verbose_mode_fn": mock_set_verbose_mode,
        "source_path": source_path,
        "target_path": target_path,
    }


def test_get_file_pairs_exception(mock_dependencies):
    """Test handling of exceptions when getting file pairs."""
    # Configure the mock renamer to raise an exception
    mock_dependencies["file_renamer"].get_file_pairs.side_effect = Exception(
        "API error"
    )

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        input_reader=mock_dependencies["input_reader"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
        output_writer_factory=mock_dependencies["output_writer_factory"],
        set_verbose_mode_fn=mock_dependencies["set_verbose_mode_fn"],
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 1

    # Verify error was reported
    mock_dependencies["output_writer"].notice.assert_called_with("Error: API error")


def test_conflicts_with_user_cancellation(mock_dependencies):
    """Test handling of conflicts with user cancellation."""
    # Configure the mock arg parser to return args with yes=False
    mock_dependencies["arg_parser"].parse_args.return_value = CommandLineArgs(
        source=None,
        target=None,
        dry_run=False,
        yes=False,
        verbose=False,
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

    # Configure the input reader to first return 'y' for initial confirmation
    # and then 'n' for conflict confirmation
    mock_dependencies["input_reader"].read_input.side_effect = ["y", "n"]

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        input_reader=mock_dependencies["input_reader"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
        output_writer_factory=mock_dependencies["output_writer_factory"],
        set_verbose_mode_fn=mock_dependencies["set_verbose_mode_fn"],
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0

    # Verify the input reader was called with the conflict prompt
    mock_dependencies["input_reader"].read_input.assert_any_call(
        "\nDo you want to continue? (y/n): "
    )

    # Verify cancellation message was shown
    mock_dependencies["output_writer"].message.assert_called_with(
        "Operation cancelled by user."
    )


def test_missing_directories_with_user_cancellation(mock_dependencies):
    """Test handling of missing directories with user cancellation."""
    # Configure the mock arg parser to return args with yes=False
    mock_dependencies["arg_parser"].parse_args.return_value = CommandLineArgs(
        source=None,
        target=None,
        dry_run=False,
        yes=False,
        verbose=False,
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

    # Configure the input reader to first return 'y' for initial confirmation
    # and then 'n' for directory creation confirmation
    mock_dependencies["input_reader"].read_input.side_effect = ["y", "n"]

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        input_reader=mock_dependencies["input_reader"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
        output_writer_factory=mock_dependencies["output_writer_factory"],
        set_verbose_mode_fn=mock_dependencies["set_verbose_mode_fn"],
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0

    # Verify the input reader was called with the directory creation prompt
    mock_dependencies["input_reader"].read_input.assert_any_call(
        "\nCreate these directories? (y/n): "
    )

    # Verify cancellation message was shown
    mock_dependencies["output_writer"].message.assert_called_with(
        "Operation cancelled by user."
    )


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

    # Configure the input reader to return 'y' to proceed
    mock_dependencies["input_reader"].read_input.return_value = "y"

    # Configure the renamer to fail directory creation
    mock_dependencies["file_renamer"].create_directories.return_value = False

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        input_reader=mock_dependencies["input_reader"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
        output_writer_factory=mock_dependencies["output_writer_factory"],
        set_verbose_mode_fn=mock_dependencies["set_verbose_mode_fn"],
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 1

    # Verify error message was shown
    mock_dependencies["output_writer"].notice.assert_called_with(
        "Failed to create directories. Operation cancelled."
    )


def test_rename_files_with_errors(mock_dependencies):
    """Test handling of errors during file renaming."""
    # Configure the mock arg parser to return args with yes=True to skip confirmations
    mock_dependencies["arg_parser"].parse_args.return_value = CommandLineArgs(
        source=None,
        target=None,
        dry_run=False,
        yes=True,
        verbose=False,
    )

    # Configure the mock renamer to return file pairs
    file_pairs = [
        (
            mock_dependencies["source_path"] / "file1.mp4",
            mock_dependencies["target_path"] / "Anime1" / "renamed_file1.mp4",
        ),
    ]
    mock_dependencies["file_renamer"].get_file_pairs.return_value = file_pairs
    mock_dependencies["file_renamer"].check_for_conflicts.return_value = []
    mock_dependencies["file_renamer"].find_missing_directories.return_value = []

    # Configure the renamer to return errors during file renaming
    errors = [
        (
            mock_dependencies["source_path"] / "file1.mp4",
            mock_dependencies["target_path"] / "Anime1" / "renamed_file1.mp4",
            "Permission denied",
        )
    ]
    mock_dependencies["file_renamer"].rename_files.return_value = errors

    # Create the application
    app = AnimeLibrarian(
        arg_parser=mock_dependencies["arg_parser"],
        input_reader=mock_dependencies["input_reader"],
        config_provider=mock_dependencies["config_provider"],
        file_renamer_factory=mock_dependencies["file_renamer_factory"],
        output_writer_factory=mock_dependencies["output_writer_factory"],
        set_verbose_mode_fn=mock_dependencies["set_verbose_mode_fn"],
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 1

    # Verify error messages were shown
    mock_dependencies["output_writer"].notice.assert_any_call(
        "\nThe following errors occurred during file renaming:"
    )

    # Verify the specific error message was shown
    error_message_call = False
    for call in mock_dependencies["output_writer"].notice.call_args_list:
        args, _ = call
        if args[0].startswith("  Error moving") and "Permission denied" in args[0]:
            error_message_call = True
            break
    assert error_message_call, "Error message for specific file not found in calls"

    # Verify the summary message was shown
    mock_dependencies["output_writer"].notice.assert_any_call(
        "\nCompleted with 1 errors."
    )
