"""Tests for output formats in RichOutputWriter."""

import json

import pytest

from anime_librarian.rich_output_writer import RichOutputWriter


def test_display_file_moves_plain(capsys: pytest.CaptureFixture[str]) -> None:
    """Plain format prints minimal 'source -> target' lines without styling."""
    writer = RichOutputWriter()
    pairs = [("a.mp4", "b.mp4"), ("x.mkv", "y.mkv")]

    writer.display_file_moves_table(pairs, output_format="plain")
    out = capsys.readouterr().out

    assert "a.mp4 -> b.mp4" in out
    assert "x.mkv -> y.mkv" in out


def test_display_file_moves_json_outputs_ndjson(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON format now emits newline-delimited JSON records."""
    writer = RichOutputWriter()
    pairs = [("a.mp4", "b.mp4"), ("x.mkv", "y.mkv")]

    writer.display_file_moves_table(pairs, output_format="json")
    out = capsys.readouterr().out

    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"source": "a.mp4", "target": "b.mp4"}
    assert json.loads(lines[1]) == {"source": "x.mkv", "target": "y.mkv"}
