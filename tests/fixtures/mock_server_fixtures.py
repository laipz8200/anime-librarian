"""
Test fixtures for mock Dify server testing.

This module provides fixtures and test data for testing the AnimeLibrarian
with the mock Dify server.
"""

import random
import sys
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
import uvicorn
from httpx import Client

# Add tests directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mock_dify_server import mock_server


@pytest.fixture
def mock_dify_url() -> str:
    """Return the URL for the mock Dify server."""
    return "http://localhost:8765"


@pytest.fixture
def mock_api_key() -> str:
    """Return a test API key."""
    return "test-api-key-12345"


@contextmanager
def run_mock_server(port: int | None = None) -> Generator[str]:
    """
    Context manager to run the mock Dify server in a background thread.

    Args:
        port: The port to run the server on (defaults to random port)

    Yields:
        The server URL
    """
    # Use a random port if not specified to avoid conflicts
    if port is None:
        port = random.randint(9000, 9999)
    # Reset server state
    mock_server.reset()

    # Create server configuration
    config = uvicorn.Config(
        app=mock_server.app,
        host="127.0.0.1",
        port=port,
        log_level="error",  # Suppress logs during testing
    )
    server = uvicorn.Server(config)

    # Run server in background thread
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to start and check if it's really running
    import socket
    import time

    max_retries = 10
    for _ in range(max_retries):
        time.sleep(0.1)
        # Check if port is actually open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        if result == 0:
            break
    else:
        # If port is still not open, try a different port
        port = random.randint(10000, 10999)
        config = uvicorn.Config(
            app=mock_server.app,
            host="127.0.0.1",
            port=port,
            log_level="error",
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        time.sleep(0.5)

    try:
        yield f"http://localhost:{port}"
    finally:
        # Server will stop when thread terminates
        pass


@pytest.fixture
def running_mock_server() -> Generator[str]:
    """Fixture that provides a running mock Dify server."""
    with run_mock_server() as url:
        yield url


@pytest.fixture
def sample_files() -> list[str]:
    """Return sample file names for testing."""
    return [
        "[SubsPlease] Frieren - 01 (1080p) [4A89B8A2].mkv",
        "[SubsPlease] Frieren - 02 (1080p) [5B90C9B3].mkv",
        "[Erai-raws] Spy x Family - 01 [1080p][Multiple Subtitle].mkv",
        "[Erai-raws] Spy x Family - 02 [1080p][Multiple Subtitle].mkv",
        "Demon.Slayer.S01E01.1080p.WEB-DL.AAC2.0.H.264.mkv",
        "Demon.Slayer.S01E02.1080p.WEB-DL.AAC2.0.H.264.mkv",
        "subtitles_en.srt",
        "subtitles_jp.ass",
    ]


@pytest.fixture
def sample_directories() -> list[str]:
    """Return sample directory names for testing."""
    return [
        "Frieren - Beyond Journey's End",
        "Spy x Family",
        "Demon Slayer",
        "Attack on Titan",
        "One Piece",
    ]


@pytest.fixture
def expected_rename_pairs() -> list[tuple[str, str]]:
    """Return expected rename pairs for the sample files."""
    return [
        (
            "[SubsPlease] Frieren - 01 (1080p) [4A89B8A2].mkv",
            "Frieren - Beyond Journey's End/Episode_01.mkv",
        ),
        (
            "[SubsPlease] Frieren - 02 (1080p) [5B90C9B3].mkv",
            "Frieren - Beyond Journey's End/Episode_02.mkv",
        ),
        (
            "[Erai-raws] Spy x Family - 01 [1080p][Multiple Subtitle].mkv",
            "Spy x Family/Episode_01.mkv",
        ),
        (
            "[Erai-raws] Spy x Family - 02 [1080p][Multiple Subtitle].mkv",
            "Spy x Family/Episode_02.mkv",
        ),
        (
            "Demon.Slayer.S01E01.1080p.WEB-DL.AAC2.0.H.264.mkv",
            "Demon Slayer/Episode_01.mkv",
        ),
        (
            "Demon.Slayer.S01E02.1080p.WEB-DL.AAC2.0.H.264.mkv",
            "Demon Slayer/Episode_02.mkv",
        ),
    ]


@pytest.fixture
def error_response_invalid_json() -> dict[str, Any]:
    """Return a response with invalid JSON in the text field."""
    return {"data": {"outputs": {"text": "This is not valid JSON {broken: syntax"}}}


@pytest.fixture
def error_response_missing_field() -> dict[str, Any]:
    """Return a response missing required fields."""
    return {"data": {}}


@pytest.fixture
def custom_response_single_file() -> dict[str, Any]:
    """Return a custom response for a single file rename."""
    return {
        "data": {
            "outputs": {
                "text": (
                    '{"result": [{"original_name": "test.mkv", '
                    '"new_name": "Target/renamed.mkv"}]}'
                )
            }
        }
    }


@pytest.fixture
def custom_response_multiple_files() -> dict[str, Any]:
    """Return a custom response for multiple file renames."""
    return {
        "data": {
            "outputs": {
                "text": (
                    '{"result": ['
                    '{"original_name": "file1.mkv", "new_name": "Dir1/new1.mkv"},'
                    '{"original_name": "file2.mp4", "new_name": "Dir2/new2.mp4"},'
                    '{"original_name": "file3.avi", "new_name": "Dir3/new3.avi"}'
                    "]}"
                )
            }
        }
    }


@pytest.fixture
def test_http_client(running_mock_server: str) -> Client:
    """Return a configured HTTP client for testing."""
    return Client(base_url=running_mock_server)
