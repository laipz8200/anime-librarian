"""One terminal boundary for interactive and machine-readable output."""

import unicodedata
from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING

from rich import box
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

from .models import FileMove

if TYPE_CHECKING:
    from .main import OutputFormat


class Terminal:
    """Render plans on stdout and interaction/status messages on stderr."""

    def __init__(
        self,
        *,
        stdout: Console | None = None,
        stderr: Console | None = None,
    ) -> None:
        self.stdout = stdout or Console()
        self.stderr = stderr or Console(stderr=True)

    def show_plan(
        self,
        moves: Sequence[FileMove],
        target_root: Path,
        output_format: "OutputFormat",
    ) -> None:
        """Render a plan in the selected human or streaming format."""
        rows = [
            (move.source.name, self._relative_target(move.target, target_root))
            for move in moves
        ]
        if str(output_format) == "plain":
            for source, target in rows:
                self.stdout.print(
                    f"{_escape_unsafe(source)} -> {_escape_unsafe(target)}",
                    markup=False,
                    highlight=False,
                    soft_wrap=True,
                )
            return
        if str(output_format) == "json":
            import json

            for source, target in rows:
                self.stdout.print(
                    json.dumps(
                        {"source": source, "target": target},
                        ensure_ascii=True,
                    ),
                    markup=False,
                    highlight=False,
                    soft_wrap=True,
                )
            return

        table = Table(
            title=f"Move plan · {len(rows)} {_plural(len(rows), 'file')}",
            box=box.ROUNDED,
            header_style="bold cyan",
            show_lines=False,
            expand=True,
        )
        table.add_column("Current name", style="yellow", overflow="fold")
        table.add_column("New location", style="green", overflow="fold")
        for source, target in rows:
            table.add_row(Text(_escape_unsafe(source)), Text(_escape_unsafe(target)))
        self.stdout.print(table)

    def show_paths(self, title: str, paths: Sequence[Path], *, warning: bool) -> None:
        """Show a compact preflight list."""
        style = "yellow" if warning else "cyan"
        lines = Text()
        lines.append(f"{title}\n", style=f"bold {style}")
        for path in paths:
            lines.append("  • ", style=style)
            lines.append(f"{_escape_unsafe(str(path))}\n")
        self.stderr.print(lines, end="", soft_wrap=True)

    def info(self, message: str) -> None:
        """Write an informational status to stderr."""
        self._message("●", "cyan", message)

    def success(self, message: str) -> None:
        """Write a success status to stderr."""
        self._message("✓", "green", message)

    def warning(self, message: str) -> None:
        """Write a warning status to stderr."""
        self._message("!", "yellow", message)

    def error(self, message: str) -> None:
        """Write an error status to stderr."""
        self._message("x", "red", message)

    def confirm(self, question: str, *, default: bool) -> bool:
        """Ask one styled yes/no question."""
        return Confirm.ask(question, default=default, console=self.stderr)

    def status(self, message: str) -> AbstractContextManager[object]:
        """Show a transient spinner in interactive terminals."""
        if not self.stderr.is_terminal:
            return nullcontext()
        return self.stderr.status(f"[cyan]{message}[/cyan]", spinner="dots")

    def track(self, moves: Sequence[FileMove]) -> Iterable[FileMove]:
        """Track move progress when stderr is interactive."""
        if not self.stderr.is_terminal:
            return moves
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=self.stderr,
            transient=True,
        )
        return progress.track(moves, description="Moving files")

    def _message(self, symbol: str, style: str, message: str) -> None:
        self.stderr.print(
            Text.assemble((f"{symbol} ", f"bold {style}"), _escape_unsafe(message))
        )

    @staticmethod
    def _relative_target(target: Path, target_root: Path) -> str:
        try:
            relative = target.relative_to(target_root)
        except ValueError:
            relative = target.relative_to(target_root.resolve())
        return relative.as_posix()


def _plural(count: int, noun: str) -> str:
    return noun if count == 1 else f"{noun}s"


def _escape_unsafe(value: str) -> str:
    escaped: list[str] = []
    for character in value:
        if unicodedata.category(character) not in {"Cc", "Cf", "Cs", "Zl", "Zp"}:
            escaped.append(character)
            continue
        codepoint = ord(character)
        if codepoint <= 0xFF:
            escaped.append(f"\\x{codepoint:02x}")
        elif codepoint <= 0xFFFF:
            escaped.append(f"\\u{codepoint:04x}")
        else:
            escaped.append(f"\\U{codepoint:08x}")
    return "".join(escaped)
