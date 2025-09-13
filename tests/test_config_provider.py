"""Tests for the config provider module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from anime_librarian.config_provider import DefaultConfigProvider


def test_default_config_provider_get_source_path():
    """Test DefaultConfigProvider.get_source_path method."""
    with patch(
        "anime_librarian.config.get_source_path", return_value=Path("/test/source")
    ):
        provider = DefaultConfigProvider()
        path = provider.get_source_path()
        assert path == Path("/test/source")


def test_default_config_provider_get_target_path():
    """Test DefaultConfigProvider.get_target_path method."""
    with patch(
        "anime_librarian.config.get_target_path", return_value=Path("/test/target")
    ):
        provider = DefaultConfigProvider()
        path = provider.get_target_path()
        assert path == Path("/test/target")


def test_default_config_provider_error_handling():
    """Test error handling in DefaultConfigProvider."""
    # Test error handling for get_source_path
    with patch(
        "anime_librarian.config.get_source_path",
        side_effect=ValueError("Source path error"),
    ):
        provider = DefaultConfigProvider()
        with pytest.raises(ValueError, match="Source path error"):
            _ = provider.get_source_path()

    # Test error handling for get_target_path
    with patch(
        "anime_librarian.config.get_target_path",
        side_effect=ValueError("Target path error"),
    ):
        provider = DefaultConfigProvider()
        with pytest.raises(ValueError, match="Target path error"):
            _ = provider.get_target_path()
