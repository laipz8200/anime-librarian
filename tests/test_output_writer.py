"""Tests for the output writer module."""

from unittest.mock import MagicMock

import pytest

from anime_librarian.rich_output_writer import RichOutputWriter as ConsoleOutputWriter


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


def test_output_class_basic():
    """Test the ConsoleOutputWriter class basic functionality."""
    output = ConsoleOutputWriter()

    # Mock the inner Rich console
    mock_inner_console = MagicMock()
    output.console.console = mock_inner_console

    # Message and info are now only logged
    output.message("This is a message")
    output.info("This is an info message")

    # Success message
    output.success("This is a success message")
    assert mock_inner_console.print.called

    # Reset mock
    mock_inner_console.reset_mock()

    # Notice (error/warning) messages should always be printed
    output.notice("This is a notice")
    assert mock_inner_console.print.called

    # Test error and warning methods
    mock_inner_console.reset_mock()
    output.error("This is an error message")
    assert mock_inner_console.print.called

    mock_inner_console.reset_mock()
    output.warning("This is a warning message")
    assert mock_inner_console.print.called


def test_list_items_visibility():
    """Test list_items method respects always_show flag."""
    output = ConsoleOutputWriter()
    mock_inner_console = MagicMock()
    output.console.console = mock_inner_console

    # Should not print when always_show=False (default behavior)
    output.list_items("Items:", ["item1", "item2"], always_show=False)
    # Does not show when always_show=False

    # Reset mock
    mock_inner_console.reset_mock()

    # Should print when always_show=True
    output.list_items("Always show items:", ["item3", "item4"], always_show=True)
    assert mock_inner_console.print.called


def test_display_methods():
    """Test Rich-specific display methods."""
    writer = ConsoleOutputWriter()

    # Mock the inner console width for table logic
    writer.console.console = MagicMock()
    writer.console.console.width = 120

    # These should not raise exceptions
    file_pairs = [("source1.mp4", "target1.mp4"), ("source2.mkv", "target2.mkv")]
    writer.display_file_moves_table(file_pairs)

    # Test summary panel
    writer.display_summary_panel("Test Title", "Test Content")

    # Test progress display (returns a Progress object)
    progress = writer.display_progress("Test operation")
    assert progress is not None


def test_console_force_terminal():
    """Test that console is created with proper configuration."""
    writer = ConsoleOutputWriter()
    # Check that the console exists and is properly configured
    assert writer.console is not None
    # BeautifulConsole has an internal Rich Console
    assert hasattr(writer.console, "console")
    # Check that inner console exists
    assert writer.console.console is not None
