"""Tests for the main module."""

import io
import sys

import pytest

from anime_librarian.output_writer import ConsoleOutputWriter


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
