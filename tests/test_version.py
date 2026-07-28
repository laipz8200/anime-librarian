"""Tests for the package version."""

from anime_librarian import __version__


def test_version() -> None:
    """The package reports the released version."""
    assert __version__ == "0.3.1"
