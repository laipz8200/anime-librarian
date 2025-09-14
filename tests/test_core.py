"""Tests for the AnimeLibrarian class."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from anime_librarian.file_renamer import FileRenamer
from anime_librarian.rich_core import RichAnimeLibrarian as AnimeLibrarian
from anime_librarian.types import CommandLineArgs


class MockArgumentParser:
    """Mock implementation of ArgumentParser for testing."""

    def __init__(
        self,
        source=None,
        target=None,
        dry_run=False,
        yes=False,
        version=False,
    ):
        """Initialize with predefined arguments."""
        self.source = source
        self.target = target
        self.dry_run = dry_run
        self.yes = yes
        self.version = version

    def parse_args(self) -> CommandLineArgs:
        """Return CommandLineArgs with the predefined arguments."""
        return CommandLineArgs(
            source=self.source,
            target=self.target,
            dry_run=self.dry_run,
            yes=self.yes,
            version=self.version,
        )


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


# Removed mock_set_verbose_mode fixture (verbose feature removed)


def test_anime_librarian_basic_functionality(mock_file_renamer_factory):
    """Test basic functionality of the AnimeLibrarian."""
    # Setup
    mock_factory, mock_renamer = mock_file_renamer_factory

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
    # Mock rename_files to return no errors
    mock_renamer.rename_files.return_value = []
    # Add source_path and target_path attributes
    mock_renamer.source_path = source_path
    mock_renamer.target_path = target_path

    # Create the application
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(yes=True),
        config_provider=MockConfigProvider(
            source_path=source_path, target_path=target_path
        ),
        file_renamer_factory=mock_factory,
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0

    # Verify the factory was called with the correct arguments (including console)
    assert mock_factory.call_count == 1
    args = mock_factory.call_args[0]
    assert args[0] == source_path
    assert args[1] == target_path
    assert args[2] is None  # http_client
    # args[3] is the console instance

    # Verify the methods were called on the renamer
    mock_renamer.get_file_pairs.assert_called_once()
    mock_renamer.check_for_conflicts.assert_called_once_with(file_pairs)
    mock_renamer.find_missing_directories.assert_called_once_with(file_pairs)

    # Verify that rename_files was called for each file pair
    # Since we process files one by one, rename_files should be called twice
    assert mock_renamer.rename_files.call_count == 2


def test_anime_librarian_dry_run(mock_file_renamer_factory):
    """Test the application with dry run flag."""
    # Setup
    mock_factory, mock_renamer = mock_file_renamer_factory

    # Create mock file pairs
    source_path = Path("/mock/source")
    target_path = Path("/mock/target")
    file_pairs = [
        (source_path / "file1.mp4", target_path / "Anime1" / "renamed_file1.mp4"),
    ]
    mock_renamer.get_file_pairs.return_value = file_pairs
    # Add source_path and target_path attributes
    mock_renamer.source_path = source_path
    mock_renamer.target_path = target_path

    # Create the application with dry run flag
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(dry_run=True),
        config_provider=MockConfigProvider(),
        file_renamer_factory=mock_factory,
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


# Test for verbose mode removed (feature deleted)


def test_anime_librarian_version_flag(mock_file_renamer_factory):
    """Test the application with version flag."""
    # Setup
    mock_factory, mock_renamer = mock_file_renamer_factory

    # Create the application with version flag
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(version=True),
        config_provider=MockConfigProvider(),
        file_renamer_factory=mock_factory,
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0

    # Verify no file operations were performed
    mock_factory.assert_not_called()
    mock_renamer.get_file_pairs.assert_not_called()
    mock_renamer.check_for_conflicts.assert_not_called()
    mock_renamer.find_missing_directories.assert_not_called()


def test_anime_librarian_no_files():
    """Test the application when no files need to be renamed."""
    mock_renamer = MagicMock(spec=FileRenamer)
    mock_renamer.get_file_pairs.return_value = []
    # Add source_path and target_path attributes for the no-files check
    mock_renamer.source_path = Path("/mock/source")
    mock_renamer.target_path = Path("/mock/target")
    mock_factory = MagicMock(return_value=mock_renamer)

    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(yes=True),
        config_provider=MockConfigProvider(),
        file_renamer_factory=mock_factory,
    )

    # Run the application
    result = app.run()

    # Should exit with 0 when no files to rename
    assert result == 0

    # Verify get_file_pairs was called
    mock_renamer.get_file_pairs.assert_called_once()

    # Verify no rename operations were attempted
    mock_renamer.check_for_conflicts.assert_not_called()
    mock_renamer.find_missing_directories.assert_not_called()


def test_anime_librarian_with_conflicts_yes_mode(mock_file_renamer_factory):
    """Test handling of conflicts in yes mode (auto-confirm)."""
    # Setup
    mock_factory, mock_renamer = mock_file_renamer_factory

    # Create mock file pairs with conflicts
    source_path = Path("/mock/source")
    target_path = Path("/mock/target")
    file_pairs = [
        (source_path / "file1.mp4", target_path / "Anime1" / "renamed_file1.mp4"),
    ]
    mock_renamer.get_file_pairs.return_value = file_pairs
    mock_renamer.check_for_conflicts.return_value = [
        target_path / "Anime1" / "renamed_file1.mp4"
    ]
    mock_renamer.find_missing_directories.return_value = []
    # Mock rename_files to return no errors
    mock_renamer.rename_files.return_value = []
    # Add source_path and target_path attributes
    mock_renamer.source_path = source_path
    mock_renamer.target_path = target_path

    # Create the application with yes flag
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(yes=True),
        config_provider=MockConfigProvider(
            source_path=source_path, target_path=target_path
        ),
        file_renamer_factory=mock_factory,
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0

    # Verify that rename_files was called despite conflicts (yes mode)
    assert mock_renamer.rename_files.call_count == 1


def test_anime_librarian_with_missing_directories(mock_file_renamer_factory):
    """Test handling of missing directories."""
    # Setup
    mock_factory, mock_renamer = mock_file_renamer_factory

    # Create mock file pairs with missing directories
    source_path = Path("/mock/source")
    target_path = Path("/mock/target")
    file_pairs = [
        (source_path / "file1.mp4", target_path / "NewDir" / "file1.mp4"),
    ]
    missing_dirs = [target_path / "NewDir"]

    mock_renamer.get_file_pairs.return_value = file_pairs
    mock_renamer.check_for_conflicts.return_value = []
    mock_renamer.find_missing_directories.return_value = missing_dirs
    mock_renamer.create_directories.return_value = True
    # Mock rename_files to return no errors
    mock_renamer.rename_files.return_value = []
    # Add source_path and target_path attributes
    mock_renamer.source_path = source_path
    mock_renamer.target_path = target_path

    # Create the application with yes flag
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(yes=True),
        config_provider=MockConfigProvider(
            source_path=source_path, target_path=target_path
        ),
        file_renamer_factory=mock_factory,
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0

    # Verify create_directories was called
    mock_renamer.create_directories.assert_called()

    # Verify that rename_files was called
    assert mock_renamer.rename_files.call_count == 1
