"""HTTP client implementation for the AnimeLibrarian application."""

from typing import Any

import httpx


class HttpxClient:
    """Implementation of HttpClient using httpx library."""

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
        resp = httpx.post(url, headers=headers, json=json, timeout=timeout)
        resp.raise_for_status()  # Raise an exception for HTTP errors
        return resp.json()
