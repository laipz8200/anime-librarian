"""
File renaming module for the AnimeLibrarian application.

This module provides the FileRenamer class that encapsulates the logic for
renaming and organizing video files using AI suggestions.
"""

import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import json_repair

from . import config
from . import console as console_module
from .errors import raise_parse_error
from .http_client import HttpxClient
from .models import AIResponse, ApiResponse
from .types import HttpClient


class FileRenamer:
    """
    Class for renaming and organizing video files using AI suggestions.

    This class encapsulates the logic for:
    1. Getting file name suggestions from an AI service
    2. Mapping source files to target files
    3. Handling the file renaming and organization process
    """

    # File extension constants
    VIDEO_EXTENSIONS: ClassVar[set[str]] = {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
    }
    SUBTITLE_EXTENSIONS: ClassVar[set[str]] = {".srt", ".ass", ".ssa", ".sub", ".vtt"}
    MEDIA_EXTENSIONS: ClassVar[set[str]] = VIDEO_EXTENSIONS.union(SUBTITLE_EXTENSIONS)

    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        http_client: HttpClient | None = None,
        api_endpoint: str = config.DIFY_WORKFLOW_RUN_ENDPOINT,
        api_key: str = config.DIFY_API_KEY,
        api_timeout: int = config.API_TIMEOUT,
    ):
        """
        Initialize the FileRenamer.

        Args:
            source_path: Path to the directory containing source files
            target_path: Path to the directory containing target directories
            http_client: Optional HTTP client to use for AI requests
            api_endpoint: API endpoint for the AI service
            api_key: API key for the AI service
            api_timeout: Timeout for API requests in seconds
        """
        self.source_path = source_path
        self.target_path = target_path
        self.http_client = http_client or HttpxClient()
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_timeout = api_timeout

    def _get_name_pairs_from_ai(
        self, source_files_list: list[str], target_files_list: list[str]
    ) -> list[tuple[str, str]]:
        """
        Retrieve name pairs for file renaming from an AI service.

        This method sends a request to an AI service with the list of source files
        and target directories, and receives suggested new names for the files.

        Args:
            source_files_list: List of source file names
            target_files_list: List of target directory names

        Returns:
            A list of tuples, each containing (original_name, new_name) pairs

        Raises:
            InvalidResponseError: If the response format is invalid
            AIParseError: If parsing the AI response fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": {
                "files": "\n".join(str(f) for f in source_files_list),
                "directories": "\n".join(str(f) for f in target_files_list),
            },
            "user": config.USER_NAME,
            "response_mode": "blocking",
        }

        # Send POST request to the AI service
        console_module.console.debug("Sending request to AI service")
        console_module.console.debug(f"Payload: {payload}")
        resp = self.http_client.post(
            self.api_endpoint, headers=headers, json=payload, timeout=self.api_timeout
        )

        # Log raw response for debugging
        console_module.console.debug("Received response from AI service")
        status = resp.status_code if hasattr(resp, "status_code") else "OK"
        console_module.console.debug(f"Status: {status}")
        console_module.console.debug(f"Response data: {resp}")

        # Validate response structure using Pydantic model
        try:
            api_response = ApiResponse.model_validate(resp)
            response_text = api_response.response_text
            console_module.console.debug(f"Extracted response text: {response_text}")
        except Exception as exc:
            console_module.console.exception(
                "Invalid response structure from AI service"
            )
            raise_parse_error(exc)
        # Parse the JSON response
        try:
            # Repair the JSON response if needed
            json_response = json_repair.repair_json(response_text, return_objects=True)

            # Parse the response using Pydantic model
            ai_response = AIResponse.model_validate(json_response)

            # Convert the Pydantic model to a list of tuples
            name_pairs = []
            for pair in ai_response.result:
                name_pairs.append((pair.original_name, pair.new_name))

        except Exception as exc:
            # Log the error and re-raise with a more specific error type
            console_module.console.exception("Error parsing AI response")
            # This will always raise, so mypy knows we don't need an else clause
            raise_parse_error(exc)
        # Return the name pairs in the try block to satisfy ruff TRY300
        # and use else to make it clear this is the success path
        else:
            return name_pairs

    def get_file_pairs(self) -> Sequence[tuple[Path, Path]]:
        """
        Get pairs of source and target file paths.

        Returns:
            A sequence of tuples containing (source_file_path, target_file_path)
        """
        # Get list of files and directories
        # Filter for video and subtitle files only
        source_files = [
            f
            for f in self.source_path.glob("*")
            if f.is_file() and f.suffix.lower() in self.MEDIA_EXTENSIONS
        ]

        # Filter for directories only
        target_dirs = [d for d in self.target_path.glob("*") if d.is_dir()]

        # Check if we have files to process
        if not source_files:
            console_module.console.info(f"No media files found in {self.source_path}")
            if console_module.console.verbose:
                console_module.console.debug(f"Searched path: {self.source_path}")
                exts = self.VIDEO_EXTENSIONS | self.SUBTITLE_EXTENSIONS
                console_module.console.debug(f"Looking for extensions: {exts}")
            return []

        # Check if we have target directories
        if not target_dirs:
            console_module.console.info(
                f"No target directories found in {self.target_path}"
            )
            if console_module.console.verbose:
                console_module.console.debug(f"Searched path: {self.target_path}")
                console_module.console.debug(
                    "Expected to find subdirectories for organizing files"
                )
            return []

        # Get just the file/directory names
        source_file_names = [f.name for f in source_files]
        target_dir_names = [d.name for d in target_dirs]

        # Get name pairs from AI
        name_pairs = self._get_name_pairs_from_ai(
            source_files_list=source_file_names,
            target_files_list=target_dir_names,
        )

        # Convert string pairs to full Path objects
        full_path_pairs = []
        for source_name, target_name in name_pairs:
            source_file = self.source_path / source_name

            # Handle target paths that might include subdirectories
            if "/" in target_name:
                # If target includes a directory structure
                target_dir_name, file_name = target_name.split("/", 1)
                target_dir = self.target_path / target_dir_name
                target_file = target_dir / file_name
            else:
                target_file = self.target_path / target_name

            full_path_pairs.append((source_file, target_file))

        return full_path_pairs

    def check_for_conflicts(
        self, file_pairs: Sequence[tuple[Path, Path]]
    ) -> list[Path]:
        """
        Check for potential conflicts in the file renaming operation.

        Args:
            file_pairs: Sequence of (source, target) file path pairs

        Returns:
            List of target paths that already exist
        """
        conflicts = []
        for _, target_path in file_pairs:
            if target_path.exists():
                conflicts.append(target_path)
        return conflicts

    def find_missing_directories(
        self, file_pairs: Sequence[tuple[Path, Path]]
    ) -> list[Path]:
        """
        Find directories that need to be created for the renaming operation.

        Args:
            file_pairs: Sequence of (source, target) file path pairs

        Returns:
            List of directories that need to be created
        """
        missing_dirs = set()
        for _, target_file in file_pairs:
            target_dir = target_file.parent
            if not target_dir.exists():
                missing_dirs.add(target_dir)
        return list(missing_dirs)

    def create_directories(self, directories: list[Path]) -> bool:
        """
        Create the specified directories.

        Args:
            directories: List of directories to create

        Returns:
            True if all directories were created successfully, False otherwise
        """
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                console_module.console.debug(
                    f"Successfully created directory: {directory}"
                )
            except Exception:
                console_module.console.exception(
                    f"Error creating directory {directory}"
                )
                return False
        return True

    def rename_files(
        self, file_pairs: Sequence[tuple[Path, Path]]
    ) -> list[tuple[Path, Path, str]]:
        """
        Rename files according to the specified pairs.

        Args:
            file_pairs: Sequence of (source, target) file path pairs

        Returns:
            List of (source, target, error) tuples for failed operations
        """
        errors = []
        for source_file, target_file in file_pairs:
            try:
                if console_module.console.verbose:
                    console_module.console.debug(f"Moving file: {source_file}")
                    console_module.console.debug(f"Target location: {target_file}")
                console_module.console.print_file_operation(
                    "Moving", str(source_file), str(target_file), "processing"
                )
                shutil.move(str(source_file), str(target_file))
            except Exception as e:
                error_msg = str(e)
                # Don't include the exception object in the log message
                # This satisfies TRY401 (verbose-log-message)
                console_module.console.exception(f"Error moving {source_file}")
                errors.append((source_file, target_file, error_msg))
        return errors
