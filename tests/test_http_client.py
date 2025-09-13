"""Tests for the HTTP client module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from anime_librarian.http_client import HttpxClient


@patch("httpx.post")
def test_http_client_post_success(mock_post):
    """Test successful HTTP POST request."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"result": "success"}}
    mock_post.return_value = mock_response

    # Create client and make request
    client = HttpxClient()
    result = client.post(
        url="https://api.example.com/endpoint",
        headers={"Authorization": "Bearer token"},
        json={"key": "value"},
        timeout=30.0,
    )

    # Verify the request was made with correct parameters
    mock_post.assert_called_once_with(
        "https://api.example.com/endpoint",
        headers={"Authorization": "Bearer token"},
        json={"key": "value"},
        timeout=30.0,
    )

    # Verify response was processed correctly
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == {"data": {"result": "success"}}


@patch("httpx.post")
def test_http_client_post_http_error(mock_post):
    """Test HTTP POST request with HTTP error."""
    # Setup mock response to raise an HTTP error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found",
        request=MagicMock(),
        response=MagicMock(),
    )
    mock_post.return_value = mock_response

    # Create client and attempt request
    client = HttpxClient()

    # Verify the error is propagated
    with pytest.raises(httpx.HTTPStatusError):
        _ = client.post(
            url="https://api.example.com/endpoint",
            headers={"Authorization": "Bearer token"},
            json={"key": "value"},
            timeout=30.0,
        )

    # Verify the request was made
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


@patch("httpx.post")
def test_http_client_post_request_error(mock_post):
    """Test HTTP POST request with request error."""
    # Setup mock to raise a request error
    mock_post.side_effect = httpx.RequestError("Connection error", request=MagicMock())

    # Create client and attempt request
    client = HttpxClient()

    # Verify the error is propagated
    with pytest.raises(httpx.RequestError):
        _ = client.post(
            url="https://api.example.com/endpoint",
            headers={"Authorization": "Bearer token"},
            json={"key": "value"},
            timeout=30.0,
        )

    # Verify the request was attempted
    mock_post.assert_called_once()
