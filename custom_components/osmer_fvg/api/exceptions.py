"""Exceptions for the OSMER API."""


class OsmerApiError(Exception):
    """Base exception for the OSMER API."""


class OsmerConnectionError(OsmerApiError):
    """Raised when the API cannot be reached."""


class OsmerApiResponseError(OsmerApiError):
    """Raised when the API returns an unexpected response."""