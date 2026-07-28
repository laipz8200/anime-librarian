"""Scan, validate, and apply media file moves."""

import ntpath
import shutil
import unicodedata
from collections.abc import Callable, Sequence
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import ClassVar

from .errors import ConfigurationError, InvalidMovePlanError
from .models import FileMove, NamePair

SuggestNames = Callable[[list[str], list[str]], Sequence[NamePair]]


class FileOrganizer:
    """Build safe move plans from externally supplied name suggestions."""

    MEDIA_EXTENSIONS: ClassVar[frozenset[str]] = frozenset(
        {
            ".avi",
            ".flv",
            ".m4v",
            ".mkv",
            ".mov",
            ".mp4",
            ".mpeg",
            ".mpg",
            ".webm",
            ".wmv",
            ".ass",
            ".idx",
            ".srt",
            ".ssa",
            ".sub",
            ".vtt",
        }
    )

    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        suggest_names: SuggestNames,
    ) -> None:
        if not source_path.is_dir():
            message = f"Source directory does not exist: {source_path}"
            raise ConfigurationError(message)
        if not target_path.is_dir():
            message = f"Target directory does not exist: {target_path}"
            raise ConfigurationError(message)
        self.source_path = source_path
        self.target_path = target_path
        self._target_root = target_path.resolve()
        self._target_identity = _path_identity(self._target_root)
        self._source_identities: dict[Path, tuple[int, int]] = {}
        self._conflict_identities: dict[Path, tuple[int, int]] = {}
        self._suggest_names = suggest_names

    def plan_moves(self) -> list[FileMove]:
        """Scan the configured roots and return one fully validated move plan."""
        self._source_identities.clear()
        source_files = sorted(
            (
                path
                for path in self.source_path.iterdir()
                if not path.is_symlink()
                and path.is_file()
                and path.suffix.lower() in self.MEDIA_EXTENSIONS
            ),
            key=lambda path: path.name.casefold(),
        )
        target_directories = sorted(
            (path for path in self.target_path.iterdir() if path.is_dir()),
            key=lambda path: path.name.casefold(),
        )
        if not source_files or not target_directories:
            return []
        self._validate_catalog_names((*source_files, *target_directories))
        self._source_identities = {
            path: _path_identity(path, follow_symlinks=False) for path in source_files
        }

        suggestions = self._suggest_names(
            [path.name for path in source_files],
            [path.name for path in target_directories],
        )
        moves = self._validate_suggestions(source_files, suggestions)
        self._validate_target_root()
        return moves

    def conflicts(self, moves: Sequence[FileMove]) -> list[Path]:
        """Return existing destinations in deterministic order."""
        conflicts = sorted(
            {
                move.target
                for move in moves
                if move.target.exists() or move.target.is_symlink()
            }
        )
        self._conflict_identities = {
            path: _path_identity(path, follow_symlinks=False) for path in conflicts
        }
        return conflicts

    def missing_directories(self, moves: Sequence[FileMove]) -> list[Path]:
        """Return destination directories that need to be created."""
        return sorted(
            {move.target.parent for move in moves if not move.target.parent.exists()}
        )

    def create_directories(self, directories: Sequence[Path]) -> None:
        """Create destination directories and their parents."""
        for directory in directories:
            self._validate_directory_at_creation_time(directory)
            # ponytail: immediate validation closes normal races; portable atomic
            # no-follow directory creation is not available in pathlib.
            directory.mkdir(parents=True, exist_ok=True)
            self._validate_directory_at_creation_time(directory)

    def move(self, move: FileMove, *, overwrite: bool = False) -> None:
        """Apply one validated move."""
        self._validate_destination_at_move_time(move, overwrite=overwrite)
        # ponytail: this narrows normal races; fully atomic cross-filesystem moves
        # would require platform-specific transactions.
        _ = shutil.move(move.source, move.target)

    def _validate_suggestions(
        self,
        source_files: Sequence[Path],
        suggestions: Sequence[NamePair],
    ) -> list[FileMove]:
        sources_by_name = {path.name: path for path in source_files}
        source_keys = {_portable_path_key(path) for path in source_files}
        seen_sources: set[Path] = set()
        seen_targets: set[str] = set()
        moves: list[FileMove] = []

        for suggestion in suggestions:
            source = sources_by_name.get(suggestion.original_name)
            if source is None:
                message = (
                    f"Dify suggested an unknown source file: {suggestion.original_name}"
                )
                raise InvalidMovePlanError(message)
            if (
                not source.is_file()
                or _path_identity(source, follow_symlinks=False)
                != self._source_identities[source]
            ):
                message = f"Source changed while Dify built the plan: {source.name}"
                raise InvalidMovePlanError(message)

            target = self._target_path(suggestion.new_name)
            target_key = _portable_path_key(target)
            if source in seen_sources:
                message = f"Dify suggested more than one move for: {source.name}"
                raise InvalidMovePlanError(message)
            if target_key in seen_targets:
                message = f"Dify suggested duplicate destination: {suggestion.new_name}"
                raise InvalidMovePlanError(message)
            if target_key in source_keys:
                message = (
                    f"Dify suggested another source as the destination: "
                    f"{suggestion.new_name}"
                )
                raise InvalidMovePlanError(message)
            if source.suffix.lower() != target.suffix.lower():
                message = f"Dify changed the file extension for: {source.name}"
                raise InvalidMovePlanError(message)
            if target.exists() and target.is_dir():
                message = f"Dify suggested a directory as a file destination: {target}"
                raise InvalidMovePlanError(message)

            seen_sources.add(source)
            seen_targets.add(target_key)
            moves.append(FileMove(source=source, target=target))

        return moves

    def _target_path(self, suggested_name: str) -> Path:
        normalized = suggested_name.replace("\\", "/")
        posix_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(suggested_name)
        parts = normalized.split("/")
        if (
            not suggested_name
            or posix_path.is_absolute()
            or windows_path.is_absolute()
            or windows_path.drive
            or ntpath.isreserved(normalized)
            or any(part in {"", ".", ".."} for part in parts)
            or _contains_unsafe_character(suggested_name)
        ):
            message = f"Dify suggested an unsafe destination: {suggested_name}"
            raise InvalidMovePlanError(message)

        target = self._target_root.joinpath(*parts)
        if not target.resolve(strict=False).is_relative_to(self._target_root):
            message = (
                f"Dify suggested a destination outside the library: {suggested_name}"
            )
            raise InvalidMovePlanError(message)
        return target

    @staticmethod
    def _validate_catalog_names(paths: Sequence[Path]) -> None:
        for path in paths:
            if _contains_unsafe_character(path.name):
                message = (
                    "Catalog names cannot contain control or formatting "
                    f"characters: {path.name!a}"
                )
                raise ConfigurationError(message)

    def _validate_destination_at_move_time(
        self, move: FileMove, *, overwrite: bool
    ) -> None:
        self._validate_target_root()
        if not move.source.is_file():
            message = f"Source is no longer a file: {move.source}"
            if move.source.is_dir():
                raise IsADirectoryError(message)
            raise FileNotFoundError(message)
        expected_source = self._source_identities.get(move.source)
        if (
            expected_source is not None
            and _path_identity(move.source, follow_symlinks=False) != expected_source
        ):
            message = f"Source changed after the move plan was created: {move.source}"
            raise OSError(message)
        if not move.target.resolve(strict=False).is_relative_to(self._target_root):
            message = f"Destination escaped the target directory: {move.target}"
            raise PermissionError(message)
        if move.target.is_dir():
            message = f"Destination became a directory: {move.target}"
            raise IsADirectoryError(message)
        destination_exists = move.target.exists() or move.target.is_symlink()
        if destination_exists and overwrite:
            expected_target = self._conflict_identities.get(move.target)
            if (
                expected_target is None
                or _path_identity(move.target, follow_symlinks=False) != expected_target
            ):
                message = f"Destination changed after confirmation: {move.target}"
                raise FileExistsError(message)
        elif destination_exists:
            message = f"Destination appeared after confirmation: {move.target}"
            raise FileExistsError(message)

    def _validate_directory_at_creation_time(self, directory: Path) -> None:
        self._validate_target_root()
        if not directory.resolve(strict=False).is_relative_to(self._target_root):
            message = f"Directory escaped the target root: {directory}"
            raise PermissionError(message)

    def _validate_target_root(self) -> None:
        if (
            not self.target_path.is_dir()
            or self.target_path.resolve() != self._target_root
            or _path_identity(self._target_root) != self._target_identity
        ):
            message = "Target directory changed after the move plan was created."
            raise PermissionError(message)


def _portable_path_key(path: Path) -> str:
    """Normalize destination identity across common media-library filesystems."""
    return unicodedata.normalize(
        "NFC", path.resolve(strict=False).as_posix()
    ).casefold()


def _contains_unsafe_character(value: str) -> bool:
    return any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in value
    )


def _path_identity(path: Path, *, follow_symlinks: bool = True) -> tuple[int, int]:
    details = path.stat(follow_symlinks=follow_symlinks)
    return details.st_dev, details.st_ino
