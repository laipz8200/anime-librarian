from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from anime_librarian.console import Terminal
from anime_librarian.file_renamer import FileOrganizer
from anime_librarian.main import CliOptions, OutputFormat, main, run
from anime_librarian.models import FileMove, NamePair


class FailingOrganizer(FileOrganizer):
    def move(self, move: FileMove, *, overwrite: bool = False) -> None:
        _ = self
        _ = move
        _ = overwrite
        message = "read-only filesystem"
        raise PermissionError(message)


def make_terminal() -> tuple[Terminal, StringIO, StringIO]:
    stdout = StringIO()
    stderr = StringIO()
    return (
        Terminal(
            stdout=Console(file=stdout, force_terminal=False, width=100),
            stderr=Console(file=stderr, force_terminal=False, width=100),
        ),
        stdout,
        stderr,
    )


def test_dry_run_never_prompts_or_moves_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    media = source / "episode.mkv"
    media.touch()
    (target / "Series").mkdir()

    organizer = FileOrganizer(
        source,
        target,
        lambda _files, _directories: [
            NamePair(
                original_name="episode.mkv",
                new_name="Series/Series S01E01.mkv",
            )
        ],
    )
    terminal, stdout, stderr = make_terminal()

    def unexpected_prompt(_question: str, *, default: bool) -> bool:
        message = f"dry-run prompted with default={default}"
        raise AssertionError(message)

    terminal.confirm = unexpected_prompt  # type: ignore[method-assign]

    result = run(
        CliOptions(dry_run=True, output_format=OutputFormat.JSON),
        organizer,
        terminal,
    )

    assert result == 0
    assert media.exists()
    assert '"target": "Series/Series S01E01.mkv"' in stdout.getvalue()
    assert "Dry run" in stderr.getvalue()


def test_conflicts_use_one_safe_confirmation(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (source / "episode.mkv").touch()
    series = target / "Series"
    series.mkdir()
    (series / "Episode.mkv").touch()

    organizer = FileOrganizer(
        source,
        target,
        lambda _files, _directories: [
            NamePair(
                original_name="episode.mkv",
                new_name="Series/Episode.mkv",
            )
        ],
    )
    terminal, _, _ = make_terminal()
    prompts: list[tuple[str, bool]] = []

    def decline(question: str, *, default: bool) -> bool:
        prompts.append((question, default))
        return False

    terminal.confirm = decline  # type: ignore[method-assign]

    result = run(CliOptions(), organizer, terminal)

    assert result == 0
    assert len(prompts) == 1
    assert prompts[0][1] is False
    assert (source / "episode.mkv").exists()


def test_confirmed_plan_creates_directories_and_moves_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    media = source / "episode.mkv"
    media.write_text("video")
    (target / "Existing").mkdir()

    organizer = FileOrganizer(
        source,
        target,
        lambda _files, _directories: [
            NamePair(
                original_name="episode.mkv",
                new_name="New Series/Season 01/Episode.mkv",
            )
        ],
    )
    terminal, _, stderr = make_terminal()

    def confirm(_question: str, *, default: bool) -> bool:
        _ = default
        return True

    terminal.confirm = confirm  # type: ignore[method-assign]

    result = run(CliOptions(), organizer, terminal)

    assert result == 0
    assert not media.exists()
    assert (target / "New Series" / "Season 01" / "Episode.mkv").read_text() == (
        "video"
    )
    assert "Moved 1 file" in stderr.getvalue()


def test_move_failures_are_reported_without_losing_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    media = source / "episode.mkv"
    media.touch()
    (target / "Series").mkdir()
    organizer = FailingOrganizer(
        source,
        target,
        lambda _files, _directories: [
            NamePair(
                original_name="episode.mkv",
                new_name="Series/Episode.mkv",
            )
        ],
    )
    terminal, _, stderr = make_terminal()

    def confirm(_question: str, *, default: bool) -> bool:
        _ = default
        return True

    terminal.confirm = confirm  # type: ignore[method-assign]

    assert run(CliOptions(), organizer, terminal) == 1
    assert media.exists()
    assert "1 failed" in stderr.getvalue()
    assert "read-only filesystem" in stderr.getvalue()


def test_main_reports_invalid_proxy_without_a_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    monkeypatch.setenv("ANIMELIBRARIAN_SOURCE_PATH", str(source))
    monkeypatch.setenv("ANIMELIBRARIAN_TARGET_PATH", str(target))
    monkeypatch.setenv("ANIMELIBRARIAN_DIFY_API_KEY", "secret")
    monkeypatch.setenv("HTTP_PROXY", "http://[::1")
    monkeypatch.setenv("HTTPS_PROXY", "http://[::1")
    monkeypatch.setenv("ALL_PROXY", "http://[::1")

    assert main([]) == 2
    captured = capsys.readouterr()
    assert "Invalid HTTP configuration" in captured.err
    assert "Traceback" not in captured.err
