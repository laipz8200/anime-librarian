"""Tests covering BeautifulConsole behavior."""

from pathlib import Path

import pytest

from anime_librarian.console import BeautifulConsole


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
