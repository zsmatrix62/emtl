"""EMT (East Money Trade) library for programmatic trading.

This library provides a Python interface to the EMT trading platform,
allowing users to query account information, create orders, and manage
trades programmatically with multi-user support and session persistence.
"""

__version__ = "0.2.8"

from .client import EMTClient
from .client_manager import ClientManager, LoginFailedError
from .serializer import DillSerializer, EMTClientSerializer, SerializerError

__all__ = [
    "EMTClient",
    "ClientManager",
    "LoginFailedError",
    "EMTClientSerializer",
    "DillSerializer",
    "SerializerError",
]
