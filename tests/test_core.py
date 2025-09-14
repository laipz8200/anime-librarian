"""Tests for the AnimeLibrarian class."""

from pathlib import Path
from typing import TYPE_CHECKING

from anime_librarian.rich_core import RichAnimeLibrarian as AnimeLibrarian
from anime_librarian.types import CommandLineArgs

if TYPE_CHECKING:
    from anime_librarian.types import Console, HttpClient


class MockArgumentParser:
    """Mock implementation of ArgumentParser for testing."""

    def __init__(
        self,
        source: Path | None = None,
        target: Path | None = None,
        dry_run: bool = False,
        yes: bool = False,
        version: bool = False,
    ) -> None:
        """Initialize with predefined arguments."""
        self.source = source
        self.target = target
        self.dry_run = dry_run
        self.yes = yes
        self.version = version

    def parse_args(self) -> CommandLineArgs:
        """Return CommandLineArgs with the predefined arguments."""
        return CommandLineArgs(
            source=self.source,
            target=self.target,
            dry_run=self.dry_run,
            yes=self.yes,
            version=self.version,
        )


class MockConfigProvider:
    """Mock implementation of ConfigProvider for testing."""

    def __init__(
        self, source_path: Path | None = None, target_path: Path | None = None
    ) -> None:
        """Initialize with predefined paths."""
        self.source_path = source_path or Path("/mock/source")
        self.target_path = target_path or Path("/mock/target")

    def get_source_path(self) -> Path:
        """Return the predefined source path."""
        return self.source_path

    def get_target_path(self) -> Path:
        """Return the predefined target path."""
        return self.target_path


class MockFileRenamer:
    """Mock implementation of FileRenamer for testing."""

    def __init__(
        self,
        file_pairs: list[tuple[Path, Path]] | None = None,
        conflicts: list[Path] | None = None,
        missing_dirs: list[Path] | None = None,
        errors: list[tuple[Path, Path]] | None = None,
    ) -> None:
        """Initialize with predefined responses."""
        self.file_pairs = file_pairs or []
        self.conflicts = conflicts or []
        self.missing_dirs = missing_dirs or []
        self.errors = errors or []
        self.source_path = Path("/mock/source")
        self.target_path = Path("/mock/target")

    def get_file_pairs(self) -> list[tuple[Path, Path]]:
        """Return the predefined file pairs."""
        return self.file_pairs

    def check_for_conflicts(self, _: list[tuple[Path, Path]]) -> list[Path]:
        """Return the predefined conflicts."""
        return self.conflicts

    def find_missing_directories(self, _: list[tuple[Path, Path]]) -> list[Path]:
        """Return the predefined missing directories."""
        return self.missing_dirs

    def create_directories(self, _: list[Path]) -> bool:
        """Return True to indicate success."""
        return True

    def rename_files(self, _: list[tuple[Path, Path]]) -> list[tuple[Path, Path]]:
        """Return the predefined errors."""
        return self.errors


# Removed mock_file_renamer_factory fixture (uses unittest.mock)


# Removed mock_set_verbose_mode fixture (verbose feature removed)


# Removed test_anime_librarian_basic_functionality (uses unittest.mock)


# Removed test_anime_librarian_dry_run (uses unittest.mock)


# Test for verbose mode removed (feature deleted)


# Removed test_anime_librarian_version_flag (uses unittest.mock)


def test_anime_librarian_no_files():
    """Test the application when no files need to be renamed."""
    mock_renamer = MockFileRenamer(file_pairs=[])

    def mock_factory(
        source: Path,
        target: Path,
        http_client: "HttpClient | None" = None,
        console: "Console | None" = None,
    ) -> MockFileRenamer:
        return mock_renamer

    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(yes=True),
        config_provider=MockConfigProvider(),
        file_renamer_factory=mock_factory,  # type: ignore[arg-type]
    )

    # Run the application
    result = app.run()

    # Should exit with 0 when no files to rename
    assert result == 0


def test_anime_librarian_with_conflicts_yes_mode():
    """Test handling of conflicts in yes mode (auto-confirm)."""
    # Create mock file pairs with conflicts
    source_path = Path("/mock/source")
    target_path = Path("/mock/target")
    file_pairs = [
        (source_path / "file1.mp4", target_path / "Anime1" / "renamed_file1.mp4"),
    ]

    mock_renamer = MockFileRenamer(
        file_pairs=file_pairs,
        conflicts=[target_path / "Anime1" / "renamed_file1.mp4"],
        missing_dirs=[],
        errors=[],
    )

    def mock_factory(
        source: Path,
        target: Path,
        http_client: "HttpClient | None" = None,
        console: "Console | None" = None,
    ) -> MockFileRenamer:
        return mock_renamer

    # Create the application with yes flag
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(yes=True),
        config_provider=MockConfigProvider(
            source_path=source_path, target_path=target_path
        ),
        file_renamer_factory=mock_factory,  # type: ignore[arg-type]
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0


def test_anime_librarian_with_missing_directories():
    """Test handling of missing directories."""
    # Create mock file pairs with missing directories
    source_path = Path("/mock/source")
    target_path = Path("/mock/target")
    file_pairs = [
        (source_path / "file1.mp4", target_path / "NewDir" / "file1.mp4"),
    ]
    missing_dirs = [target_path / "NewDir"]

    mock_renamer = MockFileRenamer(
        file_pairs=file_pairs, conflicts=[], missing_dirs=missing_dirs, errors=[]
    )

    def mock_factory(
        source: Path,
        target: Path,
        http_client: "HttpClient | None" = None,
        console: "Console | None" = None,
    ) -> MockFileRenamer:
        return mock_renamer

    # Create the application with yes flag
    app = AnimeLibrarian(
        arg_parser=MockArgumentParser(yes=True),
        config_provider=MockConfigProvider(
            source_path=source_path, target_path=target_path
        ),
        file_renamer_factory=mock_factory,  # type: ignore[arg-type]
    )

    # Run the application
    result = app.run()

    # Verify the result
    assert result == 0
