"""Tests for output formats in RichOutputWriter."""

import json

from anime_librarian.rich_output_writer import RichOutputWriter


def test_display_file_moves_plain() -> None:
    """Plain format prints minimal 'source -> target' lines without styling."""
    writer = RichOutputWriter()
    pairs = [("a.mp4", "b.mp4"), ("x.mkv", "y.mkv")]

    outputs: list[str] = []

    def capture(content: str, *_args: object, **_kwargs: object) -> None:
        outputs.append(content)

    writer.console.print_raw = capture  # type: ignore[assignment]

    writer.display_file_moves_table(pairs, output_format="plain")
    out = "\n".join(outputs)

    assert "a.mp4 -> b.mp4" in out
    assert "x.mkv -> y.mkv" in out


def test_display_file_moves_json_outputs_ndjson() -> None:
    """JSON format now emits newline-delimited JSON records."""
    writer = RichOutputWriter()
    pairs = [("a.mp4", "b.mp4"), ("x.mkv", "y.mkv")]

    outputs: list[str] = []

    def capture(content: str, *_args: object, **_kwargs: object) -> None:
        outputs.append(content)

    writer.console.print_raw = capture  # type: ignore[assignment]

    writer.display_file_moves_table(pairs, output_format="json")
    out = "\n".join(outputs)

    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"source": "a.mp4", "target": "b.mp4"}
    assert json.loads(lines[1]) == {"source": "x.mkv", "target": "y.mkv"}


def test_display_file_moves_default_uses_simple_layout() -> None:
    writer = RichOutputWriter()
    pairs = [("a.mp4", "b.mp4"), ("x.mkv", "y.mkv")]

    outputs: list[str] = []

    def capture(content: str, *_args: object, **_kwargs: object) -> None:
        outputs.append(content)

    writer.console.print_raw = capture  # type: ignore[assignment]

    writer.display_file_moves_table(pairs)

    assert outputs[0] == "Planned file moves:"
    assert outputs[1] == "  - a.mp4"
    assert outputs[2] == "    -> b.mp4"
    assert outputs[3] == "  - x.mkv"
    assert outputs[4] == "    -> y.mkv"
