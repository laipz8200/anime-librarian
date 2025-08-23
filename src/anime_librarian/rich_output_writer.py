"""Rich-enhanced output writer implementation for the AnimeLibrarian application."""

from collections.abc import Sequence

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

from .types import OutputWriter


class RichOutputWriter(OutputWriter):
    """Rich-enhanced implementation of OutputWriter for better UX."""

    def __init__(self, verbose: bool = False, *, no_color: bool = False) -> None:
        """
        Initialize with verbosity setting.

        Args:
            verbose: If True, show verbose output
            no_color: If True, disable colored output
        """
        self.verbose = verbose
        # Force terminal for consistent formatting; allow disabling color
        color_system = None if no_color else "auto"
        self.console = Console(force_terminal=True, color_system=color_system)

    def message(self, message: str) -> None:
        """
        Print informational or success message only in verbose mode.

        Args:
            message: The message to print
        """
        if self.verbose:
            self.console.print(f"[dim]{message}[/dim]")

    def notice(self, message: str) -> None:
        """
        Always print error or warning message.

        Args:
            message: The message to print
        """
        # Determine the style based on message content
        if "error" in message.lower():
            style = "bold red"
        elif "warning" in message.lower():
            style = "bold yellow"
        else:
            style = "bold cyan"

        self.console.print(message, style=style)

    def list_items(
        self, header: str, items: Sequence[str], always_show: bool = False
    ) -> None:
        """
        Print a list of items with a header using Rich formatting.

        Args:
            header: The header to display
            items: The items to list
            always_show: If True, show even in non-verbose mode
        """
        if not self.verbose and not always_show:
            return

        # Create a styled header
        self.console.print()
        self.console.print(header, style="bold cyan")

        # Display items with bullet points and indentation
        for item in items:
            self.console.print(f"  • {item}", style="dim")

    def display_file_moves_table(
        self, file_pairs: Sequence[tuple[str, str]], output_format: str | None = None
    ) -> None:
        """
        Display planned file moves in the requested format.

        Args:
            file_pairs: List of (source, target) file name pairs
            output_format: One of {table, plain, json, ndjson}. Defaults to table.
        """
        fmt = (output_format or "table").lower()

        # Plain format: minimal, machine-friendly-ish text with no styling
        if fmt == "plain":
            for source, target in file_pairs:
                self.console.print(f"{source} -> {target}", markup=False)
            return

        if fmt in {"json", "ndjson"}:
            try:
                import json
            except Exception:  # pragma: no cover - if json import fails, fallback
                fmt = "table"
            else:
                records = [
                    {"source": source, "target": target}
                    for source, target in file_pairs
                ]
                if fmt == "json":
                    self.console.print(
                        json.dumps(records, ensure_ascii=False, indent=2)
                    )
                else:  # ndjson
                    for rec in records:
                        self.console.print(json.dumps(rec, ensure_ascii=False))
                return

        # Check terminal width to decide on table layout
        term_width = self.console.width

        # For very narrow terminals, use a list format instead of table
        if term_width < 100:
            # Minimal output: no title banner
            self.console.print()
            for source, target in file_pairs:
                self.console.print(f"  [yellow]{source}[/yellow]")
                if target != source:
                    self.console.print(f"    [dim]→[/dim] [green]{target}[/green]")
                self.console.print()
        else:
            # Use table for wider terminals
            table = Table(
                title=None,
                show_header=True,
                header_style="bold cyan",
                expand=True,  # Use full terminal width
                padding=(0, 1),  # Reduce padding to save space
            )

            # Calculate column widths dynamically
            # Reserve 5 chars for arrow column, split rest between source and target
            available = term_width - 7  # Account for borders and arrow
            col_width = available // 2

            table.add_column(
                "Source",
                style="yellow",
                no_wrap=False,
                overflow="fold",  # Fold long text instead of truncating
                min_width=20,
                max_width=col_width,
            )
            table.add_column("→", justify="center", style="dim", width=3)
            table.add_column(
                "Target",
                style="green",
                no_wrap=False,
                overflow="fold",  # Fold long text instead of truncating
                min_width=20,
                max_width=col_width,
            )

            for source, target in file_pairs:
                table.add_row(source, "→", target)

            self.console.print()
            self.console.print(table)

    def display_progress(self, description: str) -> Progress:
        """
        Create and return a progress indicator.

        Args:
            description: Description of the operation

        Returns:
            A Rich Progress instance
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )
        progress.add_task(description, total=None)
        return progress

    def success(self, message: str) -> None:
        """
        Display a success message with green styling.

        Args:
            message: The message to print
        """
        self.console.print(f"✅ {message}", style="bold green")

    def error(self, message: str) -> None:
        """
        Display an error message with red styling.

        Args:
            message: The message to print
        """
        self.console.print(f"❌ {message}", style="bold red")

    def warning(self, message: str) -> None:
        """
        Display a warning message with yellow styling.

        Args:
            message: The message to print
        """
        self.console.print(f"⚠️  {message}", style="bold yellow")

    def info(self, message: str) -> None:
        """
        Display an info message with blue styling.

        Args:
            message: The message to print
        """
        if self.verbose:
            self.console.print(f"[INFO] {message}", style="blue")

    def display_summary_panel(self, title: str, content: str) -> None:
        """
        Display a summary panel with formatted content.

        Args:
            title: Panel title
            content: Panel content
        """
        panel = Panel(content, title=title, border_style="cyan", padding=(1, 2))
        self.console.print()
        self.console.print(panel)


class RichInputReader:
    """Rich-enhanced input reader for interactive prompts."""

    def __init__(self, *, no_color: bool = False) -> None:
        """Initialize the Rich input reader."""
        # Force terminal; allow disabling color
        color_system = None if no_color else "auto"
        self.console = Console(force_terminal=True, color_system=color_system)

    def confirm(self, prompt: str, default: bool = False) -> bool:
        """
        Ask for user confirmation with a styled prompt.

        Args:
            prompt: The prompt to display
            default: Default value if user just presses Enter

        Returns:
            True if confirmed, False otherwise
        """
        return Confirm.ask(prompt, default=default, console=self.console)

    def read_input(self, prompt: str) -> str:
        """
        Read user input with a styled prompt.

        Args:
            prompt: The prompt to display

        Returns:
            User input as a string
        """
        return self.console.input(f"[bold cyan]{prompt}[/bold cyan]")
