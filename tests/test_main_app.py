"""Tests for the main module."""

from pathlib import Path

from anime_librarian.main import create_file_renamer


def test_create_file_renamer():
    """Test the create_file_renamer factory function."""
    source_path = Path("/test/source")
    target_path = Path("/test/target")

    renamer = create_file_renamer(source_path, target_path)

    assert renamer is not None
    assert renamer.source_path == source_path
    assert renamer.target_path == target_path
