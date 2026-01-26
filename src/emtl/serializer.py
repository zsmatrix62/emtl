"""Serialization support for EMTClient instances.

This module provides abstract and concrete implementations for serializing
EMTClient instances with expiration support.
"""

import abc
import time
from pathlib import Path
from typing import Optional

import dill

from .client import EMTClient


class SerializerError(Exception):
    """Exception raised for serializer-related errors."""

    pass


class EMTClientSerializer(abc.ABC):
    """Abstract base class for EMTClient serialization.

    Implementations must define how to save, load, and delete client instances
    with expiration support.
    """

    @abc.abstractmethod
    def save(self, client: EMTClient, ttl: int = 1800) -> None:
        """Save a client instance with time-to-live.

        Args:
            client: The EMTClient instance to save.
            ttl: Time-to-live in seconds (default 30 minutes).

        Raises:
            SerializerError: If saving fails.
        """
        pass

    @abc.abstractmethod
    def load(self, username: str) -> Optional[EMTClient]:
        """Load a client instance by username.

        Returns None if the client is not found or has expired.

        Args:
            username: The username associated with the client.

        Returns:
            The loaded EMTClient instance, or None if not found/expired.

        Raises:
            SerializerError: If loading fails (other than expiration).
        """
        pass

    @abc.abstractmethod
    def delete(self, username: str) -> bool:
        """Delete a saved client instance.

        Args:
            username: The username associated with the client.

        Returns:
            True if deleted, False if not found.

        Raises:
            SerializerError: If deletion fails.
        """
        pass

    @abc.abstractmethod
    def list_users(self) -> list[str]:
        """List all usernames with saved (non-expired) clients.

        Returns:
            List of usernames.
        """
        pass


class DillSerializer(EMTClientSerializer):
    """Default implementation using dill for serialization with expiration.

    Each client is saved as a separate file named after the username.
    Expiration is checked on load based on the saved timestamp.
    """

    def __init__(self, storage_dir: str | Path = "~/.emtl"):
        """Initialize the serializer.

        Args:
            storage_dir: Directory to store serialized clients.
        """
        self.storage_dir = Path(storage_dir).expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, username: str) -> Path:
        """Get the file path for a given username."""
        return self.storage_dir / f"{username}.pkl"

    def _get_meta_path(self, username: str) -> Path:
        """Get the metadata file path for a given username."""
        return self.storage_dir / f"{username}.meta"

    def save(self, client: EMTClient, ttl: int = 1800) -> None:
        """Save a client instance with time-to-live.

        Args:
            client: The EMTClient instance to save.
            ttl: Time-to-live in seconds (default 30 minutes).

        Raises:
            SerializerError: If client has no username or saving fails.
        """
        if not client.username:
            raise SerializerError("Cannot save client without username")

        file_path = self._get_file_path(client.username)
        meta_path = self._get_meta_path(client.username)

        try:
            # Save client data
            with open(file_path, "wb") as f:
                dill.dump(client, f)

            # Save metadata with expiration time
            expires_at = time.time() + ttl
            with open(meta_path, "w") as f:
                f.write(str(expires_at))
        except Exception as e:
            raise SerializerError(f"Failed to save client: {e}") from e

    def load(self, username: str) -> Optional[EMTClient]:
        """Load a client instance by username.

        Returns None if the client is not found or has expired.

        Args:
            username: The username associated with the client.

        Returns:
            The loaded EMTClient instance, or None if not found/expired.
        """
        file_path = self._get_file_path(username)
        meta_path = self._get_meta_path(username)

        if not file_path.exists() or not meta_path.exists():
            return None

        # Check expiration
        try:
            with open(meta_path, "r") as f:
                expires_at = float(f.read().strip())
            if time.time() > expires_at:
                # Expired, clean up files
                self.delete(username)
                return None
        except Exception:
            # If metadata is corrupted, treat as expired
            self.delete(username)
            return None

        # Load client
        try:
            with open(file_path, "rb") as f:
                return dill.load(f)
        except Exception as e:
            raise SerializerError(f"Failed to load client: {e}") from e

    def delete(self, username: str) -> bool:
        """Delete a saved client instance.

        Args:
            username: The username associated with the client.

        Returns:
            True if deleted, False if not found.
        """
        file_path = self._get_file_path(username)
        meta_path = self._get_meta_path(username)

        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
            return True
        except Exception as e:
            raise SerializerError(f"Failed to delete client: {e}") from e

    def list_users(self) -> list[str]:
        """List all usernames with saved (non-expired) clients.

        Returns:
            List of usernames.
        """
        users = []
        current_time = time.time()

        for file_path in self.storage_dir.glob("*.pkl"):
            username = file_path.stem
            meta_path = self._get_meta_path(username)

            # Check if expired
            if meta_path.exists():
                try:
                    with open(meta_path, "r") as f:
                        expires_at = float(f.read().strip())
                    if current_time <= expires_at:
                        users.append(username)
                except Exception:
                    # Corrupted metadata, skip
                    continue

        return sorted(users)
