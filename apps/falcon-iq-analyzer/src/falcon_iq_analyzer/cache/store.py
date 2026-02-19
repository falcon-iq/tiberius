import json
import logging
import os
import tempfile
from typing import Dict, Optional

logger = logging.getLogger(__name__)

CACHE_DIR_NAME = ".analysis_cache"


class DiskCache:
    """Simple disk-based cache for per-page analysis results."""

    def __init__(self, crawl_directory: str):
        from falcon_iq_analyzer.config import settings

        if settings.storage_type == "s3":
            # In S3 mode, use a local temp directory for caching
            safe_dir_name = crawl_directory.replace("/", "_").replace("\\", "_")
            self._cache_dir = os.path.join(tempfile.gettempdir(), "analyzer_cache", safe_dir_name)
        else:
            self._cache_dir = os.path.join(crawl_directory, CACHE_DIR_NAME)

        os.makedirs(self._cache_dir, exist_ok=True)

    def _key_path(self, filename: str, stage: str) -> str:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        return os.path.join(self._cache_dir, f"{safe_name}.{stage}.json")

    def get(self, filename: str, stage: str) -> Optional[Dict]:
        path = self._key_path(filename, stage)
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Cache read failed for %s/%s", filename, stage)
            return None

    def set(self, filename: str, stage: str, data: dict) -> None:
        path = self._key_path(filename, stage)
        try:
            with open(path, "w") as f:
                json.dump(data, f)
        except OSError:
            logger.warning("Cache write failed for %s/%s", filename, stage)
