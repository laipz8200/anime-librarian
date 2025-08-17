"""Tests for the Rich-enhanced components."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from anime_librarian.rich_core import RichAnimeLibrarian
from anime_librarian.rich_output_writer import RichInputReader, RichOutputWriter
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
        self.args = CommandLineArgs(
            source=source,
            target=target,
            dry_run=dry_run,
            yes=yes,
            verbose=verbose,
            version=version,
        )

    def parse_args(self) -> CommandLineArgs:
        """Return CommandLineArgs with the predefined arguments."""
        return self.args


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


def test_rich_output_writer_initialization():
    """Test RichOutputWriter initialization."""
    writer = RichOutputWriter(verbose=True)
    assert writer.verbose is True
    assert writer.console is not None
    assert writer.console._force_terminal is True


def test_rich_output_writer_message_methods():
    """Test RichOutputWriter message methods."""
    writer = RichOutputWriter(verbose=True)

    # These should not raise exceptions
    writer.message("Test message")
    writer.notice("Test notice")
    writer.success("Test success")
    writer.error("Test error")
    writer.warning("Test warning")
    writer.info("Test info")


def test_rich_output_writer_display_methods():
    """Test RichOutputWriter display methods."""
    writer = RichOutputWriter(verbose=True)

    # Test file moves table
    file_pairs = [("source1.mp4", "target1.mp4"), ("source2.mkv", "target2.mkv")]
    writer.display_file_moves_table(file_pairs)

    # Test summary panel
    writer.display_summary_panel("Test Title", "Test Content")

    # Test list items
    writer.list_items("Test Header", ["item1", "item2"], always_show=True)


def test_rich_input_reader():
    """Test RichInputReader methods."""
    reader = RichInputReader()
    assert reader.console is not None
    assert reader.console._force_terminal is True

    # Test confirm method with mock
    with patch("rich.prompt.Confirm.ask", return_value=True):
        result = reader.confirm("Test prompt?")
        assert result is True

    # Test read_input method with mock
    with patch.object(reader.console, "input", return_value="test input"):
        result = reader.read_input("Test prompt: ")
        assert result == "test input"


def test_rich_anime_librarian_version():
    """Test RichAnimeLibrarian version display."""
    mock_renamer = MagicMock()
    mock_factory = MagicMock(return_value=mock_renamer)

    app = RichAnimeLibrarian(
        arg_parser=MockArgumentParser(version=True),
        config_provider=MockConfigProvider(),
        file_renamer_factory=mock_factory,
    )

    # Run the application
    result = app.run()

    # Version command should return 0
    assert result == 0

    # File renamer should not be called for version
    mock_factory.assert_not_called()


def test_rich_anime_librarian_dry_run():
    """Test RichAnimeLibrarian dry run mode."""
    mock_renamer = MagicMock()
    mock_renamer.get_file_pairs.return_value = [
        (Path("/source/file.mp4"), Path("/target/file.mp4"))
    ]
    mock_factory = MagicMock(return_value=mock_renamer)

    app = RichAnimeLibrarian(
        arg_parser=MockArgumentParser(dry_run=True, yes=True),
        config_provider=MockConfigProvider(),
        file_renamer_factory=mock_factory,
    )

    # Run the application
    result = app.run()

    # Dry run should return 0
    assert result == 0

    # File renamer should be created and get_file_pairs called
    mock_factory.assert_called_once()
    mock_renamer.get_file_pairs.assert_called_once()

    # But rename_files should not be called
    mock_renamer.rename_files.assert_not_called()
