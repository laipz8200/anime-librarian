# ruff: noqa: D102
"""Plain-text console utilities for AnimeLibrarian."""

from __future__ import annotations

import shutil
import sys
import traceback
from pathlib import Path
from typing import Any

from anime_librarian.enums import FileOperation, PreviewType, ProcessingStatus


class _NullProgress:
    """Minimal progress helper used when rich is unavailable."""

    def __init__(self, description: str) -> None:
        self.description = description

    def add_task(self, *_args: Any, **_kwargs: Any) -> int:
        """Return a dummy task id."""
        return 0

    def update(self, *_args: Any, **_kwargs: Any) -> None:
        """Ignore progress updates."""

    def advance(self, *_args: Any, **_kwargs: Any) -> None:
        """Ignore progress advancement."""

    def stop(self) -> None:
        """No-op to mirror rich API."""

    def __enter__(self) -> _NullProgress:
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> bool:
        return False


class BeautifulConsole:
    """Plain console output handler (no color codes or rich dependencies)."""

    _last_was_progress: bool

    def __init__(self) -> None:
        self._last_was_progress = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _terminal_width(self) -> int:
        return shutil.get_terminal_size((80, 20)).columns

    @property
    def width(self) -> int:
        """Expose terminal width for compatibility with existing callers."""
        return self._terminal_width()

    def _print(self, message: str = "", *, stream: Any = sys.stdout) -> None:
        print(message, file=stream)

    def input(self, prompt: str = "") -> str:
        """Read raw input using the built-in prompt."""
        return input(prompt)

    def _ensure_spacing(self) -> None:
        if self._last_was_progress:
            self._print()
            self._last_was_progress = False

    def _truncate_path(
        self, path: str, max_length: int = 60, *, preserve_filename: bool = True
    ) -> str:
        if len(path) <= max_length:
            return path

        path_obj = Path(path)
        filename = path_obj.name

        if preserve_filename:
            if len(filename) >= max_length:
                return filename[-max_length:]

            remaining = max_length - len(filename) - 4
            parent_str = str(path_obj.parent)
            if len(parent_str) <= remaining:
                return f"{parent_str}/{filename}"

            if remaining > 10:
                start = parent_str[: remaining // 2 - 2]
                end = parent_str[-(remaining // 2 - 2) :]
                return f"{start}...{end}/{filename}"
            return f".../{filename}"

        if len(filename) >= max_length - 3:
            return f"...{filename[-(max_length - 3) :]}"
        if max_length > 20:
            return f"...{path[-(max_length - 3) :]}"
        return f"...{filename}"

    # ------------------------------------------------------------------
    # Message helpers
    # ------------------------------------------------------------------
    def success(self, message: str, title: str | None = None) -> None:
        self._ensure_spacing()
        if title:
            self._print(f"SUCCESS [{title}]: {message}")
        else:
            self._print(f"SUCCESS: {message}")

    def info(self, message: str, title: str | None = None) -> None:
        self._ensure_spacing()
        if title:
            self._print(f"INFO [{title}]: {message}")
        else:
            self._print(f"INFO: {message}")

    def warning(self, message: str, title: str | None = None) -> None:
        self._ensure_spacing()
        if title:
            self._print(f"WARNING [{title}]: {message}", stream=sys.stderr)
        else:
            self._print(f"WARNING: {message}", stream=sys.stderr)

    def error(self, message: str, title: str | None = None) -> None:
        self._ensure_spacing()
        if title:
            self._print(f"ERROR [{title}]: {message}", stream=sys.stderr)
        else:
            self._print(f"ERROR: {message}", stream=sys.stderr)

    def debug(self, message: str) -> None:
        """Ignore debug messages (logging removed)."""
        _ = message

    def exception(self, message: str, exc_info: Exception | None = None) -> None:
        self.error(message)
        if exc_info:
            traceback.print_exception(
                exc_info.__class__, exc_info, exc_info.__traceback__
            )

    # ------------------------------------------------------------------
    # Structured output helpers
    # ------------------------------------------------------------------
    def print_header(self, title: str, subtitle: str | None = None) -> None:
        self._ensure_spacing()
        self._print()
        self._print(title)
        self._print("=" * len(title))
        if subtitle:
            self._print(subtitle)
        self._print()

    def print_file_operation(
        self,
        operation: str,
        source: str,
        target: str | None = None,
        status: str = "pending",
        show_full_path: bool = False,
    ) -> None:
        self._ensure_spacing()
        status_labels = {
            "pending": "PENDING",
            "success": "DONE",
            "failed": "FAILED",
            "processing": "WORKING",
        }
        label = status_labels.get(status, status.upper())
        source_name = Path(source).name
        pieces = [label, operation.capitalize(), source_name]

        if target:
            display_target = (
                target if show_full_path else self._truncate_path(target, 60)
            )
            pieces.append(f"-> {display_target}")
        line = " ".join(pieces)
        self._print(line)
        if show_full_path and target:
            self._print(f"  from: {source}")
            self._print(f"    to: {target}")

    def create_progress(self, description: str = "Processing...") -> _NullProgress:
        self._last_was_progress = True
        self._print(f"PROGRESS: {description}")
        return _NullProgress(description)

    def print_summary_table(self, title: str, data: list[tuple[str, str]]) -> None:
        self._ensure_spacing()
        self._print(title)
        self._print("-" * len(title))
        for key, value in data:
            self._print(f"{key}: {value}")
        self._print()

    def print_divider(self, text: str | None = None) -> None:
        self._ensure_spacing()
        width = self.width
        if text:
            text_str = f" {text} "
            remaining = max(width - len(text_str), 0)
            left = remaining // 2
            right = remaining - left
            self._print(f"{'-' * left}{text_str}{'-' * right}")
        else:
            self._print("-" * width)

    def ask_confirmation(self, question: str, default: bool = False) -> bool:
        self._ensure_spacing()
        sanitized = question.rstrip().rstrip("?: ").strip()
        if not sanitized:
            sanitized = "Are you sure"
        choice_hint = "[Y/n]" if default else "[y/N]"
        prompt = f"{sanitized} {choice_hint}: "
        response = self.input(prompt).strip().lower()
        if not response:
            return default
        return response in {"y", "yes"}

    def show_progress(self, status: ProcessingStatus, content: str) -> None:
        self._ensure_spacing()
        label = status.name.replace("_", " ").title()
        self._print(f"{label}: {content}")

    def show_change_preview(
        self,
        before: str,
        after: str,
        preview_type: PreviewType = PreviewType.RENAME_PREVIEW,
    ) -> None:
        self._ensure_spacing()
        if preview_type == PreviewType.RENAME_PREVIEW:
            heading = "Rename"
        elif preview_type == PreviewType.MOVE_PREVIEW:
            heading = "Move"
        else:
            heading = "Conflict"
        self._print(f"{heading}: {before} -> {after}")

    def show_file_list(self, title: str, files: list[str], style: str = "") -> None:
        _ = style  # Parameter kept for compatibility; ignored now.
        if not files:
            return
        self._ensure_spacing()
        self._print(title)
        for file in files:
            self._print(f"  - {file}")

    def show_operation_result(
        self,
        operation: FileOperation,
        source: str,
        target: str | None = None,
        success: bool = True,
        message: str | None = None,
    ) -> None:
        self._ensure_spacing()
        verb_map = {
            FileOperation.RENAME: "Renamed",
            FileOperation.MOVE: "Moved",
            FileOperation.COPY: "Copied",
            FileOperation.DELETE: "Deleted",
            FileOperation.CREATE_DIR: "Created",
        }
        verb = verb_map.get(operation, operation.value.title())
        status = "OK" if success else "ERROR"
        if target:
            line = f"{status} {verb}: {source} -> {target}"
        else:
            line = f"{status} {verb}: {source}"
        if message:
            line += f" ({message})"
        self._print(line)

    def show_statistics(self, stats: dict[str, int | str]) -> None:
        self._ensure_spacing()
        self._print("Statistics")
        self._print("-" * len("Statistics"))
        for key, value in stats.items():
            self._print(f"{key}: {value}")
        self._print()

    def print_raw(self, content: str, markup: bool = True) -> None:
        _ = markup  # kept for compatibility
        self._ensure_spacing()
        self._print(content)


# Global console instance for backward compatibility
console = BeautifulConsole()


def set_verbose_mode(verbose: bool = False) -> None:
    """Maintain backward compatibility with legacy CLI flags."""
    _ = verbose
