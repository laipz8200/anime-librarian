"""Tests for terminal plan output formats."""

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from rich.console import Console
from rich.table import Table

from anime_librarian.console import Terminal
from anime_librarian.main import OutputFormat
from anime_librarian.models import FileMove


def test_table_plan_uses_rich_table_and_keeps_destination_parent() -> None:
    output = StringIO()
    stdout = Console(file=output, force_terminal=False, width=120)
    terminal = Terminal(stdout=stdout)
    move = FileMove(
        source=Path("/incoming/[subsplease] Frieren 01.mkv"),
        target=Path("/library/Frieren/Season 01/Frieren - S01E01.mkv"),
    )

    with patch.object(stdout, "print", wraps=stdout.print) as print_spy:
        terminal.show_plan([move], Path("/library"), OutputFormat.TABLE)

    assert any(
        isinstance(renderable, Table)
        for call in print_spy.call_args_list
        for renderable in call.args
    )
    assert "[subsplease] Frieren 01.mkv" in output.getvalue()
    assert "Frieren/Season 01/Frieren - S01E01.mkv" in output.getvalue()


def test_plain_plan_is_unstyled_and_uses_relative_destination() -> None:
    output = StringIO()
    terminal = Terminal(stdout=Console(file=output, force_terminal=False))
    move = FileMove(
        source=Path("/incoming/Frieren 01.mkv"),
        target=Path("/library/Frieren/Season 01/Frieren - S01E01.mkv"),
    )

    terminal.show_plan([move], Path("/library"), OutputFormat.PLAIN)

    assert output.getvalue() == (
        "Frieren 01.mkv -> Frieren/Season 01/Frieren - S01E01.mkv\n"
    )
    assert "\x1b[" not in output.getvalue()


def test_json_plan_is_clean_ndjson() -> None:
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    terminal = Terminal(
        stdout=Console(file=stdout_buffer, force_terminal=False),
        stderr=Console(file=stderr_buffer, force_terminal=False),
    )
    moves = [
        FileMove(
            source=Path("/incoming/Frieren 01.mkv"),
            target=Path("/library/Frieren/Season 01/Frieren - S01E01.mkv"),
        ),
        FileMove(
            source=Path("/incoming/Frieren 02.mkv"),
            target=Path("/library/Frieren/Season 01/Frieren - S01E02.mkv"),
        ),
    ]

    terminal.show_plan(moves, Path("/library"), OutputFormat.JSON)

    assert [json.loads(line) for line in stdout_buffer.getvalue().splitlines()] == [
        {
            "source": "Frieren 01.mkv",
            "target": "Frieren/Season 01/Frieren - S01E01.mkv",
        },
        {
            "source": "Frieren 02.mkv",
            "target": "Frieren/Season 01/Frieren - S01E02.mkv",
        },
    ]
    assert stderr_buffer.getvalue() == ""


def test_human_output_escapes_terminal_control_characters() -> None:
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    terminal = Terminal(
        stdout=Console(file=stdout_buffer, force_terminal=False),
        stderr=Console(file=stderr_buffer, force_terminal=False),
    )
    move = FileMove(
        source=Path("/incoming/evil\x1b[31mRED\nnext.mkv"),
        target=Path("/library/Series/Episode.mkv"),
    )

    terminal.show_plan([move], Path("/library"), OutputFormat.PLAIN)
    terminal.error("bad\x1b[31merror\u2028next")

    assert "\x1b" not in stdout_buffer.getvalue()
    assert "\x1b" not in stderr_buffer.getvalue()
    assert "evil\\x1b[31mRED\\x0anext.mkv" in stdout_buffer.getvalue()
    assert "bad\\x1b[31merror\\u2028next" in stderr_buffer.getvalue()
