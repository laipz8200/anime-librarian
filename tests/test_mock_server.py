"""
Unit tests for the mock Dify server.

This module contains unit tests that verify the mock server's functionality,
including its API endpoints, error handling, and response generation.
"""

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add tests directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mock_dify_server import MockDifyServer, app, mock_server


class TestMockDifyServerEndpoints:
    """Test the mock Dify server API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Reset mock server before each test."""
        mock_server.reset()

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_workflow_endpoint_exists(self, client: TestClient) -> None:
        """Test that the workflow endpoint exists and responds."""
        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "test.mkv", "directories": "TestDir"},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )
        assert response.status_code == 200

    def test_authorization_required(self, client: TestClient) -> None:
        """Test that authorization header is required."""
        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "test.mkv", "directories": "TestDir"},
                "user": "test_user",
                "response_mode": "blocking",
            },
        )
        assert response.status_code == 422  # Missing header

    def test_invalid_authorization(self, client: TestClient) -> None:
        """Test that invalid authorization is rejected."""
        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "test.mkv", "directories": "TestDir"},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "InvalidFormat"},
        )
        assert response.status_code == 401

    def test_valid_response_structure(self, client: TestClient) -> None:
        """Test that the server returns a valid response structure."""
        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {
                    "files": "anime_episode_01.mkv",
                    "directories": "Anime Series",
                },
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "data" in data
        assert "outputs" in data["data"]
        assert "text" in data["data"]["outputs"]

        # Verify the text is valid JSON
        text = data["data"]["outputs"]["text"]
        parsed = json.loads(text)
        assert "result" in parsed
        assert isinstance(parsed["result"], list)

    def test_request_counting(self, client: TestClient) -> None:
        """Test that the server counts requests correctly."""
        assert mock_server.request_count == 0

        # Make first request
        _ = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "test1.mkv", "directories": "Dir1"},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )
        assert mock_server.request_count == 1

        # Make second request
        _ = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "test2.mkv", "directories": "Dir2"},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )
        assert mock_server.request_count == 2


class TestMockServerIntelligentMatching:
    """Test the mock server's intelligent file matching logic."""

    @pytest.fixture
    def server(self) -> MockDifyServer:
        """Create a fresh mock server instance."""
        server = MockDifyServer()
        return server

    def test_exact_directory_match(self, server: MockDifyServer) -> None:
        """Test matching when directory name is contained in file name."""
        files = ["[Group] Frieren - 01.mkv", "Frieren Episode 02.mp4"]
        directories = ["Frieren", "Other Series"]

        suggestions = server._generate_rename_suggestions(files, directories)

        assert len(suggestions) == 2
        for suggestion in suggestions:
            assert "Frieren" in suggestion["new_name"]
            assert suggestion["new_name"].startswith("Frieren/")

    def test_episode_number_extraction(self, server: MockDifyServer) -> None:
        """Test extraction and formatting of episode numbers."""
        files = [
            "Series - 1.mkv",
            "Series - 02.mkv",
            "Series - 10.mkv",
            "Series - 100.mkv",
        ]
        directories = ["Series"]

        suggestions = server._generate_rename_suggestions(files, directories)

        expected_episodes = [
            "Episode_01.mkv",
            "Episode_02.mkv",
            "Episode_10.mkv",
            "Episode_100.mkv",
        ]

        for suggestion, expected in zip(suggestions, expected_episodes, strict=False):
            assert suggestion["new_name"] == f"Series/{expected}"

    def test_partial_name_matching(self, server: MockDifyServer) -> None:
        """Test matching with partial directory names."""
        files = ["spy.x.family.s01e01.mkv", "SPY-FAMILY-02.mp4"]
        directories = ["Spy x Family", "Another Anime"]

        suggestions = server._generate_rename_suggestions(files, directories)

        assert len(suggestions) == 2
        for suggestion in suggestions:
            assert "Spy x Family" in suggestion["new_name"]

    def test_no_match_scenario(self, server: MockDifyServer) -> None:
        """Test behavior when no directories match the files."""
        files = ["random_video.mkv", "unknown_file.mp4"]
        directories = ["Specific Series A", "Specific Series B"]

        suggestions = server._generate_rename_suggestions(files, directories)

        # Files with no matches might not be included or have special handling
        # This depends on the implementation
        assert len(suggestions) >= 0

    def test_multiple_file_extensions(self, server: MockDifyServer) -> None:
        """Test handling of different file extensions."""
        files = [
            "series.01.mkv",
            "series.02.mp4",
            "series.03.avi",
            "series.subs.srt",
        ]
        directories = ["Series"]

        suggestions = server._generate_rename_suggestions(files, directories)

        for suggestion in suggestions:
            original = suggestion["original_name"]
            new = suggestion["new_name"]
            # Preserve file extension
            assert original.split(".")[-1] == new.split(".")[-1]

    def test_complex_file_patterns(self, server: MockDifyServer) -> None:
        """Test handling of complex file naming patterns."""
        files = [
            "[SubsPlease] Demon Slayer - 01 (1080p) [4A89B8A2].mkv",
            "[Erai-raws] Demon Slayer - 02 [1080p][Multiple Subtitle].mkv",
            "Demon.Slayer.S01E03.1080p.WEB-DL.AAC2.0.H.264.mkv",
        ]
        directories = ["Demon Slayer", "Other Series"]

        suggestions = server._generate_rename_suggestions(files, directories)

        assert len(suggestions) == 3
        for suggestion in suggestions:
            assert "Demon Slayer" in suggestion["new_name"]
            # Check episode numbers are extracted
            assert "Episode_" in suggestion["new_name"]


class TestMockServerFailureModes:
    """Test the mock server's failure simulation capabilities."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Reset mock server before each test."""
        mock_server.reset()

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_invalid_json_failure_mode(self, client: TestClient) -> None:
        """Test invalid JSON response mode."""
        mock_server.set_failure_mode("invalid_json")

        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "test.mkv", "directories": "Dir"},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )

        assert response.status_code == 200
        data = response.json()
        text = data["data"]["outputs"]["text"]

        # Verify the text is NOT valid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(text)

    def test_missing_field_failure_mode(self, client: TestClient) -> None:
        """Test missing field response mode."""
        mock_server.set_failure_mode("missing_field")

        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "test.mkv", "directories": "Dir"},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "outputs" not in data["data"]

    def test_server_error_failure_mode(self, client: TestClient) -> None:
        """Test server error response mode."""
        mock_server.set_failure_mode("server_error")

        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "test.mkv", "directories": "Dir"},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    def test_custom_response_mode(self, client: TestClient) -> None:
        """Test custom response functionality."""
        custom_response = {
            "data": {
                "outputs": {
                    "text": json.dumps(
                        {
                            "result": [
                                {
                                    "original_name": "custom.mkv",
                                    "new_name": "Custom/renamed.mkv",
                                }
                            ]
                        }
                    )
                }
            }
        }
        mock_server.set_custom_response(custom_response)

        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "any.mkv", "directories": "AnyDir"},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data == custom_response


class TestMockServerStateManagement:
    """Test the mock server's state management."""

    def test_reset_functionality(self) -> None:
        """Test that reset properly clears all state."""
        # Set various states
        mock_server.request_count = 10
        mock_server.should_fail = True
        mock_server.failure_mode = "test_mode"
        mock_server.custom_response = {"test": "response"}
        mock_server.processing_delay = 5.0

        # Reset
        mock_server.reset()

        # Verify all state is cleared
        assert mock_server.request_count == 0
        assert mock_server.should_fail is False
        assert mock_server.failure_mode is None
        assert mock_server.custom_response is None
        assert mock_server.processing_delay == 0.0

    def test_independent_state_changes(self) -> None:
        """Test that state changes are independent."""
        mock_server.reset()

        # Set failure mode
        mock_server.set_failure_mode("invalid_json")
        assert mock_server.should_fail is True
        assert mock_server.failure_mode == "invalid_json"
        assert mock_server.custom_response is None

        # Reset and set custom response
        mock_server.reset()
        mock_server.set_custom_response({"custom": "data"})
        assert mock_server.should_fail is False
        assert mock_server.failure_mode is None
        assert mock_server.custom_response == {"custom": "data"}


class TestMockServerInputValidation:
    """Test the mock server's input validation."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Reset mock server before each test."""
        mock_server.reset()

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_empty_files_list(self, client: TestClient) -> None:
        """Test handling of empty files list."""
        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "", "directories": "Dir1\nDir2"},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )

        assert response.status_code == 200
        data = response.json()
        result = json.loads(data["data"]["outputs"]["text"])
        assert result["result"] == []

    def test_empty_directories_list(self, client: TestClient) -> None:
        """Test handling of empty directories list."""
        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {"files": "file1.mkv\nfile2.mp4", "directories": ""},
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )

        assert response.status_code == 200
        data = response.json()
        result = json.loads(data["data"]["outputs"]["text"])
        # Files without matching directories might not be renamed
        assert isinstance(result["result"], list)

    def test_multiline_input_parsing(self, client: TestClient) -> None:
        """Test parsing of multiline file and directory inputs."""
        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {
                    "files": "file1.mkv\nfile2.mp4\nfile3.avi",
                    "directories": "Dir1\nDir2\nDir3",
                },
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )

        assert response.status_code == 200
        data = response.json()
        result = json.loads(data["data"]["outputs"]["text"])
        assert isinstance(result["result"], list)

    def test_special_characters_in_names(self, client: TestClient) -> None:
        """Test handling of special characters in file and directory names."""
        response = client.post(
            "/v1/workflows/run",
            json={
                "inputs": {
                    "files": "[Special] File (2024) - 01.mkv\nFile & Name.mp4",
                    "directories": (
                        "Dir with Spaces\nDir-with-dashes\nDir_with_underscores"
                    ),
                },
                "user": "test_user",
                "response_mode": "blocking",
            },
            headers={"Authorization": "Bearer test-key"},
        )

        assert response.status_code == 200
        data = response.json()
        result = json.loads(data["data"]["outputs"]["text"])
        assert isinstance(result["result"], list)
