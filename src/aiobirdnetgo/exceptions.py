"""Exceptions for the aiobirdnetgo library."""

from __future__ import annotations


class BirdNetGoError(Exception):
    """Base exception for all aiobirdnetgo errors."""


class BirdNetGoConnectionError(BirdNetGoError):
    """Exception raised when connection to BirdNET-Go fails."""


class BirdNetGoTimeoutError(BirdNetGoError):
    """Exception raised when an API request or stream times out."""


class BirdNetGoAuthenticationError(BirdNetGoError):
    """Exception raised when authentication fails (HTTP 401 / 403)."""


class BirdNetGoNotFoundError(BirdNetGoError):
    """Exception raised when a requested resource is not found (HTTP 404)."""


class BirdNetGoResponseError(BirdNetGoError):
    """Exception raised when the server returns an unexpected response or status."""

    def __init__(self, status_code: int, message: str) -> None:
        """Initialize response error."""
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message
