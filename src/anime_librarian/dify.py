"""Dify workflow adapter."""

from typing import cast

import httpx
import json_repair
from pydantic import BaseModel

from .config import Settings
from .errors import AIResponseError, ConfigurationError, DifyError
from .models import NamePair


class _WorkflowOutputs(BaseModel):
    text: str


class _WorkflowData(BaseModel):
    outputs: _WorkflowOutputs


class _WorkflowResponse(BaseModel):
    data: _WorkflowData


class _Suggestions(BaseModel):
    result: list[NamePair]


class DifyClient:
    """Request and validate filename suggestions from a Dify workflow."""

    def __init__(self, settings: Settings, client: httpx.Client) -> None:
        self._settings = settings
        self._client = client

    def suggest_names(
        self, source_files: list[str], target_directories: list[str]
    ) -> list[NamePair]:
        """Return validated suggestions for the supplied catalog."""
        if not self._settings.api_key.strip():
            message = "Dify API key is missing; set ANIMELIBRARIAN_DIFY_API_KEY."
            raise ConfigurationError(message)

        try:
            response = self._client.post(
                self._settings.api_endpoint,
                headers={
                    "Authorization": f"Bearer {self._settings.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": {
                        "files": "\n".join(source_files),
                        "directories": "\n".join(target_directories),
                    },
                    "user": self._settings.user_name,
                    "response_mode": "blocking",
                },
                timeout=self._settings.api_timeout,
            )
            response.raise_for_status()
        except httpx.InvalidURL as error:
            message = f"Invalid Dify workflow endpoint: {error}."
            raise ConfigurationError(message) from error
        except httpx.HTTPStatusError as error:
            message = f"Dify returned HTTP {error.response.status_code}."
            raise DifyError(message) from error
        except (httpx.RequestError, UnicodeError) as error:
            message = f"Could not reach Dify: {error}."
            raise DifyError(message) from error

        try:
            workflow_response = _WorkflowResponse.model_validate(response.json())
            repaired = cast(
                "object",
                json_repair.repair_json(  # pyright: ignore[reportUnknownMemberType]
                    workflow_response.data.outputs.text,
                    return_objects=True,
                ),
            )
            return _Suggestions.model_validate(repaired).result
        except (ValueError, TypeError) as error:
            message = "Dify returned an invalid workflow response."
            raise AIResponseError(message) from error
