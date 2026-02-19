import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from falcon_iq_analyzer.storage.base import StorageService

logger = logging.getLogger(__name__)


class S3StorageService(StorageService):
    """S3 storage backend for AWS Fargate deployment."""

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self._bucket_name = bucket_name
        self._region = region
        self._s3 = boto3.client("s3", region_name=region)
        self._key_prefix = "analyzer/"

    def _full_key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    def save_file(self, key: str, content: str, content_type: str = "text/plain") -> str:
        full_key = self._full_key(key)
        self._s3.put_object(
            Bucket=self._bucket_name,
            Key=full_key,
            Body=content.encode("utf-8"),
            ContentType=content_type,
        )
        uri = f"s3://{self._bucket_name}/{full_key}"
        logger.debug("Saved file to %s", uri)
        return uri

    def load_file(self, key: str) -> Optional[str]:
        full_key = self._full_key(key)
        try:
            response = self._s3.get_object(Bucket=self._bucket_name, Key=full_key)
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            logger.warning("Failed to load file from S3: %s", full_key, exc_info=True)
            return None

    def file_exists(self, key: str) -> bool:
        full_key = self._full_key(key)
        try:
            self._s3.head_object(Bucket=self._bucket_name, Key=full_key)
            return True
        except ClientError:
            return False

    def list_files(self, prefix: str) -> list[str]:
        """List files matching a prefix. Glob wildcards are converted to prefix search."""
        # Convert glob pattern to S3 prefix (strip wildcards for prefix-based listing)
        search_prefix = self._full_key(prefix.split("*")[0])
        matches: list[str] = []

        try:
            paginator = self._s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self._bucket_name, Prefix=search_prefix):
                for obj in page.get("Contents", []):
                    # Strip the key prefix to return relative paths
                    rel_key = obj["Key"]
                    if rel_key.startswith(self._key_prefix):
                        rel_key = rel_key[len(self._key_prefix):]
                    matches.append(rel_key)
        except ClientError:
            logger.warning("Failed to list files from S3 with prefix: %s", search_prefix, exc_info=True)

        return sorted(matches)

    def is_healthy(self) -> bool:
        try:
            self._s3.head_bucket(Bucket=self._bucket_name)
            return True
        except ClientError:
            return False
