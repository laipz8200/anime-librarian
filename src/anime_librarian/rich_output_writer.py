# ruff: noqa: D102
"""Plain-text output utilities for the AnimeLibrarian application."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
else:  # pragma: no cover - runtime fallback for type hints
    Sequence = tuple  # type: ignore[assignment]

from .console import BeautifulConsole
from .types import OutputWriter


class RichOutputWriter(OutputWriter):
    """Simple text implementation of the OutputWriter protocol."""

    console: BeautifulConsole

    def __init__(self) -> None:
        self.console = BeautifulConsole()

    def message(self, message: str) -> None:
        # Informational chatter remains muted by default.
        _ = message

    def notice(self, message: str) -> None:
        lower = message.lower()
        if "error" in lower:
            self.console.error(message)
        elif "warning" in lower:
            self.console.warning(message)
        else:
            self.console.info(message)

    def list_items(
        self, header: str, items: Sequence[str], always_show: bool = False
    ) -> None:
        if not always_show:
            return
        self.console.show_file_list(header, list(items))

    def display_file_moves_table(
        self, file_pairs: Sequence[tuple[str, str]], output_format: str | None = None
    ) -> None:
        fmt = (output_format or "table").lower()

        if fmt == "plain":
            for source, target in file_pairs:
                self.console.print_raw(f"{source} -> {target}")
            return

        if fmt == "json":
            for source, target in file_pairs:
                record = {"source": source, "target": target}
                self.console.print_raw(json.dumps(record, ensure_ascii=False))
            return

        if not file_pairs:
            self.console.print_raw("No planned file moves.")
            return

        self.console.print_raw("Planned file moves:")
        for source, target in file_pairs:
            self.console.print_raw(f"  - {source}")
            self.console.print_raw(f"    -> {target}")

    def display_progress(self, description: str):
        """Return a minimal progress helper."""
        return self.console.create_progress(description)

    def success(self, message: str) -> None:
        self.console.success(message)

    def error(self, message: str) -> None:
        self.console.error(message)

    def warning(self, message: str) -> None:
        self.console.warning(message)

    def info(self, message: str) -> None:
        self.console.info(message)

    def display_summary_panel(self, title: str, content: str) -> None:
        self.console.print_raw("")
        self.console.print_raw(title)
        self.console.print_raw("-" * len(title))
        for line in content.splitlines():
            self.console.print_raw(line)
        self.console.print_raw("")


class RichInputReader:
    """Plain-text input reader for interactive prompts."""

    console: BeautifulConsole

    def __init__(self) -> None:
        self.console = BeautifulConsole()

    def confirm(self, prompt: str, default: bool = False) -> bool:
        return self.console.ask_confirmation(prompt, default)

    def read_input(self, prompt: str) -> str:
        return self.console.input(f"{prompt}: ")
