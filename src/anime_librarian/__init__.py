"""AnimeLibrarian - A tool that uses AI to rename and organize video files."""

__version__ = "0.4.0"

from .logging_config import configure_logging, get_logger

__all__ = [
    "__version__",
    "configure_logging",
    "get_logger",
]
