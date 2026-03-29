"""Typed application errors."""

from __future__ import annotations


class AppError(Exception):
    """Base for predictable API failures."""

    code: str = "app_error"
    status_code: int = 500

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        if code:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppError):
    code = "validation_error"
    status_code = 400


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404


class ServiceUnavailableError(AppError):
    code = "service_unavailable"
    status_code = 503


class RateLimitError(AppError):
    code = "rate_limited"
    status_code = 429
