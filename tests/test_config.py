from pathlib import Path

import pytest

from anime_librarian.config import load_settings
from anime_librarian.errors import ConfigurationError


def test_load_settings_uses_cli_paths_and_environment() -> None:
    settings = load_settings(
        source=Path("/media/inbox"),
        target=Path("/media/library"),
        environ={
            "ANIMELIBRARIAN_DIFY_API_KEY": "secret",
            "ANIMELIBRARIAN_API_TIMEOUT": "42",
        },
    )

    assert settings.source_path == Path("/media/inbox")
    assert settings.target_path == Path("/media/library")
    assert settings.api_key == "secret"
    assert settings.api_timeout == 42
    assert settings.api_endpoint == "https://api.dify.ai/v1/workflows/run"


def test_load_settings_falls_back_to_environment_paths() -> None:
    settings = load_settings(
        environ={
            "ANIMELIBRARIAN_SOURCE_PATH": "/media/inbox",
            "ANIMELIBRARIAN_TARGET_PATH": "/media/library",
            "ANIMELIBRARIAN_DIFY_API_KEY": "secret",
        }
    )

    assert settings.source_path == Path("/media/inbox")
    assert settings.target_path == Path("/media/library")


@pytest.mark.parametrize(
    ("environ", "message"),
    [
        (
            {"ANIMELIBRARIAN_DIFY_API_KEY": "secret"},
            "source directory",
        ),
        (
            {
                "ANIMELIBRARIAN_SOURCE_PATH": "/media/inbox",
                "ANIMELIBRARIAN_DIFY_API_KEY": "secret",
            },
            "target directory",
        ),
        (
            {
                "ANIMELIBRARIAN_SOURCE_PATH": "/media/inbox",
                "ANIMELIBRARIAN_TARGET_PATH": "/media/library",
            },
            "API key",
        ),
        (
            {
                "ANIMELIBRARIAN_SOURCE_PATH": "/media/inbox",
                "ANIMELIBRARIAN_TARGET_PATH": "/media/library",
                "ANIMELIBRARIAN_DIFY_API_KEY": "secret",
                "ANIMELIBRARIAN_API_TIMEOUT": "later",
            },
            "timeout",
        ),
    ],
)
def test_load_settings_reports_invalid_configuration(
    environ: dict[str, str], message: str
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        load_settings(environ=environ)


def test_load_settings_reports_unexpandable_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_to_expand(_path: Path) -> Path:
        message = "unknown user"
        raise RuntimeError(message)

    monkeypatch.setattr(Path, "expanduser", fail_to_expand)

    with pytest.raises(ConfigurationError, match="Cannot expand source directory"):
        load_settings(
            source=Path("~unknown/incoming"),
            target=Path("/media/library"),
            environ={"ANIMELIBRARIAN_DIFY_API_KEY": "secret"},
        )
