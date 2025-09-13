"""
Configuration module for the AnimeLibrarian application.

This module provides configuration values for the application, with defaults
that can be overridden through environment variables.
Environment variables can be set in a .env file at the root of the project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
_ = load_dotenv()

# API configuration
# NOTE: For security, set these values in your .env file instead of here
DIFY_WORKFLOW_RUN_ENDPOINT = os.environ.get(
    "ANIMELIBRARIAN_DIFY_WORKFLOW_RUN_ENDPOINT", "https://api.dify.ai/v1/workflows/run"
)
DIFY_API_KEY = os.environ.get(
    "ANIMELIBRARIAN_DIFY_API_KEY",
    "",  # Default empty, must be set in .env
)

# Default paths - should be set in .env to avoid privacy leaks
DEFAULT_SOURCE_PATH = os.environ.get(
    "ANIMELIBRARIAN_SOURCE_PATH",
    "",  # Default empty, must be set in .env
)
DEFAULT_TARGET_PATH = os.environ.get(
    "ANIMELIBRARIAN_TARGET_PATH",
    "",  # Default empty, must be set in .env
)

# API request timeout in seconds
API_TIMEOUT = int(os.environ.get("ANIMELIBRARIAN_API_TIMEOUT", "300"))

# User name for API requests
USER_NAME = os.environ.get("ANIMELIBRARIAN_USER_NAME", "Anime Librarian")


def get_source_path() -> Path:
    """
    Get the source path from environment or use default.

    Raises:
        ValueError: If the source path is not set in the environment
    """
    if not DEFAULT_SOURCE_PATH:
        msg = "Source path not set. Please set ANIMELIBRARIAN_SOURCE_PATH in .env file."
        raise ValueError(msg)
    return Path(DEFAULT_SOURCE_PATH)


def get_target_path() -> Path:
    """
    Get the target path from environment or use default.

    Raises:
        ValueError: If the target path is not set in the environment
    """
    if not DEFAULT_TARGET_PATH:
        msg = "Target path not set. Please set ANIMELIBRARIAN_TARGET_PATH in .env file."
        raise ValueError(msg)
    return Path(DEFAULT_TARGET_PATH)
