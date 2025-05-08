"""Tests for the main module using dependency injection instead of patching."""

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
        self,
        source=None,
        target=None,
        dry_run=False,
        yes=False,
        verbose=False,
        version=False,
    ):
        """Initialize with predefined arguments."""
        self.source = source
        self.target = target
        self.dry_run = dry_run
        self.yes = yes
        self.verbose = verbose
        self.version = version

    def parse_args(self) -> CommandLineArgs:
        """Return CommandLineArgs with the predefined arguments."""
        return CommandLineArgs(
            source=self.source,
            target=self.target,
            dry_run=self.dry_run,
            yes=self.yes,
            verbose=self.verbose,
            version=self.version,
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


@pytest.fixture
def mock_file_renamer():
    """Create a mock FileRenamer instance."""
    mock = MagicMock(spec=FileRenamer)
    return mock


@pytest.fixture
def mock_file_renamer_factory(mock_file_renamer):
    """Create a mock factory function for FileRenamer."""
    factory = MagicMock(return_value=mock_file_renamer)

    def side_effect(source_path, target_path, http_client=None):
        mock_file_renamer.source_path = source_path
        mock_file_renamer.target_path = target_path
        mock_file_renamer.http_client = http_client
        return mock_file_renamer

    factory.side_effect = side_effect
    return factory


@pytest.fixture
def mock_output_writer():
    """Create a mock OutputWriter instance."""
    return MagicMock(spec=ConsoleOutputWriter)


@pytest.fixture
def mock_output_writer_factory(mock_output_writer):
    """Create a mock factory function for OutputWriter."""
    factory = MagicMock(return_value=mock_output_writer)

    def side_effect(verbose):
        mock_output_writer.verbose = verbose
        return mock_output_writer

    factory.side_effect = side_effect
    return factory


@pytest.fixture
def mock_set_verbose_mode():
    """Create a mock function for set_verbose_mode."""
    return MagicMock()


@pytest.fixture
def mock_app_dependencies(
    mock_file_renamer_factory, mock_output_writer_factory, mock_set_verbose_mode
):
    """Create all the dependencies needed for the AnimeLibrarian app."""
    source_path = Path("/mock/source")
    target_path = Path("/mock/target")

    arg_parser = MockArgumentParser()
    input_reader = MockInputReader()
    config_provider = MockConfigProvider(source_path, target_path)

    return {
        "arg_parser": arg_parser,
        "input_reader": input_reader,
        "config_provider": config_provider,
        "file_renamer_factory": mock_file_renamer_factory,
        "output_writer_factory": mock_output_writer_factory,
        "set_verbose_mode_fn": mock_set_verbose_mode,
        "source_path": source_path,
        "target_path": target_path,
    }


def test_main_basic_functionality(
    monkeypatch, mock_app_dependencies, mock_file_renamer
):
    """Test basic functionality of the main function using dependency injection."""
    # Setup dependencies
    source_path = mock_app_dependencies["source_path"]
    target_path = mock_app_dependencies["target_path"]

    # Configure the mock arg parser to simulate --yes flag
    mock_app_dependencies["arg_parser"] = MockArgumentParser(yes=True)

    # Configure the mock renamer to return some file pairs
    file_pairs = [
        (source_path / "file1.mp4", target_path / "Anime1" / "renamed_file1.mp4"),
        (source_path / "file2.mkv", target_path / "Anime2" / "renamed_file2.mkv"),
    ]
    mock_file_renamer.get_file_pairs.return_value = file_pairs

    # Configure the mock renamer to return empty lists for conflicts and missing dirs
    mock_file_renamer.check_for_conflicts.return_value = []
    mock_file_renamer.find_missing_directories.return_value = []

    # Configure the mock renamer to return empty list for errors (success)
    mock_file_renamer.rename_files.return_value = []

    # Create a custom main function that uses our mocks
    def custom_main():
        app = AnimeLibrarian(
            arg_parser=mock_app_dependencies["arg_parser"],
            input_reader=mock_app_dependencies["input_reader"],
            config_provider=mock_app_dependencies["config_provider"],
            file_renamer_factory=mock_app_dependencies["file_renamer_factory"],
            output_writer_factory=mock_app_dependencies["output_writer_factory"],
            set_verbose_mode_fn=mock_app_dependencies["set_verbose_mode_fn"],
        )
        return app.run()

    # Patch the main function
    monkeypatch.setattr("anime_librarian.main.main", custom_main)

    # Run the main function
    result = custom_main()

    # Verify the result
    assert result == 0

    # Verify the methods were called on the renamer
    mock_file_renamer.get_file_pairs.assert_called_once()
    mock_file_renamer.check_for_conflicts.assert_called_once_with(file_pairs)
    mock_file_renamer.find_missing_directories.assert_called_once_with(file_pairs)
    mock_file_renamer.rename_files.assert_called_once_with(file_pairs)

    # Verify success message was shown
    mock_app_dependencies[
        "output_writer_factory"
    ].return_value.message.assert_called_with("\nFile renaming completed successfully.")


def test_main_no_files_to_rename(monkeypatch, mock_app_dependencies, mock_file_renamer):
    """Test main function when there are no files to rename."""
    # Configure the mock renamer to return an empty list
    mock_file_renamer.get_file_pairs.return_value = []

    # Create a custom main function that uses our mocks
    def custom_main():
        app = AnimeLibrarian(
            arg_parser=mock_app_dependencies["arg_parser"],
            input_reader=mock_app_dependencies["input_reader"],
            config_provider=mock_app_dependencies["config_provider"],
            file_renamer_factory=mock_app_dependencies["file_renamer_factory"],
            output_writer_factory=mock_app_dependencies["output_writer_factory"],
            set_verbose_mode_fn=mock_app_dependencies["set_verbose_mode_fn"],
        )
        return app.run()

    # Patch the main function
    monkeypatch.setattr("anime_librarian.main.main", custom_main)

    # Run the main function
    result = custom_main()

    # Verify the result
    assert result == 0

    # Verify get_file_pairs was called
    mock_file_renamer.get_file_pairs.assert_called_once()

    # Verify no other methods were called
    mock_file_renamer.check_for_conflicts.assert_not_called()
    mock_file_renamer.find_missing_directories.assert_not_called()
    mock_file_renamer.rename_files.assert_not_called()


def test_main_dry_run(monkeypatch, mock_app_dependencies, mock_file_renamer):
    """Test main function with --dry-run flag."""
    # Setup dependencies
    source_path = mock_app_dependencies["source_path"]
    target_path = mock_app_dependencies["target_path"]

    # Configure the mock arg parser to simulate --dry-run flag
    mock_app_dependencies["arg_parser"] = MockArgumentParser(dry_run=True)

    # Configure the mock renamer to return some file pairs
    file_pairs = [
        (source_path / "file1.mp4", target_path / "Anime1" / "renamed_file1.mp4"),
    ]
    mock_file_renamer.get_file_pairs.return_value = file_pairs

    # Create a custom main function that uses our mocks
    def custom_main():
        app = AnimeLibrarian(
            arg_parser=mock_app_dependencies["arg_parser"],
            input_reader=mock_app_dependencies["input_reader"],
            config_provider=mock_app_dependencies["config_provider"],
            file_renamer_factory=mock_app_dependencies["file_renamer_factory"],
            output_writer_factory=mock_app_dependencies["output_writer_factory"],
            set_verbose_mode_fn=mock_app_dependencies["set_verbose_mode_fn"],
        )
        return app.run()

    # Patch the main function
    monkeypatch.setattr("anime_librarian.main.main", custom_main)

    # Run the main function
    result = custom_main()

    # Verify the result
    assert result == 0

    # Verify get_file_pairs was called
    mock_file_renamer.get_file_pairs.assert_called_once()

    # Verify no other methods were called since it's a dry run
    mock_file_renamer.check_for_conflicts.assert_not_called()
    mock_file_renamer.find_missing_directories.assert_not_called()
    mock_file_renamer.rename_files.assert_not_called()

    # Verify dry run message was shown
    mock_app_dependencies[
        "output_writer_factory"
    ].return_value.message.assert_called_with(
        "\nDry run completed. No files were renamed."
    )


def test_main_user_cancellation(monkeypatch, mock_app_dependencies, mock_file_renamer):
    """Test main function when user cancels the operation."""
    # Setup dependencies
    source_path = mock_app_dependencies["source_path"]
    target_path = mock_app_dependencies["target_path"]

    # Configure the mock input reader to return 'n' to cancel
    mock_app_dependencies["input_reader"] = MockInputReader(responses=["n"])

    # Configure the mock renamer to return some file pairs
    file_pairs = [
        (source_path / "file1.mp4", target_path / "Anime1" / "renamed_file1.mp4"),
    ]
    mock_file_renamer.get_file_pairs.return_value = file_pairs

    # Create a custom main function that uses our mocks
    def custom_main():
        app = AnimeLibrarian(
            arg_parser=mock_app_dependencies["arg_parser"],
            input_reader=mock_app_dependencies["input_reader"],
            config_provider=mock_app_dependencies["config_provider"],
            file_renamer_factory=mock_app_dependencies["file_renamer_factory"],
            output_writer_factory=mock_app_dependencies["output_writer_factory"],
            set_verbose_mode_fn=mock_app_dependencies["set_verbose_mode_fn"],
        )
        return app.run()

    # Patch the main function
    monkeypatch.setattr("anime_librarian.main.main", custom_main)

    # Run the main function
    result = custom_main()

    # Verify the result
    assert result == 0

    # Verify get_file_pairs was called
    mock_file_renamer.get_file_pairs.assert_called_once()

    # Verify no other methods were called since user cancelled
    mock_file_renamer.check_for_conflicts.assert_not_called()
    mock_file_renamer.find_missing_directories.assert_not_called()
    mock_file_renamer.rename_files.assert_not_called()


def test_main_verbose_option(monkeypatch, mock_app_dependencies, mock_file_renamer):
    """Test the application with verbose flag."""
    # Configure the mock arg parser to simulate --verbose flag
    mock_app_dependencies["arg_parser"] = MockArgumentParser(verbose=True)

    # Configure the mock renamer to return an empty list
    mock_file_renamer.get_file_pairs.return_value = []

    # Create a custom main function that uses our mocks
    def custom_main():
        app = AnimeLibrarian(
            arg_parser=mock_app_dependencies["arg_parser"],
            input_reader=mock_app_dependencies["input_reader"],
            config_provider=mock_app_dependencies["config_provider"],
            file_renamer_factory=mock_app_dependencies["file_renamer_factory"],
            output_writer_factory=mock_app_dependencies["output_writer_factory"],
            set_verbose_mode_fn=mock_app_dependencies["set_verbose_mode_fn"],
        )
        return app.run()

    # Patch the main function
    monkeypatch.setattr("anime_librarian.main.main", custom_main)

    # Run the main function
    custom_main()

    # Verify set_verbose_mode was called with True
    mock_app_dependencies["set_verbose_mode_fn"].assert_called_once_with(True)

    # Verify output factory was called with verbose=True
    mock_app_dependencies["output_writer_factory"].assert_called_with(True)


def test_main_version_option(monkeypatch, mock_app_dependencies, mock_file_renamer):
    """Test the application with version flag."""
    # Configure the mock arg parser to simulate --version flag
    mock_app_dependencies["arg_parser"] = MockArgumentParser(version=True)

    # Create a custom main function that uses our mocks
    def custom_main():
        app = AnimeLibrarian(
            arg_parser=mock_app_dependencies["arg_parser"],
            input_reader=mock_app_dependencies["input_reader"],
            config_provider=mock_app_dependencies["config_provider"],
            file_renamer_factory=mock_app_dependencies["file_renamer_factory"],
            output_writer_factory=mock_app_dependencies["output_writer_factory"],
            set_verbose_mode_fn=mock_app_dependencies["set_verbose_mode_fn"],
        )
        return app.run()

    # Patch the main function
    monkeypatch.setattr("anime_librarian.main.main", custom_main)

    # Run the main function
    result = custom_main()

    # Verify the result
    assert result == 0

    # Verify version message was shown
    from anime_librarian import __version__

    mock_app_dependencies[
        "output_writer_factory"
    ].return_value.notice.assert_called_with(f"{__version__}")

    # Verify no file operations were performed
    mock_file_renamer.get_file_pairs.assert_not_called()
