"""Tests covering BeautifulConsole behavior."""

import builtins
from pathlib import Path

import pytest

from anime_librarian.console import BeautifulConsole
from anime_librarian.rich_output_writer import RichInputReader


@pytest.fixture(name="temporary_workspace")
def temporary_workspace_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Use an isolated working directory for console interactions."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_beautiful_console_does_not_create_log_files(
    temporary_workspace: Path,
) -> None:
    """Ensure instantiating and using the console does not produce log files."""
    console = BeautifulConsole()

    console.info("Hello world")

    logs_dir = temporary_workspace / "logs"
    assert not logs_dir.exists() or not any(logs_dir.iterdir())


def test_rich_input_reader_confirm_formats_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Confirm prompts strip punctuation and expose expected choices."""
    reader = RichInputReader()
    captured: dict[str, object] = {}

    def fake_input(prompt: str) -> str:
        captured["prompt"] = prompt
        return ""  # simulate pressing Enter

    monkeypatch.setattr(builtins, "input", fake_input)

    assert reader.confirm("Do you want to continue? :", default=False) is False
    assert captured["prompt"] == "Do you want to continue? [y/N]: "
