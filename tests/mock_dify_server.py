"""
Mock Dify server for testing the AnimeLibrarian application.

This module provides a FastAPI-based mock server that simulates the Dify API
for testing purposes.
"""

import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel


class WorkflowInputs(BaseModel):
    """Model for workflow inputs."""

    files: str
    directories: str


class WorkflowRequest(BaseModel):
    """Model for workflow execution request."""

    inputs: WorkflowInputs
    user: str
    response_mode: str


class MockDifyServer:
    """Mock Dify server for testing."""

    def __init__(self) -> None:
        """Initialize the mock server."""
        self.app = FastAPI()
        self.setup_routes()
        self.request_count = 0
        self.should_fail = False
        self.failure_mode: str | None = None
        self.custom_response: dict[str, Any] | None = None
        self.processing_delay = 0.0

    def setup_routes(self) -> None:
        """Set up the API routes."""

        @self.app.post("/v1/workflows/run")
        async def _run_workflow(  # pyright: ignore[reportUnusedFunction]
            request: WorkflowRequest,
            authorization: str = Header(...),
        ) -> dict[str, Any]:
            """
            Mock endpoint for workflow execution.

            This endpoint simulates the Dify workflow API and generates
            intelligent renaming suggestions based on file names and target directories.
            """
            self.request_count += 1

            # Check authorization
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Invalid authorization")

            # Handle failure scenarios for testing
            if self.should_fail:
                if self.failure_mode == "invalid_json":
                    return {
                        "data": {
                            "outputs": {
                                "text": "This is not valid JSON {broken: syntax"
                            }
                        }
                    }
                elif self.failure_mode == "missing_field":
                    return {"data": {}}
                elif self.failure_mode == "server_error":
                    raise HTTPException(status_code=500, detail="Internal server error")
                elif self.failure_mode == "timeout":
                    import asyncio

                    await asyncio.sleep(10)  # Simulate timeout
                    return {}

            # Return custom response if set
            if self.custom_response:
                return self.custom_response

            # Parse input files and directories
            files = request.inputs.files.strip().split("\n")
            directories = request.inputs.directories.strip().split("\n")

            # Generate intelligent renaming suggestions
            result = self._generate_rename_suggestions(files, directories)

            # Return response in the expected format
            return {"data": {"outputs": {"text": json.dumps({"result": result})}}}

    def _generate_rename_suggestions(
        self, files: list[str], directories: list[str]
    ) -> list[dict[str, str]]:
        """
        Generate intelligent renaming suggestions based on file names and directories.

        This simulates the AI logic for matching files to appropriate directories.
        """
        suggestions: list[dict[str, str]] = []

        for file in files:
            if not file:
                continue

            # Extract potential anime/series name from file
            file_lower = file.lower()
            target_dir = None
            new_name = file

            # Try to match with existing directories
            for directory in directories:
                if not directory:
                    continue

                dir_lower = directory.lower()

                # Simple matching logic based on common patterns
                # Check if directory name is contained in file name
                dir_parts = re.findall(r"\w+", dir_lower)
                if dir_parts and any(
                    part in file_lower for part in dir_parts if len(part) > 2
                ):
                    target_dir = directory
                    # Extract episode number if present
                    episode_match = re.search(r"(\d+)", file)
                    if episode_match:
                        episode_num = episode_match.group(1)
                        # Get file extension
                        file_path = Path(file)
                        extension = file_path.suffix
                        # Create clean name
                        new_name = (
                            f"{directory}/Episode_{episode_num.zfill(2)}{extension}"
                        )
                    else:
                        new_name = f"{directory}/{file}"
                    break

            # If no match found, suggest organizing by file type
            if not target_dir:
                file_path = Path(file)
                extension = file_path.suffix.lower()
                if extension in {".mkv", ".mp4", ".avi"}:
                    # Try to extract series name from file
                    series_match = re.match(r"^\[.*?\]\s*(.+?)\s*-?\s*\d+", file)
                    if series_match:
                        series_name = series_match.group(1).strip()
                        # Check if a similar directory exists
                        for directory in directories:
                            if series_name.lower() in directory.lower():
                                target_dir = directory
                                new_name = f"{directory}/{file}"
                                break

            # Only add suggestion if we found a target
            if target_dir or "/" in new_name:
                suggestions.append({"original_name": file, "new_name": new_name})

        return suggestions

    def reset(self) -> None:
        """Reset the server state for testing."""
        self.request_count = 0
        self.should_fail = False
        self.failure_mode = None
        self.custom_response = None
        self.processing_delay = 0.0

    def set_failure_mode(self, mode: str) -> None:
        """
        Set the server to fail in a specific way.

        Args:
            mode: The failure mode ('invalid_json', 'missing_field',
                'server_error', 'timeout')
        """
        self.should_fail = True
        self.failure_mode = mode

    def set_custom_response(self, response: dict[str, Any]) -> None:
        """
        Set a custom response for the next request.

        Args:
            response: The custom response dictionary
        """
        self.custom_response = response


# Create global mock server instance
mock_server = MockDifyServer()
app = mock_server.app
