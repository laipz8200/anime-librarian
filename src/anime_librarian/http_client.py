"""HTTP client implementation for the AnimeLibrarian application."""

from typing import Any

import httpx


class HttpxClient:
    """Implementation of HttpClient using httpx library.

    Exposes last request/response metadata for verbose logging without
    changing the public return type (still returns parsed JSON dict).
    """

    def __init__(self) -> None:
        self.last_method: str | None = None
        self.last_url: str | None = None
        self.last_status_code: int | None = None

    def post(
        self, url: str, *, headers: dict[str, str], json: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        """
        Send a POST request using httpx.

        Args:
            url: The URL to send the request to
            headers: HTTP headers to include in the request
            json: JSON payload to send in the request body
            timeout: Request timeout in seconds

        Returns:
            The parsed JSON response as a dictionary

        Raises:
            httpx.HTTPStatusError: If the HTTP request returns an error status code
            httpx.RequestError: If the request fails
        """
        self.last_method = "POST"
        self.last_url = url
        resp = httpx.post(url, headers=headers, json=json, timeout=timeout)
        self.last_status_code = resp.status_code
        resp.raise_for_status()  # Raise an exception for HTTP errors
        return resp.json()
