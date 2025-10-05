"""Configuration provider implementation for the AnimeLibrarian application."""

from pathlib import Path

from . import config
from .types import ConfigProvider


class DefaultConfigProvider(ConfigProvider):
    """Default implementation of ConfigProvider using the config module."""

    def get_source_path(self) -> Path:
        """
        Get the source path from the config module.

        Returns:
            The source path
        """
        return config.get_source_path()

    def get_target_path(self) -> Path:
        """
        Get the target path from the config module.

        Returns:
            The target path
        """
        return config.get_target_path()
