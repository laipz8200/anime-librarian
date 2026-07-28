import json
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from anime_librarian.config import Settings
from anime_librarian.dify import DifyClient
from anime_librarian.errors import AIResponseError, ConfigurationError, DifyError
from anime_librarian.models import NamePair


def settings(api_key: str = "secret") -> Settings:
    return Settings(
        source_path=Path("/source"),
        target_path=Path("/target"),
        api_endpoint="https://dify.test/v1/workflows/run",
        api_key=api_key,
        api_timeout=12,
        user_name="test-user",
    )


def test_suggest_names_sends_workflow_request_and_parses_result() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://dify.test/v1/workflows/run"
        assert request.headers["Authorization"] == "Bearer secret"
        assert json.loads(request.content) == {
            "inputs": {
                "files": "episode-01.mkv\nepisode-01.srt",
                "directories": "Frieren\nDungeon Meshi",
            },
            "response_mode": "blocking",
            "user": "test-user",
        }
        return httpx.Response(
            200,
            json={
                "data": {
                    "outputs": {
                        "text": json.dumps(
                            {
                                "result": [
                                    {
                                        "original_name": "episode-01.mkv",
                                        "new_name": "Frieren/Episode 01.mkv",
                                    }
                                ]
                            }
                        )
                    }
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        result = DifyClient(settings(), http).suggest_names(
            ["episode-01.mkv", "episode-01.srt"],
            ["Frieren", "Dungeon Meshi"],
        )

    assert result == [
        NamePair(
            original_name="episode-01.mkv",
            new_name="Frieren/Episode 01.mkv",
        )
    ]


def test_suggest_names_repairs_fenced_malformed_json() -> None:
    response_text = """```json
    {'result': [
        {'original_name': 'episode.mkv', 'new_name': 'Show/Episode 01.mkv',},
    ],}
    ```"""

    with httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={"data": {"outputs": {"text": response_text}}},
            )
        )
    ) as http:
        result = DifyClient(settings(), http).suggest_names(["episode.mkv"], ["Show"])

    assert result == [
        NamePair(
            original_name="episode.mkv",
            new_name="Show/Episode 01.mkv",
        )
    ]


def test_suggest_names_rejects_missing_response_text() -> None:
    with (
        httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"data": {"outputs": {}}})
            )
        ) as http,
        pytest.raises(AIResponseError),
    ):
        DifyClient(settings(), http).suggest_names(["episode.mkv"], ["Show"])


def test_suggest_names_maps_http_error_to_dify_error() -> None:
    with (
        httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(503, text="upstream unavailable")
            )
        ) as http,
        pytest.raises(DifyError) as error,
    ):
        DifyClient(settings(), http).suggest_names(["episode.mkv"], ["Show"])

    assert "503" in str(error.value)
    assert len(str(error.value)) < 120


def test_suggest_names_maps_request_error_to_dify_error() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    with (
        httpx.Client(transport=httpx.MockTransport(fail)) as http,
        pytest.raises(DifyError) as error,
    ):
        DifyClient(settings(), http).suggest_names(["episode.mkv"], ["Show"])

    assert "offline" in str(error.value)
    assert len(str(error.value)) < 120


def test_empty_api_key_fails_before_transport() -> None:
    called = False

    def handle(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200)

    with (
        httpx.Client(transport=httpx.MockTransport(handle)) as http,
        pytest.raises(ConfigurationError),
    ):
        DifyClient(settings(api_key=""), http).suggest_names(["episode.mkv"], ["Show"])

    assert not called


def test_invalid_endpoint_is_a_configuration_error() -> None:
    invalid_settings = replace(settings(), api_endpoint="http://[::1")

    with (
        httpx.Client() as http,
        pytest.raises(ConfigurationError, match="Invalid Dify"),
    ):
        DifyClient(invalid_settings, http).suggest_names(["episode.mkv"], ["Show"])
