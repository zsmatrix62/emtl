"""Client manager for EMTClient instances with serialization support.

This module provides a manager class that handles client lifecycle,
including loading from cache and creating new instances when needed.
"""

from .client import EMTClient
from .serializer import EMTClientSerializer


class ClientManager:
    """Manager for EMTClient instances with serialization support.

    The manager handles loading cached clients or creating new ones
    as needed, with automatic serialization for session persistence.
    """

    def __init__(self, serializer: EMTClientSerializer, default_ttl: int = 1800):
        """Initialize the client manager.

        Args:
            serializer: The serializer to use for persisting clients.
            default_ttl: Default time-to-live for saved clients in seconds
                        (default 30 minutes).
        """
        self.serializer = serializer
        self.default_ttl = default_ttl

    def get_client(self, username: str, password: str, ttl: int | None = None) -> EMTClient:
        """Get a client for the given username.

        This method will:
        1. Try to load an existing cached client from the serializer.
        2. If the client exists and is not expired, return it directly.
        3. Otherwise, create a new client, login, and save it to the serializer.

        Args:
            username: The username for the client.
            password: The password for login (only used if creating new client).
            ttl: Optional time-to-live for saving the client in seconds.
                 If not provided, uses the default_ttl from initialization.

        Returns:
            An authenticated EMTClient instance.

        Raises:
            SerializerError: If serialization operations fail.
            Exception: If login fails.
        """
        # Try to load from cache
        client = self.serializer.load(username)
        if client is not None:
            return client

        # Create new client and login
        client = EMTClient()
        client.login(username, password)

        # Save to serializer
        save_ttl = ttl if ttl is not None else self.default_ttl
        self.serializer.save(client, ttl=save_ttl)

        return client

    def invalidate(self, username: str) -> bool:
        """Invalidate a cached client by username.

        Args:
            username: The username to invalidate.

        Returns:
            True if the client was deleted, False if not found.
        """
        return self.serializer.delete(username)

    def list_cached_users(self) -> list[str]:
        """List all usernames with cached (non-expired) clients.

        Returns:
            List of usernames.
        """
        return self.serializer.list_users()
