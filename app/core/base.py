"""
Base types for the core layer.

`AppBaseException` is the root for domain/HTTP-mappable errors raised from
services or CRUD and translated in exception handlers (optional extension).
"""


class AppBaseException(Exception):
    """Base class for application-level exceptions (business rules, auth)."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)
