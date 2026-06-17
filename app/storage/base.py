from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload bytes at key; returns the key."""

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Return bytes stored at key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove object at key."""

    @abstractmethod
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Return a URL (signed or public) to access the object."""
