import fnmatch
import logging
import os
from typing import Optional

from falcon_iq_analyzer.storage.base import StorageService

logger = logging.getLogger(__name__)


class LocalStorageService(StorageService):
    """Local filesystem storage backend."""

    def __init__(self, base_dir: str = "results"):
        self._base_dir = base_dir
        os.makedirs(self._base_dir, exist_ok=True)

    def _full_path(self, key: str) -> str:
        return os.path.join(self._base_dir, key)

    def save_file(self, key: str, content: str, content_type: str = "text/plain") -> str:
        path = self._full_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug("Saved file to %s", path)
        return path

    def load_file(self, key: str) -> Optional[str]:
        path = self._full_path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except OSError:
            logger.warning("Failed to read file: %s", path)
            return None

    def file_exists(self, key: str) -> bool:
        return os.path.exists(self._full_path(key))

    def list_files(self, prefix: str) -> list[str]:
        """List files matching a glob-like pattern relative to base_dir."""
        matches: list[str] = []
        for root, _dirs, files in os.walk(self._base_dir):
            for fname in files:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, self._base_dir)
                if fnmatch.fnmatch(rel_path, prefix):
                    matches.append(rel_path)
        return sorted(matches)

    def is_healthy(self) -> bool:
        try:
            test_path = os.path.join(self._base_dir, ".health_check")
            with open(test_path, "w") as f:
                f.write("ok")
            os.remove(test_path)
            return True
        except OSError:
            return False
