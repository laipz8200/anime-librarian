"""Tests for the config module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from anime_librarian.config import get_source_path, get_target_path


def test_get_source_path_success():
    """Test get_source_path when the path is set."""
    with (
        patch.dict(os.environ, {"ANIMELIBRARIAN_SOURCE_PATH": "/test/source"}),
        patch("anime_librarian.config.DEFAULT_SOURCE_PATH", "/test/source"),
    ):
        path = get_source_path()
        assert path == Path("/test/source")


def test_get_source_path_error():
    """Test get_source_path when the path is not set."""
    with patch("anime_librarian.config.DEFAULT_SOURCE_PATH", ""):
        with pytest.raises(ValueError, match="Source path not set") as excinfo:
            get_source_path()
        assert "ANIMELIBRARIAN_SOURCE_PATH" in str(excinfo.value)


def test_get_target_path_success():
    """Test get_target_path when the path is set."""
    with (
        patch.dict(os.environ, {"ANIMELIBRARIAN_TARGET_PATH": "/test/target"}),
        patch("anime_librarian.config.DEFAULT_TARGET_PATH", "/test/target"),
    ):
        path = get_target_path()
        assert path == Path("/test/target")


def test_get_target_path_error():
    """Test get_target_path when the path is not set."""
    with patch("anime_librarian.config.DEFAULT_TARGET_PATH", ""):
        with pytest.raises(ValueError, match="Target path not set") as excinfo:
            get_target_path()
        assert "ANIMELIBRARIAN_TARGET_PATH" in str(excinfo.value)


def test_user_name_default():
    """Test USER_NAME has the correct default value."""
    with patch.dict(os.environ, {}, clear=True):
        # Reload the config module to reset USER_NAME
        import importlib

        import anime_librarian.config

        importlib.reload(anime_librarian.config)

        # Check the default value
        assert anime_librarian.config.USER_NAME == "Anime Librarian"


def test_user_name_from_env():
    """Test USER_NAME can be set from environment variable."""
    with patch.dict(os.environ, {"ANIMELIBRARIAN_USER_NAME": "Custom User"}):
        # Reload the config module to reset USER_NAME
        import importlib

        import anime_librarian.config

        importlib.reload(anime_librarian.config)

        # Check the value from environment
        assert anime_librarian.config.USER_NAME == "Custom User"
