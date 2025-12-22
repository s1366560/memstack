"""
Custom exceptions for VIP Memory SDK.
"""


class VipMemoryError(Exception):
    """Base exception for VIP Memory SDK."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AuthenticationError(VipMemoryError):
    """Raised when authentication fails."""

    pass


class APIError(VipMemoryError):
    """Raised when API request fails."""

    def __init__(self, message: str, status_code: int = None, response_body: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class RateLimitError(VipMemoryError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class ValidationError(VipMemoryError):
    """Raised when input validation fails."""

    pass


class NetworkError(VipMemoryError):
    """Raised when network request fails."""

    pass
