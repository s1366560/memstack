"""
Server exceptions.
"""


class VipMemoryError(Exception):
    """Base exception for VIP Memory errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(VipMemoryError):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(VipMemoryError):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class NotFoundError(VipMemoryError):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(VipMemoryError):
    """Validation error."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422)


class ServiceError(VipMemoryError):
    """Service error."""

    def __init__(self, message: str = "Service error occurred", status_code: int = 500):
        super().__init__(message, status_code=status_code)
