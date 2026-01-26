"""EMT exception hierarchy.

This module defines all custom exceptions used in the EMT library.
"""


class EmtlException(Exception):
    """Base exception for all EMT errors.

    All EMT-specific exceptions inherit from this class, allowing
    users to catch all EMT errors with a single except clause.
    """

    pass


class LoginFailedError(EmtlException):
    """Exception raised when client login fails.

    This can occur due to:
    - Invalid username or password
    - Captcha recognition failure
    - Network issues
    - Account locked or suspended

    Attributes:
        message: Human-readable error description
    """

    pass


class EmAPIError(EmtlException):
    """Exception raised when an API request fails.

    This can occur due to:
    - HTTP errors (non-200 status codes)
    - API returns error status (Status == -1)
    - Network connectivity issues

    Attributes:
        message: Human-readable error description
        status_code: HTTP status code (if applicable)
        response: Response content (if available)
    """

    def __init__(self, message: str, status_code: int | None = None, response: str | None = None):
        """Initialize API error.

        Args:
            message: Error description
            status_code: HTTP status code (optional)
            response: Response content (optional)
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response
