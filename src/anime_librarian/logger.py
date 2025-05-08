"""
Logging configuration for the AnimeLibrarian application.

This module configures the loguru logger for the application.
"""

import sys
from pathlib import Path

from loguru import logger

# Remove the default handler
logger.remove()

# Add a handler for stdout with a nice format
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="WARNING",
)

# Add a handler for file logging
log_file = Path("logs") / "AnimeLibrarian.log"
log_file.parent.mkdir(exist_ok=True)
logger.add(
    log_file,
    rotation="10 MB",
    retention="1 week",
    compression="zip",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "{name}:{function}:{line} - {message}"
    ),
    level="DEBUG",
)


def set_verbose_mode(verbose: bool = False) -> None:
    """
    Set the logger to verbose mode.

    Args:
        verbose: If True, set the console logger to DEBUG level
    """
    if verbose:
        # Remove all handlers and re-add them
        logger.remove()

        # Add a handler for file logging
        logger.add(
            log_file,
            rotation="10 MB",
            retention="1 week",
            compression="zip",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} - {message}"
            ),
            level="DEBUG",
        )

        # Add a new handler with DEBUG level for stdout
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            level="DEBUG",
        )
        logger.debug("Verbose logging enabled")
