"""Tests for output formats in RichOutputWriter."""

import json

import pytest

from anime_librarian.rich_output_writer import RichOutputWriter


def test_display_file_moves_plain(capsys: pytest.CaptureFixture[str]) -> None:
    """Plain format prints minimal 'source -> target' lines without styling."""
    writer = RichOutputWriter(no_color=True)
    pairs = [("a.mp4", "b.mp4"), ("x.mkv", "y.mkv")]

    writer.display_file_moves_table(pairs, output_format="plain")
    out = capsys.readouterr().out

    assert "a.mp4 -> b.mp4" in out
    assert "x.mkv -> y.mkv" in out


def test_display_file_moves_json_indented(capsys: pytest.CaptureFixture[str]) -> None:
    """JSON format prints an indented array with indent=2 and valid JSON."""
    writer = RichOutputWriter(no_color=True)
    pairs = [("a.mp4", "b.mp4"), ("x.mkv", "y.mkv")]

    writer.display_file_moves_table(pairs, output_format="json")
    out = capsys.readouterr().out

    # Valid JSON and expected content
    data = json.loads(out)
    assert data == [
        {"source": "a.mp4", "target": "b.mp4"},
        {"source": "x.mkv", "target": "y.mkv"},
    ]

    # Pretty-printed with 2-space indentation (check representative pattern)
    assert "\n  {" in out  # two spaces before object


def test_display_file_moves_ndjson(capsys: pytest.CaptureFixture[str]) -> None:
    """NDJSON format prints one JSON object per line."""
    writer = RichOutputWriter(no_color=True)
    pairs = [("a.mp4", "b.mp4"), ("x.mkv", "y.mkv")]

    writer.display_file_moves_table(pairs, output_format="ndjson")
    out = capsys.readouterr().out

    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"source": "a.mp4", "target": "b.mp4"}
    assert json.loads(lines[1]) == {"source": "x.mkv", "target": "y.mkv"}
