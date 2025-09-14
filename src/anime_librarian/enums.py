"""Enumerations for the AnimeLibrarian application."""

from enum import Enum, auto


class ProcessingStatus(Enum):
    """Status of file processing operations."""

    SCANNING = auto()
    """Scanning files and directories."""

    ANALYZING = auto()
    """Analyzing file content or names."""

    RENAMING = auto()
    """Performing rename operations."""

    MOVING = auto()
    """Moving files to target locations."""

    ORGANIZING = auto()
    """Organizing files into directories."""

    VALIDATING = auto()
    """Validating operations or results."""

    COMPLETED = auto()
    """Operation completed successfully."""

    FAILED = auto()
    """Operation failed."""

    SKIPPED = auto()
    """Operation was skipped."""


class FileOperation(Enum):
    """Types of file operations."""

    RENAME = "rename"
    """File rename operation."""

    MOVE = "move"
    """File move operation."""

    COPY = "copy"
    """File copy operation."""

    DELETE = "delete"
    """File delete operation."""

    CREATE_DIR = "create_dir"
    """Directory creation operation."""


class PreviewType(Enum):
    """Types of preview displays."""

    RENAME_PREVIEW = auto()
    """Preview of rename operations."""

    MOVE_PREVIEW = auto()
    """Preview of move operations."""

    CONFLICT_PREVIEW = auto()
    """Preview of conflicting operations."""
