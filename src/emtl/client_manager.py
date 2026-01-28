"""Client manager for EMTClient instances with serialization support.

This module provides a manager class that handles client lifecycle,
including loading from cache, verifying session validity, and creating
new instances when needed.
"""

from .client import EMTClient
from .error import LoginFailedError
from .serializer import EMTClientSerializer


class ClientManager:
    """Manager for EMTClient instances with serialization support.

    The manager handles loading cached clients, verifying session validity,
    and creating new ones as needed. Session validity is verified on load
    rather than using time-based expiration.
    """

    def __init__(self, serializer: EMTClientSerializer):
        """Initialize the client manager.

        Args:
            serializer: The serializer to use for persisting clients.
        """
        self.serializer = serializer

    def get_client(self, username: str, password: str, max_retries: int = 3) -> EMTClient:
        """Get a client for the given username.

        This method will:
        1. Try to load an existing cached client from the serializer.
        2. Verify the session is valid using a lightweight API call.
        3. If invalid or not found, create a new client, login, and save it.
        4. Retry up to max_retries times if login/session verification fails.

        Args:
            username: The username for the client.
            password: The password for login (only used if creating new client).
            max_retries: Maximum number of retry attempts (default 3).

        Returns:
            An authenticated EMTClient instance with valid session.

        Raises:
            SerializerError: If serialization operations fail.
            LoginFailedError: If login fails after all retries.
        """
        for attempt in range(max_retries):
            try:
                # Try to load from cache
                client = self.serializer.load(username)

                if client is not None:
                    # Verify session is still valid
                    if client.verify_session():
                        return client
                    else:
                        # Session expired, delete cached file
                        self.serializer.delete(username)

                # Create new client and login
                client = EMTClient()
                validate_key = client.login(username, password)

                # Check if login succeeded
                if validate_key is None:
                    raise LoginFailedError(f"Login failed for user '{username}'. Please check username, password, and captcha.")

                # Save to serializer
                self.serializer.save(client)

                return client

            except (LoginFailedError, Exception) as e:
                if attempt == max_retries - 1:
                    # Last attempt failed, clean up and raise
                    self.serializer.delete(username)
                    raise LoginFailedError(f"Failed to get client for '{username}' after {max_retries} attempts: {e}") from e
                # Retry

        # Should not reach here, but just in case
        self.serializer.delete(username)
        raise LoginFailedError(f"Failed to get client for '{username}' after {max_retries} attempts")

    def invalidate(self, username: str) -> bool:
        """Invalidate a cached client by username.

        Args:
            username: The username to invalidate.

        Returns:
            True if the client was deleted, False if not found.
        """
        return self.serializer.delete(username)

    def list_cached_users(self) -> list[str]:
        """List all usernames with cached clients.

        Returns:
            List of usernames.
        """
        return self.serializer.list_users()
