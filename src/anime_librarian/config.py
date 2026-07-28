"""Runtime settings loaded from CLI overrides and the environment."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .errors import ConfigurationError

DEFAULT_DIFY_ENDPOINT = "https://api.dify.ai/v1/workflows/run"
DEFAULT_API_TIMEOUT = 300
DEFAULT_USER_NAME = "Anime Librarian"


@dataclass(frozen=True, slots=True)
class Settings:
    """Resolved settings for one organization run."""

    source_path: Path
    target_path: Path
    api_endpoint: str
    api_key: str
    api_timeout: int
    user_name: str


def load_settings(
    source: Path | None = None,
    target: Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Resolve and validate settings without retaining global state."""
    if environ is None:
        _ = load_dotenv()
        environ = os.environ

    source_path = source or _path_from_environment(
        environ, "ANIMELIBRARIAN_SOURCE_PATH", "source directory"
    )
    target_path = target or _path_from_environment(
        environ, "ANIMELIBRARIAN_TARGET_PATH", "target directory"
    )
    api_key = environ.get("ANIMELIBRARIAN_DIFY_API_KEY", "").strip()
    if not api_key:
        message = "Dify API key is missing; set ANIMELIBRARIAN_DIFY_API_KEY."
        raise ConfigurationError(message)

    api_endpoint = environ.get(
        "ANIMELIBRARIAN_DIFY_WORKFLOW_RUN_ENDPOINT", DEFAULT_DIFY_ENDPOINT
    ).strip()
    if not api_endpoint:
        message = "Dify workflow endpoint cannot be empty."
        raise ConfigurationError(message)

    timeout_value = environ.get("ANIMELIBRARIAN_API_TIMEOUT", str(DEFAULT_API_TIMEOUT))
    try:
        api_timeout = int(timeout_value)
    except ValueError as error:
        message = "API timeout must be a positive integer."
        raise ConfigurationError(message) from error
    if api_timeout <= 0:
        message = "API timeout must be a positive integer."
        raise ConfigurationError(message)

    return Settings(
        source_path=_expand_path(source_path, "source directory"),
        target_path=_expand_path(target_path, "target directory"),
        api_endpoint=api_endpoint,
        api_key=api_key,
        api_timeout=api_timeout,
        user_name=environ.get("ANIMELIBRARIAN_USER_NAME", DEFAULT_USER_NAME).strip()
        or DEFAULT_USER_NAME,
    )


def _path_from_environment(
    environ: Mapping[str, str], variable: str, label: str
) -> Path:
    value = environ.get(variable, "").strip()
    if not value:
        message = f"No {label} configured; pass its CLI option or set {variable}."
        raise ConfigurationError(message)
    return Path(value)


def _expand_path(path: Path, label: str) -> Path:
    try:
        return path.expanduser()
    except RuntimeError as error:
        message = f"Cannot expand {label} path: {path}"
        raise ConfigurationError(message) from error
