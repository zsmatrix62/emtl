"""EMT (East Money Trade) library for programmatic trading.

This library provides a Python interface to the EMT trading platform,
allowing users to query account information, create orders, and manage
trades programmatically with multi-user support and session persistence.
"""

__version__ = "0.3.0"

from .client import EMTClient
from .client_manager import ClientManager
from .error import EmAPIError
from .error import EmtlException
from .error import LoginFailedError
from .serializer import DillSerializer
from .serializer import EMTClientSerializer
from .serializer import SerializerError

__all__ = [
    "ClientManager",
    "DillSerializer",
    # Core classes
    "EMTClient",
    # Serializers
    "EMTClientSerializer",
    "EmAPIError",
    # Exceptions
    "EmtlException",
    "LoginFailedError",
    "SerializerError",
]
