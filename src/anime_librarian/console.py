"""
Beautiful console output for the AnimeLibrarian application.

This module provides a Rich-based console interface with beautiful UI/UX.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Custom theme for better colors
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "success": "green",
        "debug": "dim white",
        "path": "bright_blue",
        "filename": "bright_cyan",
    }
)


class BeautifulConsole:
    """Beautiful console output handler using Rich library for excellent UI/UX."""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize the beautiful console.

        Args:
            verbose: If True, show debug messages
        """
        self.console = Console(theme=custom_theme)
        self.verbose = verbose
        self._log_file: Path | None = None
        self._setup_log_file()
        self._last_was_progress = False

    def _setup_log_file(self) -> None:
        """Setup log file for persistent logging."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_file = log_dir / f"AnimeLibrarian_{timestamp}.log"

    def _write_to_log(self, message: str, level: str = "INFO") -> None:
        """Write message to log file."""
        if self._log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")

    def _get_terminal_width(self) -> int:
        """Get the current terminal width."""
        return self.console.width

    def _truncate_path(
        self, path: str, max_length: int = 60, preserve_filename: bool = True
    ) -> str:
        """
        Intelligently truncate a file path for display.

        Args:
            path: The file path to truncate
            max_length: Maximum length of the displayed path
            preserve_filename: If True, always show the full filename

        Returns:
            Truncated path with ellipsis if needed
        """
        if len(path) <= max_length:
            return path

        path_obj = Path(path)
        filename = path_obj.name

        # If preserve_filename is True, never truncate the filename
        if preserve_filename:
            # Return just the filename if it's longer than max_length
            if len(filename) >= max_length:
                return filename

            # Calculate how much of the directory we can show
            remaining = max_length - len(filename) - 4  # 4 for ".../""

            # Try to show as much of the parent directory as possible
            parent_str = str(path_obj.parent)
            if len(parent_str) <= remaining:
                return f"{parent_str}/{filename}"

            # Show the beginning and end of the path
            if remaining > 10:
                start = parent_str[: remaining // 2 - 2]
                end = parent_str[-(remaining // 2 - 2) :]
                return f"{start}...{end}/{filename}"
            else:
                return f".../{filename}"
        else:
            # Normal truncation - can truncate filename too
            if len(filename) >= max_length - 3:
                return f"...{filename[-(max_length - 3) :]}"

            # Show as much as possible
            if max_length > 20:
                return f"...{path[-(max_length - 3) :]}"
            else:
                return f"...{filename}"

    def success(self, message: str, title: str | None = None) -> None:
        """
        Display a success message with beautiful formatting.

        Args:
            message: The success message to display
            title: Optional title for the message
        """
        self._ensure_spacing()
        if title:
            panel = Panel(
                Text(message, style="success"),
                title=f"[success]✅ {title}[/success]",
                border_style="success",
                padding=(0, 2),
            )
            self.console.print(panel)
        else:
            self.console.print(f"[success]✅[/success] {message}")
        self._write_to_log(message, "SUCCESS")

    def info(self, message: str, title: str | None = None) -> None:
        """
        Display an informational message.

        Args:
            message: The info message to display
            title: Optional title for the message
        """
        self._ensure_spacing()
        if title:
            panel = Panel(
                message,
                title=f"[info]💡 {title}[/info]",
                border_style="info",
                padding=(0, 2),
            )
            self.console.print(panel)
        else:
            self.console.print(f"[info]💡[/info] {message}")
        self._write_to_log(message, "INFO")

    def warning(self, message: str, title: str | None = None) -> None:
        """
        Display a warning message.

        Args:
            message: The warning message to display
            title: Optional title for the message
        """
        self._ensure_spacing()
        if title:
            panel = Panel(
                Text(message, style="warning"),
                title=f"[warning]⚠️  {title}[/warning]",
                border_style="warning",
                padding=(0, 2),
            )
            self.console.print(panel)
        else:
            self.console.print(f"[warning]⚠️[/warning]  {message}")
        self._write_to_log(message, "WARNING")

    def error(self, message: str, title: str | None = None) -> None:
        """
        Display an error message.

        Args:
            message: The error message to display
            title: Optional title for the message
        """
        self._ensure_spacing()
        if title:
            panel = Panel(
                Text(message, style="error"),
                title=f"[error]❌ {title}[/error]",
                border_style="error",
                padding=(0, 2),
            )
            self.console.print(panel)
        else:
            self.console.print(f"[error]❌[/error] {message}")
        self._write_to_log(message, "ERROR")

    def debug(self, message: str) -> None:
        """
        Display a debug message (only if verbose mode is enabled).

        Args:
            message: The debug message to display
        """
        if self.verbose:
            # Don't add spacing for consecutive debug messages
            self.console.print(f"[debug]  🔍 {message}[/debug]")
        self._write_to_log(message, "DEBUG")

    def exception(self, message: str, exc_info: Exception | None = None) -> None:
        """
        Display an exception message with optional exception details.

        Args:
            message: The error message to display
            exc_info: Optional exception object for detailed info
        """
        self.error(message)
        if exc_info and self.verbose:
            self.console.print_exception(show_locals=False)
        self._write_to_log(f"{message} - {exc_info}" if exc_info else message, "ERROR")

    def _ensure_spacing(self) -> None:
        """Ensure proper spacing between messages and progress bars."""
        if self._last_was_progress:
            self.console.print()
            self._last_was_progress = False

    def print_header(self, title: str, subtitle: str | None = None) -> None:
        """
        Print a beautiful header for the application.

        Args:
            title: Main title
            subtitle: Optional subtitle
        """
        self.console.print()
        header_text = Text(title, style="bold bright_cyan")
        if subtitle:
            header_text.append(f"\n{subtitle}", style="dim white")

        panel = Panel(
            header_text,
            border_style="bright_cyan",
            padding=(1, 2),
            expand=False,
        )
        self.console.print(panel, justify="center")
        self.console.print()

    def print_file_operation(
        self,
        operation: str,
        source: str,
        target: str | None = None,
        status: str = "pending",
        show_full_path: bool = False,
    ) -> None:
        """
        Print a beautiful file operation message, responsive to terminal width.

        Args:
            operation: Type of operation (move, rename, etc.)
            source: Source file path
            target: Target file path (if applicable)
            status: Status of the operation (pending, success, failed)
            show_full_path: If True, show full paths without truncation
        """
        status_icons = {
            "pending": "⏳",
            "success": "✅",
            "failed": "❌",
            "processing": "→",
        }

        status_colors = {
            "pending": "yellow",
            "success": "success",
            "failed": "error",
            "processing": "info",
        }

        icon = status_icons.get(status, "❓")
        color = status_colors.get(status, "white")

        # Get terminal width to adapt display
        term_width = self._get_terminal_width()
        source_name = Path(source).name

        # For narrow terminals (< 80 chars), always use multi-line format
        if term_width < 80:
            self._print_narrow_format(icon, color, source_name, source, target)
        elif self.verbose or show_full_path:
            self._print_verbose_format(
                icon, color, operation, source_name, source, target
            )
        else:
            self._print_normal_format(
                icon, color, source_name, source, target, term_width
            )

    def _print_narrow_format(
        self,
        icon: str,
        color: str,
        source_name: str,
        source: str,  # noqa: ARG002
        target: str | None,
    ) -> None:
        """Print file operation in narrow terminal format (multi-line)."""
        # Always show full filename
        self.console.print(
            f"  [{color}]{icon}[/{color}] [filename]{source_name}[/filename]"
        )

        if target:
            target_name = Path(target).name
            target_dir = str(Path(target).parent)

            # Show target filename if different
            if target_name != source_name:
                self.console.print(
                    f"      [dim]→[/dim] [filename]{target_name}[/filename]"
                )

            # Show target directory
            self.console.print(f"      [dim]in[/dim] [path]{target_dir}[/path]")

    def _print_verbose_format(
        self,
        icon: str,
        color: str,
        operation: str,
        source_name: str,
        source: str,
        target: str | None,
    ) -> None:
        """Print file operation in verbose format with full paths."""
        self.console.print(
            f"  [{color}]{icon}[/{color}] [bold]{operation}[/bold]: "
            f"[filename]{source_name}[/filename]"
        )
        self.console.print(f"      [dim]From:[/dim] [path]{source}[/path]")

        if target:
            self.console.print(f"      [dim]To:[/dim]   [path]{target}[/path]")

    def _print_normal_format(
        self,
        icon: str,
        color: str,
        source_name: str,
        source: str,
        target: str | None,
        term_width: int,
    ) -> None:
        """Print file operation in normal format, adapting to terminal width."""
        if not target:
            self.console.print(
                f"  [{color}]{icon}[/{color}] [filename]{source_name}[/filename]"
            )
            return

        # Calculate available space
        # Account for: "  " (2) + icon (2) + " " (1) + " → " (3) = 8 chars overhead
        filename_len = len(source_name)
        available = term_width - 8 - filename_len

        if available > 30:
            # Enough space for single line with truncated path
            display_target = self._truncate_path(
                target, available, preserve_filename=False
            )
            self.console.print(
                f"  [{color}]{icon}[/{color}] [filename]{source_name}[/filename] "
                f"[dim]→[/dim] [path]{display_target}[/path]"
            )
        else:
            # Not enough space - use multi-line format
            self._print_narrow_format(icon, color, source_name, source, target)

    def create_progress(self, description: str = "Processing...") -> Any:  # noqa: ARG002
        """
        Create a beautiful progress bar for long operations.

        Args:
            description: Description for the progress bar

        Returns:
            A configured Rich Progress object
        """
        self._last_was_progress = True
        return Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )

    def print_summary_table(self, title: str, data: list[tuple[str, str]]) -> None:
        """
        Print a beautiful summary table.

        Args:
            title: Table title
            data: List of (key, value) tuples to display
        """
        self._ensure_spacing()
        table = Table(title=title, show_header=False, border_style="bright_cyan")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        for key, value in data:
            table.add_row(key, value)

        self.console.print(table)
        self.console.print()

    def print_divider(self, text: str | None = None) -> None:
        """
        Print a beautiful divider line.

        Args:
            text: Optional text to display in the divider
        """
        self._ensure_spacing()
        if text:
            self.console.rule(f"[cyan]{text}[/cyan]", style="dim cyan")
        else:
            self.console.rule(style="dim cyan")

    def ask_confirmation(self, question: str, default: bool = False) -> bool:
        """
        Ask user for confirmation with beautiful formatting.

        Args:
            question: The question to ask
            default: Default answer if user just presses Enter

        Returns:
            User's response as boolean
        """
        self._ensure_spacing()
        default_text = "[Y/n]" if default else "[y/N]"
        response = (
            self.console.input(
                f"[yellow]❓[/yellow] {question} [dim]{default_text}[/dim]: "
            )
            .strip()
            .lower()
        )

        if not response:
            return default

        return response in ["y", "yes"]


# Global console instance
console = BeautifulConsole()


def set_verbose_mode(verbose: bool = False) -> None:
    """
    Set the console to verbose mode.

    Args:
        verbose: If True, show debug messages
    """
    global console
    console = BeautifulConsole(verbose=verbose)
    if verbose:
        console.debug("Verbose mode enabled")
