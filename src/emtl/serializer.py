"""Serialization support for EMTClient instances.

This module provides abstract and concrete implementations for serializing
EMTClient instances. Session validity is verified on load rather than using
time-based expiration.
"""

import abc
import os
from pathlib import Path
from typing import Optional

import dill

from .client import EMTClient


class SerializerError(Exception):
    """Exception raised for serializer-related errors."""

    pass


class EMTClientSerializer(abc.ABC):
    """Abstract base class for EMTClient serialization.

    Implementations must define how to save, load, and delete client instances.
    Session validity is verified externally by the ClientManager.
    """

    @abc.abstractmethod
    def save(self, client: EMTClient) -> None:
        """Save a client instance.

        Args:
            client: The EMTClient instance to save.

        Raises:
            SerializerError: If saving fails.
        """
        pass

    @abc.abstractmethod
    def load(self, username: str) -> Optional[EMTClient]:
        """Load a client instance by username.

        Args:
            username: The username associated with the client.

        Returns:
            The loaded EMTClient instance, or None if not found.

        Raises:
            SerializerError: If loading fails.
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
        """List all usernames with saved clients.

        Returns:
            List of usernames.
        """
        pass


class DillSerializer(EMTClientSerializer):
    """Default implementation using dill for serialization.

    Each client is saved as a separate file named after the username.
    Session validity is verified externally by the ClientManager.
    """

    def __init__(self, storage_dir: str | Path | None = None):
        """Initialize the serializer.

        Storage directory is determined by:
        1. Environment variable EMTL_STORAGE_DIR (if set)
        2. Provided storage_dir argument (if set)
        3. Default to .emtl/ in current working directory

        Args:
            storage_dir: Optional directory to store serialized clients.
        """
        # Check environment variable first
        env_dir = os.getenv("EMTL_STORAGE_DIR")

        if env_dir:
            # Environment variable takes precedence
            dir_path = Path(env_dir)
        elif storage_dir is not None:
            # Use provided argument
            dir_path = Path(storage_dir).expanduser()
        else:
            # Default to .emtl/ in current directory
            dir_path = Path(".emtl")

        self.storage_dir = dir_path
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, username: str) -> Path:
        """Get the file path for a given username."""
        return self.storage_dir / f"{username}.pkl"

    def save(self, client: EMTClient) -> None:
        """Save a client instance.

        Args:
            client: The EMTClient instance to save.

        Raises:
            SerializerError: If client has no username or saving fails.
        """
        if not client.username:
            raise SerializerError("Cannot save client without username")

        file_path = self._get_file_path(client.username)

        try:
            with open(file_path, "wb") as f:
                dill.dump(client, f)
        except Exception as e:
            raise SerializerError(f"Failed to save client: {e}") from e

    def load(self, username: str) -> Optional[EMTClient]:
        """Load a client instance by username.

        Args:
            username: The username associated with the client.

        Returns:
            The loaded EMTClient instance, or None if not found.

        Raises:
            SerializerError: If loading fails.
        """
        file_path = self._get_file_path(username)

        if not file_path.exists():
            return None

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

        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            return True
        except Exception as e:
            raise SerializerError(f"Failed to delete client: {e}") from e

    def list_users(self) -> list[str]:
        """List all usernames with saved clients.

        Returns:
            List of usernames.
        """
        users = []
        for file_path in self.storage_dir.glob("*.pkl"):
            users.append(file_path.stem)
        return sorted(users)
