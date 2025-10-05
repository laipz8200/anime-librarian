"""Tests verifying structlog defaults behave as expected for the app."""

from __future__ import annotations

import structlog
from structlog.testing import capture_logs


def test_structlog_capture_logs_produces_event_dict() -> None:
    """capture_logs should record structured events with context."""
    with capture_logs() as logs:
        structlog.get_logger("test").bind(component="core").info(
            "binding_check", files=2
        )

    assert len(logs) == 1
    entry = logs[0]
    assert entry["event"] == "binding_check"
    assert entry["component"] == "core"
    assert entry["files"] == 2


def test_structlog_capture_logs_records_multiple_events() -> None:
    """Multiple log events should be collected in order."""
    with capture_logs() as logs:
        logger = structlog.get_logger("test")
        logger.info("first")
        logger.info("second")

    assert [entry["event"] for entry in logs] == ["first", "second"]
