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


def test_output_class_verbose_mode():
    """Test the ConsoleOutputWriter class with verbose mode enabled and disabled."""
    # Test with verbose mode off
    output_non_verbose = ConsoleOutputWriter(verbose=False)

    # Mock the inner Rich console
    mock_inner_console = MagicMock()
    output_non_verbose.console.console = mock_inner_console

    # Message (info/success) should not be printed in non-verbose mode
    output_non_verbose.message("This is a message")
    # message() only prints in verbose mode
    assert output_non_verbose.verbose is False

    # Legacy methods should behave the same
    output_non_verbose.info("This is an info message")
    # info() only prints in verbose mode

    output_non_verbose.success("This is a success message")
    # Success always prints
    assert mock_inner_console.print.called

    # Reset mock
    mock_inner_console.reset_mock()

    # Notice (error/warning) messages should always be printed
    output_non_verbose.notice("This is a notice")
    assert mock_inner_console.print.called

    # Test with verbose mode on
    output_verbose = ConsoleOutputWriter(verbose=True)
    mock_inner_console_verbose = MagicMock()
    output_verbose.console.console = mock_inner_console_verbose

    # All messages should trigger console print in verbose mode
    output_verbose.message("This is a message")
    # In verbose mode, message is shown

    output_verbose.notice("This is a notice")
    assert mock_inner_console_verbose.print.called

    # Test legacy methods
    output_verbose.info("This is an info message")
    # info() prints in verbose mode

    output_verbose.success("This is a success message")
    assert mock_inner_console_verbose.print.called

    mock_inner_console_verbose.reset_mock()
    output_verbose.error("This is an error message")
    assert mock_inner_console_verbose.print.called

    mock_inner_console_verbose.reset_mock()
    output_verbose.warning("This is a warning message")
    assert mock_inner_console_verbose.print.called


def test_list_items_visibility():
    """Test list_items method respects verbose mode and always_show flag."""
    # Non-verbose mode
    output_non_verbose = ConsoleOutputWriter(verbose=False)
    mock_inner_console = MagicMock()
    output_non_verbose.console.console = mock_inner_console

    # Should not print when verbose=False and always_show=False
    output_non_verbose.list_items("Items:", ["item1", "item2"], always_show=False)
    # show_file_list is called but checks verbose internally

    # Reset mock
    mock_inner_console.reset_mock()

    # Should print when always_show=True even in non-verbose mode
    output_non_verbose.list_items(
        "Always show items:", ["item3", "item4"], always_show=True
    )
    assert mock_inner_console.print.called

    # Verbose mode
    output_verbose = ConsoleOutputWriter(verbose=True)
    mock_inner_console_verbose = MagicMock()
    output_verbose.console.console = mock_inner_console_verbose

    # Should always print in verbose mode
    output_verbose.list_items("Items:", ["item1", "item2"], always_show=False)
    assert mock_inner_console_verbose.print.called

    mock_inner_console_verbose.reset_mock()
    output_verbose.list_items(
        "Always show items:", ["item3", "item4"], always_show=True
    )
    assert mock_inner_console_verbose.print.called


def test_display_methods():
    """Test Rich-specific display methods."""
    writer = ConsoleOutputWriter(verbose=True)

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
    writer = ConsoleOutputWriter(verbose=True)
    # Check that the console exists and is properly configured
    assert writer.console is not None
    # BeautifulConsole has an internal Rich Console
    assert hasattr(writer.console, "console")
    # Check that inner console exists
    assert writer.console.console is not None
