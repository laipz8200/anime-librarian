"""Tests for the new structured console logging methods."""

from unittest.mock import patch

import pytest

from anime_librarian.console import BeautifulConsole
from anime_librarian.enums import FileOperation, PreviewType, ProcessingStatus


@pytest.fixture
def console():
    """Create a BeautifulConsole instance for testing."""
    return BeautifulConsole()


@pytest.fixture
def mock_rich_console():
    """Create a mock Rich Console."""
    with patch("anime_librarian.console.Console") as mock:
        yield mock.return_value


def test_show_progress_scanning(console, mock_rich_console):
    """Test show_progress with SCANNING status."""
    console.console = mock_rich_console

    console.show_progress(ProcessingStatus.SCANNING, "Looking for video files")

    mock_rich_console.print.assert_called_once()
    call_args = mock_rich_console.print.call_args[0][0]
    assert "🔍" in call_args
    assert "Scanning" in call_args
    assert "Looking for video files" in call_args


def test_show_progress_completed(console, mock_rich_console):
    """Test show_progress with COMPLETED status."""
    console.console = mock_rich_console

    console.show_progress(ProcessingStatus.COMPLETED, "All files processed")

    mock_rich_console.print.assert_called_once()
    call_args = mock_rich_console.print.call_args[0][0]
    assert "✅" in call_args
    assert "Completed" in call_args
    assert "All files processed" in call_args


def test_show_progress_failed(console, mock_rich_console):
    """Test show_progress with FAILED status."""
    console.console = mock_rich_console

    console.show_progress(ProcessingStatus.FAILED, "Error processing file")

    mock_rich_console.print.assert_called_once()
    call_args = mock_rich_console.print.call_args[0][0]
    assert "❌" in call_args
    assert "Failed" in call_args
    assert "Error processing file" in call_args


def test_show_change_preview_rename(console, mock_rich_console):
    """Test show_change_preview for rename operations."""
    console.console = mock_rich_console

    console.show_change_preview(
        "old_file.mkv", "Episode_01.mkv", PreviewType.RENAME_PREVIEW
    )

    mock_rich_console.print.assert_called_once()
    # The method creates and prints a table


def test_show_change_preview_move(console, mock_rich_console):
    """Test show_change_preview for move operations."""
    console.console = mock_rich_console

    console.show_change_preview(
        "/source/file.mkv", "/target/anime/file.mkv", PreviewType.MOVE_PREVIEW
    )

    mock_rich_console.print.assert_called_once()


def test_show_change_preview_conflict(console, mock_rich_console):
    """Test show_change_preview for conflict display."""
    console.console = mock_rich_console

    console.show_change_preview(
        "existing_file.mkv", "new_file.mkv", PreviewType.CONFLICT_PREVIEW
    )

    mock_rich_console.print.assert_called_once()


def test_show_file_list_empty(console, mock_rich_console):
    """Test show_file_list with empty list."""
    console.console = mock_rich_console

    console.show_file_list("Video Files", [])

    mock_rich_console.print.assert_not_called()


def test_show_file_list_with_files(console, mock_rich_console):
    """Test show_file_list with multiple files."""
    console.console = mock_rich_console

    files = ["file1.mkv", "file2.mp4", "file3.avi"]
    console.show_file_list("Video Files", files)

    # Should print title + 3 files = 4 calls
    assert mock_rich_console.print.call_count == 4

    # Check title
    title_call = mock_rich_console.print.call_args_list[0][0][0]
    assert "Video Files" in title_call

    # Check each file
    for i, file in enumerate(files):
        file_call = mock_rich_console.print.call_args_list[i + 1][0][0]
        assert file in file_call
        assert "•" in file_call


def test_show_file_list_custom_style(console, mock_rich_console):
    """Test show_file_list with custom style."""
    console.console = mock_rich_console

    console.show_file_list("Errors", ["error1.txt"], style="red")

    assert mock_rich_console.print.call_count == 2
    title_call = mock_rich_console.print.call_args_list[0][0][0]
    assert "[bold red]" in title_call


def test_show_operation_result_rename_success(console, mock_rich_console):
    """Test show_operation_result for successful rename."""
    console.console = mock_rich_console

    console.show_operation_result(
        FileOperation.RENAME, "old_name.mkv", "new_name.mkv", success=True
    )

    mock_rich_console.print.assert_called_once()
    call_args = mock_rich_console.print.call_args[0][0]
    assert "✅" in call_args
    assert "Renamed" in call_args
    assert "old_name.mkv" in call_args
    assert "new_name.mkv" in call_args


def test_show_operation_result_move_failure(console, mock_rich_console):
    """Test show_operation_result for failed move."""
    console.console = mock_rich_console

    console.show_operation_result(
        FileOperation.MOVE,
        "source.mkv",
        "target.mkv",
        success=False,
        message="Permission denied",
    )

    mock_rich_console.print.assert_called_once()
    call_args = mock_rich_console.print.call_args[0][0]
    assert "❌" in call_args
    assert "Moved" in call_args
    assert "Permission denied" in call_args


def test_show_operation_result_delete(console, mock_rich_console):
    """Test show_operation_result for delete operation."""
    console.console = mock_rich_console

    console.show_operation_result(FileOperation.DELETE, "temp_file.tmp", success=True)

    mock_rich_console.print.assert_called_once()
    call_args = mock_rich_console.print.call_args[0][0]
    assert "✅" in call_args
    assert "Deleted" in call_args
    assert "temp_file.tmp" in call_args


def test_show_operation_result_create_dir(console, mock_rich_console):
    """Test show_operation_result for directory creation."""
    console.console = mock_rich_console

    console.show_operation_result(
        FileOperation.CREATE_DIR, "/path/to/new/dir", success=True
    )

    mock_rich_console.print.assert_called_once()
    call_args = mock_rich_console.print.call_args[0][0]
    assert "✅" in call_args
    assert "Created" in call_args
    assert "/path/to/new/dir" in call_args


def test_show_statistics_empty(console, mock_rich_console):
    """Test show_statistics with empty stats."""
    console.console = mock_rich_console

    console.show_statistics({})

    mock_rich_console.print.assert_called_once()


def test_show_statistics_with_data(console, mock_rich_console):
    """Test show_statistics with various statistics."""
    console.console = mock_rich_console

    stats = {
        "Files Processed": 10,
        "Files Renamed": 8,
        "Files Skipped": 2,
        "Total Size": "1.5 GB",
        "Duration": "00:02:30",
    }

    console.show_statistics(stats)

    mock_rich_console.print.assert_called_once()


def test_logging_to_file(console, tmp_path, monkeypatch):
    """Test that methods write to log file."""
    # Override log directory
    log_file = tmp_path / "test.log"
    console._log_file = log_file

    console.show_progress(ProcessingStatus.SCANNING, "Test message")

    assert log_file.exists()
    content = log_file.read_text()
    assert "Scanning: Test message" in content


def test_all_processing_statuses_have_config(console, mock_rich_console):
    """Test that all ProcessingStatus values have proper configuration."""
    console.console = mock_rich_console

    for status in ProcessingStatus:
        console.show_progress(status, f"Testing {status.name}")
        mock_rich_console.print.assert_called()
        mock_rich_console.print.reset_mock()


def test_all_file_operations_have_config(console, mock_rich_console):
    """Test that all FileOperation values have proper configuration."""
    console.console = mock_rich_console

    for operation in FileOperation:
        console.show_operation_result(operation, "test_file", success=True)
        mock_rich_console.print.assert_called()
        mock_rich_console.print.reset_mock()
