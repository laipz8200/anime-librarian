"""Centralised structlog configuration for AnimeLibrarian."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, TextIO

import structlog

_LOG_LEVEL_ENV = "ANIMELIBRARIAN_LOG_LEVEL"
_JSON_FLAG_ENV = "ANIMELIBRARIAN_LOG_JSON"
_DEFAULT_LEVEL = "INFO"


def _resolve_stream(stream: TextIO | None) -> TextIO:
    return stream if stream is not None else sys.stderr


def _resolve_level(level: int | str | None) -> int:
    if level is None:
        level_env = os.getenv(_LOG_LEVEL_ENV)
        level = level_env if level_env is not None else _DEFAULT_LEVEL

    if isinstance(level, int):
        return level

    normalized = level.upper()
    mapping = logging.getLevelNamesMapping()
    if normalized not in mapping:
        msg = f"Unsupported log level: {level}"
        raise ValueError(msg)
    return int(mapping[normalized])


def _resolve_json_flag(json_output: bool | None) -> bool:
    if json_output is not None:
        return json_output

    flag = os.getenv(_JSON_FLAG_ENV)
    if flag is None:
        return False

    normalized = flag.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def configure_logging(
    *,
    level: int | str | None = None,
    json_output: bool | None = None,
    stream: TextIO | None = None,
) -> None:
    """Configure structlog and stdlib logging with consistent processors."""
    resolved_stream = _resolve_stream(stream)
    resolved_level = _resolve_level(level)
    resolved_json = _resolve_json_flag(json_output)

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    final_processors = [
        structlog.processors.dict_tracebacks,
        structlog.processors.EventRenamer("message"),
    ]

    if resolved_json:
        renderer = structlog.processors.JSONRenderer(sort_keys=True)
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=False)

    processor_formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=[*shared_processors, *final_processors],
    )

    handler = logging.StreamHandler(resolved_stream)
    handler.setFormatter(processor_formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(resolved_level)

    structlog.configure(
        processors=[
            *shared_processors,
            *final_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(resolved_level),
        cache_logger_on_first_use=False,
    )


def get_logger(
    name: str | None = None, **initial_values: Any
) -> structlog.stdlib.BoundLogger:
    """Return a structlog BoundLogger with optional initial context."""
    logger = structlog.get_logger(name)
    if initial_values:
        logger = logger.bind(**initial_values)
    return logger
