"""Tests for the command-line argument parser."""

from enum import StrEnum
from pathlib import Path

import pytest

from anime_librarian import __version__
from anime_librarian.main import OutputFormat, build_parser


def test_parser_defaults_to_table_output() -> None:
    args = build_parser().parse_args([])

    assert args.source is None
    assert args.target is None
    assert args.dry_run is False
    assert args.output_format is OutputFormat.TABLE
    assert issubclass(OutputFormat, StrEnum)
    assert {output_format.value for output_format in OutputFormat} == {
        "table",
        "plain",
        "json",
    }


@pytest.mark.parametrize(
    ("options", "output_format"),
    [
        (
            ["-s", "/incoming", "-t", "/library", "-n", "--format", "plain"],
            OutputFormat.PLAIN,
        ),
        (
            [
                "--source",
                "/incoming",
                "--target",
                "/library",
                "--dry-run",
                "--format",
                "json",
            ],
            OutputFormat.JSON,
        ),
    ],
)
def test_parser_accepts_short_and_long_options(
    options: list[str], output_format: OutputFormat
) -> None:
    args = build_parser().parse_args(options)

    assert args.source == Path("/incoming")
    assert args.target == Path("/library")
    assert args.dry_run is True
    assert args.output_format is output_format


@pytest.mark.parametrize("option", ["-V", "--version"])
def test_parser_reports_version(
    option: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args([option])

    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_help_does_not_expose_configured_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_source = "/Users/alice/Private/Incoming"
    private_target = "/Volumes/Media/Private/Library"
    monkeypatch.setenv("ANIMELIBRARIAN_SOURCE_PATH", private_source)
    monkeypatch.setenv("ANIMELIBRARIAN_TARGET_PATH", private_target)

    help_text = build_parser().format_help()

    assert private_source not in help_text
    assert private_target not in help_text


@pytest.mark.parametrize("option", ["--source", "--target"])
def test_parser_rejects_empty_directory_paths(option: str) -> None:
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args([option, "  "])

    assert exit_info.value.code == 2
