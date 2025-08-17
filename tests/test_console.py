"""Tests for the console module."""

from unittest.mock import MagicMock, mock_open, patch

from anime_librarian.console import BeautifulConsole, set_verbose_mode


@patch("anime_librarian.console.Console")
def test_console_initialization(mock_console_class):
    """Test that the console is initialized correctly."""
    console = BeautifulConsole(verbose=False)

    # Verify Console was instantiated
    mock_console_class.assert_called_once()
    assert console.verbose is False
    assert console._log_file is not None


@patch("anime_librarian.console.Console")
def test_console_verbose_mode(mock_console_class):
    """Test that verbose mode affects debug output."""
    # Test with verbose=True
    console = BeautifulConsole(verbose=True)
    assert console.verbose is True

    # Test with verbose=False
    console = BeautifulConsole(verbose=False)
    assert console.verbose is False


@patch("anime_librarian.console.Console")
@patch("builtins.open", new_callable=mock_open)
def test_console_success_message(mock_file, mock_console_class):
    """Test success message output."""
    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    console = BeautifulConsole()
    console.success("Operation completed", "Success")

    # Verify console.print was called
    mock_console.print.assert_called()

    # Verify log file was written
    mock_file.assert_called()


@patch("anime_librarian.console.Console")
@patch("builtins.open", new_callable=mock_open)
def test_console_error_message(mock_file, mock_console_class):
    """Test error message output."""
    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    console = BeautifulConsole()
    console.error("Something went wrong", "Error")

    # Verify console.print was called
    mock_console.print.assert_called()

    # Verify log file was written
    mock_file.assert_called()


@patch("anime_librarian.console.Console")
def test_console_debug_respects_verbose(mock_console_class):
    """Test that debug messages respect verbose mode."""
    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    # Test with verbose=False
    console = BeautifulConsole(verbose=False)
    console.debug("Debug message")
    mock_console.print.assert_not_called()

    # Test with verbose=True
    console = BeautifulConsole(verbose=True)
    console.debug("Debug message")
    mock_console.print.assert_called()


@patch("anime_librarian.console.BeautifulConsole")
def test_set_verbose_mode(mock_console_class):
    """Test set_verbose_mode function."""
    # Test with verbose=True
    set_verbose_mode(True)
    mock_console_class.assert_called_with(verbose=True)

    # Test with verbose=False
    set_verbose_mode(False)
    mock_console_class.assert_called_with(verbose=False)


@patch("anime_librarian.console.Console")
def test_console_ask_confirmation(mock_console_class):
    """Test ask_confirmation method."""
    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    # Test with 'yes' response
    mock_console.input.return_value = "yes"
    console = BeautifulConsole()
    result = console.ask_confirmation("Continue?", default=False)
    assert result is True

    # Test with 'no' response
    mock_console.input.return_value = "n"
    result = console.ask_confirmation("Continue?", default=True)
    assert result is False

    # Test with empty response (use default)
    mock_console.input.return_value = ""
    result = console.ask_confirmation("Continue?", default=True)
    assert result is True


@patch("anime_librarian.console.Console")
def test_console_print_file_operation(mock_console_class):
    """Test print_file_operation method."""
    mock_console = MagicMock()
    mock_console.width = 100  # Mock terminal width
    mock_console_class.return_value = mock_console

    console = BeautifulConsole()
    console.print_file_operation("Rename", "old.txt", "new.txt", "success")

    # Verify console.print was called
    mock_console.print.assert_called()

    # Check that the appropriate status icon was used
    call_args = mock_console.print.call_args[0][0]
    assert "✅" in call_args  # Success icon
