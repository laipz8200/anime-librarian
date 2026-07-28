"""Tests for the package version."""

import tomllib
from pathlib import Path

from anime_librarian import __version__


def test_version() -> None:
    """The package reports the released version."""
    metadata = tomllib.loads(Path("pyproject.toml").read_text())

    assert __version__ == "0.4.0"
    assert metadata["project"]["version"] == __version__
