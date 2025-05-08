"""Tests for the argument parser module."""

from pathlib import Path
from unittest.mock import patch

from anime_librarian.arg_parser import DefaultArgumentParser
from anime_librarian.types import CommandLineArgs


def test_parse_args_default():
    """Test parsing arguments with default values."""
    # Mock sys.argv to simulate command-line arguments
    with patch("sys.argv", ["main.py"]):
        parser = DefaultArgumentParser()
        args = parser.parse_args()

        # Verify the default values
        assert isinstance(args, CommandLineArgs)
        assert args.source is None
        assert args.target is None
        assert args.dry_run is False
        assert args.yes is False
        assert args.verbose is False
        assert args.version is False


def test_parse_args_with_options():
    """Test parsing arguments with various options."""
    # Mock sys.argv to simulate command-line arguments
    with patch(
        "sys.argv",
        [
            "main.py",
            "--source",
            "/test/source",
            "--target",
            "/test/target",
            "--dry-run",
            "--yes",
            "--verbose",
        ],
    ):
        parser = DefaultArgumentParser()
        args = parser.parse_args()

        # Verify the parsed values
        assert isinstance(args, CommandLineArgs)
        assert args.source == Path("/test/source")
        assert args.target == Path("/test/target")
        assert args.dry_run is True
        assert args.yes is True
        assert args.verbose is True
        assert args.version is False


def test_parse_args_with_short_options():
    """Test parsing arguments with short option flags."""
    # Mock sys.argv to simulate command-line arguments
    with patch(
        "sys.argv",
        [
            "main.py",
            "-y",  # Short for --yes
            "-v",  # Short for --verbose
        ],
    ):
        parser = DefaultArgumentParser()
        args = parser.parse_args()

        # Verify the parsed values
        assert isinstance(args, CommandLineArgs)
        assert args.source is None
        assert args.target is None
        assert args.dry_run is False
        assert args.yes is True
        assert args.verbose is True
        assert args.version is False


def test_parse_args_with_version_flag():
    """Test parsing arguments with the version flag."""
    # Mock sys.argv to simulate command-line arguments
    with patch(
        "sys.argv",
        [
            "main.py",
            "--version",
        ],
    ):
        parser = DefaultArgumentParser()
        args = parser.parse_args()

        # Verify the parsed values
        assert isinstance(args, CommandLineArgs)
        assert args.source is None
        assert args.target is None
        assert args.dry_run is False
        assert args.yes is False
        assert args.verbose is False
        assert args.version is True
