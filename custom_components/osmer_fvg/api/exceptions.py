"""Exceptions for the OSMER API."""


class OsmerApiError(Exception):
    """Base exception."""


class OsmerConnectionError(OsmerApiError):
    """Unable to connect to OSMER."""


class OsmerApiResponseError(OsmerApiError):
    """Invalid API response."""