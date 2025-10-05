"""Tests for structlog integration and configuration utilities."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from anime_librarian.logging_config import configure_logging, get_logger

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture, CaptureResult


def _read_last_json_line(err: str, out: str) -> dict[str, object]:
    stream = err or out
    lines = [line.strip() for line in stream.splitlines() if line.strip()]
    assert lines, "Expected logging output but none was captured."
    return json.loads(lines[-1])


def test_configure_logging_emits_structured_json(
    capfd: CaptureFixture[str],
) -> None:
    """configure_logging should emit JSON-formatted structured events."""
    configure_logging(json_output=True)
    _ignored: CaptureResult[str] = capfd.readouterr()
    del _ignored

    logger = get_logger("test.logging")
    logger.info("test_event", files=3)

    captured: CaptureResult[str] = capfd.readouterr()
    record = _read_last_json_line(captured.err, captured.out)

    assert record["message"] == "test_event"
    assert record["files"] == 3
    assert record["level"] == "info"
    assert "timestamp" in record


def test_configure_logging_is_idempotent(
    capfd: CaptureFixture[str],
) -> None:
    """Calling configure_logging repeatedly should not duplicate handlers."""
    configure_logging(json_output=True)
    configure_logging(json_output=True)
    _ignored: CaptureResult[str] = capfd.readouterr()
    del _ignored

    logger = get_logger("test.logging")
    logger.warning("idempotent_check", attempt=2)

    captured: CaptureResult[str] = capfd.readouterr()
    stream: str = captured.err or captured.out
    occurrences = sum(1 for line in stream.splitlines() if "idempotent_check" in line)
    assert occurrences == 1


def test_get_logger_binds_initial_context(
    capfd: CaptureFixture[str],
) -> None:
    """get_logger should attach initial context for subsequent events."""
    configure_logging(json_output=True)
    _ignored: CaptureResult[str] = capfd.readouterr()
    del _ignored

    logger = get_logger("test.logging", component="core", operation="rename")
    logger.info("binding_check")

    captured: CaptureResult[str] = capfd.readouterr()
    record = _read_last_json_line(captured.err, captured.out)

    assert record["component"] == "core"
    assert record["operation"] == "rename"
    assert record["message"] == "binding_check"
