"""Tests for the AnimeLibrarian class."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from anime_librarian.core import AnimeLibrarian
from anime_librarian.file_renamer import FileRenamer
from anime_librarian.output_writer import ConsoleOutputWriter
from anime_librarian.types import CommandLineArgs


class MockArgumentParser:
    """Mock implementation of ArgumentParser for testing."""

    def __init__(
        self, source=None, target=None, dry_run=False, yes=False, verbose=False
    ):
        """Initialize with predefined arguments."""
        self.source = source
        self.target = target
        self.dry_run = dry_run
        self.yes = yes
        self.verbose = verbose

    def parse_args(self) -> CommandLineArgs:
        """Return CommandLineArgs with the predefined arguments."""
        return CommandLineArgs(
            source=self.source,
            target=self.target,
            dry_run=self.dry_run,
            yes=self.yes,
            verbose=self.verbose,
        )


class MockInputReader:
    """Mock implementation of InputReader for testing."""

    def __init__(self, responses=None):
        """Initialize with predefined responses."""
        self.responses = responses or []
        self.prompts = []

    def read_input(self, prompt):
        """Return the next response from the list."""
        self.prompts.append(prompt)
        if not self.responses:
            return "y"  # Default to yes if no responses are provided
        return self.responses.pop(0)


class MockConfigProvider:
    """Mock implementation of ConfigProvider for testing."""

    def __init__(self, source_path=None, target_path=None):
        """Initialize with predefined paths."""
        self.source_path = source_path or Path("/mock/source")
        self.target_path = target_path or Path("/mock/target")

    def get_source_path(self):
        """Return the predefined source path."""
        return self.source_path

    def get_target_path(self):
        """Return the predefined target path."""
        return self.target_path


class MockFileRenamer:
    """Mock implementation of FileRenamer for testing."""

    def __init__(self, file_pairs=None, conflicts=None, missing_dirs=None, errors=None):
        """Initialize with predefined responses."""
        self.file_pairs = file_pairs or []
        self.conflicts = conflicts or []
        self.missing_dirs = missing_dirs or []
        self.errors = errors or []
        self.source_path = Path("/mock/source")
        self.target_path = Path("/mock/target")

    def get_file_pairs(self):
        """Return the predefined file pairs."""
        return self.file_pairs

    def check_for_conflicts(self, _):
        """Return the predefined conflicts."""
        return self.conflicts

    def find_missing_directories(self, _):
        """Return the predefined missing directories."""
        return self.missing_dirs

    def create_directories(self, _):
        """Return True to indicate success."""
        return True

    def rename_files(self, _):
        """Return the predefined errors."""
        return self.errors


@pytest.fixture
def mock_file_renamer_factory():
    """Create a mock factory function for FileRenamer."""
    mock_renamer = MagicMock(spec=FileRenamer)
    mock_factory = MagicMock(return_value=mock_renamer)
    return mock_factory, mock_renamer


@pytest.fixture
def mock_output_writer_factory():
    """Create a mock factory function for OutputWriter."""
    mock_output = MagicMock(spec=ConsoleOutputWriter)
    mock_factory = MagicMock(return_value=mock_output)
    return mock_factory, mock_output


@pytest.fixture
def mock_set_verbose_mode():
    """Create a mock function for set_verbose_mode."""
    return MagicMock()


def test_anime_librarian_basic_functionality(
    mock_file_renamer_factory, mock_output_writer_factory, mock_set_verbose_mode
):
    """Test basic functionality of the AnimeLibrarian."""
    # Setup
    mock_factory, mock_renamer = mock_file_renamer_factory
    mock_output_factory, mock_output = mock_output_writer_factory

    # Create mock file pairs
    source_path = Path("/mock/source")
    target_path = Path("/mock/target")
    file_pairs = [
        (source_path / "file1.mp4", target_path / "Anime1" / "renamed_file1.mp4"),
        (source_path / "file2.mkv", target_path / "Anime2" / "renamed_file2.mkv"),
    ]
    mock_renamer.get_file_pairs.return_value = file_pairs
    mock_renamer.check_for_conflicts.return_value = []
    mock_renamer.find_missing_directories.return_value = []
    mock_renamer.rename_files.return_value = []

    # Create the application
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(yes=True),
        input_reader=MockInputReader(),
        config_provider=MockConfigProvider(
            source_path=source_path, target_path=target_path
        ),
        file_renamer_factory=mock_factory,
        output_writer_factory=mock_output_factory,
        set_verbose_mode_fn=mock_set_verbose_mode,
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0

    # Verify the factory was called with the correct arguments
    mock_factory.assert_called_once_with(source_path, target_path, None)

    # Verify the methods were called on the renamer
    mock_renamer.get_file_pairs.assert_called_once()
    mock_renamer.check_for_conflicts.assert_called_once_with(file_pairs)
    mock_renamer.find_missing_directories.assert_called_once_with(file_pairs)
    mock_renamer.rename_files.assert_called_once_with(file_pairs)

    # Verify success message was shown
    mock_output.message.assert_called_with("\nFile renaming completed successfully.")


def test_anime_librarian_dry_run(
    mock_file_renamer_factory, mock_output_writer_factory, mock_set_verbose_mode
):
    """Test the application with dry run flag."""
    # Setup
    mock_factory, mock_renamer = mock_file_renamer_factory
    mock_output_factory, mock_output = mock_output_writer_factory

    # Create mock file pairs
    source_path = Path("/mock/source")
    target_path = Path("/mock/target")
    file_pairs = [
        (source_path / "file1.mp4", target_path / "Anime1" / "renamed_file1.mp4"),
    ]
    mock_renamer.get_file_pairs.return_value = file_pairs

    # Create the application with dry run flag
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(dry_run=True),
        input_reader=MockInputReader(),
        config_provider=MockConfigProvider(),
        file_renamer_factory=mock_factory,
        output_writer_factory=mock_output_factory,
        set_verbose_mode_fn=mock_set_verbose_mode,
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0

    # Verify get_file_pairs was called
    mock_renamer.get_file_pairs.assert_called_once()

    # Verify no other methods were called since it's a dry run
    mock_renamer.check_for_conflicts.assert_not_called()
    mock_renamer.find_missing_directories.assert_not_called()
    mock_renamer.rename_files.assert_not_called()

    # Verify dry run message was shown
    mock_output.message.assert_called_with(
        "\nDry run completed. No files were renamed."
    )


def test_anime_librarian_verbose_mode(
    mock_file_renamer_factory, mock_output_writer_factory, mock_set_verbose_mode
):
    """Test the application with verbose flag."""
    # Setup
    mock_factory, mock_renamer = mock_file_renamer_factory
    mock_output_factory, _ = mock_output_writer_factory

    # Create mock file pairs
    mock_renamer.get_file_pairs.return_value = []

    # Create the application with verbose flag
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(verbose=True),
        input_reader=MockInputReader(),
        config_provider=MockConfigProvider(),
        file_renamer_factory=mock_factory,
        output_writer_factory=mock_output_factory,
        set_verbose_mode_fn=mock_set_verbose_mode,
    )

    # Run the application
    app.run()

    # Verify set_verbose_mode was called with True
    mock_set_verbose_mode.assert_called_once_with(True)

    # Verify output factory was called with verbose=True
    mock_output_factory.assert_called_once_with(True)
