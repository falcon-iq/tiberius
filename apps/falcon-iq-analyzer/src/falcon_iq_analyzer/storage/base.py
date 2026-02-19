from abc import ABC, abstractmethod
from typing import Optional


class StorageService(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_file(self, key: str, content: str, content_type: str = "text/plain") -> str:
        """Save content to storage. Returns the path/URI of the saved file."""

    @abstractmethod
    def load_file(self, key: str) -> Optional[str]:
        """Load content from storage. Returns None if not found."""

    @abstractmethod
    def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage."""

    @abstractmethod
    def list_files(self, prefix: str) -> list[str]:
        """List files matching a prefix/pattern."""

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if the storage backend is accessible."""
