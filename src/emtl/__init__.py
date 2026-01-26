"""EMT (East Money Trade) library for programmatic trading.

This library provides a Python interface to the EMT trading platform,
allowing users to query account information, create orders, and manage
trades programmatically.
"""

__version__ = "0.2.8"

from .client import EMTClient

__all__ = [
    "EMTClient",
]

