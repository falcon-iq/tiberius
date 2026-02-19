import logging
import os
import re
from typing import List, Optional, Set

from falcon_iq_analyzer.models.domain import PageInfo

logger = logging.getLogger(__name__)

KNOWN_LOCALES = {"ar", "de", "es", "fr", "jp"}


def _parse_locale(filepath: str) -> Optional[str]:
    """Detect non-English locale from the file path or name."""
    filename = os.path.basename(filepath)
    # Check for locale prefix pattern like "de_" or "/de/" in path
    for locale in KNOWN_LOCALES:
        if re.search(rf"(^|[/_]){locale}([/_]|$)", filename) or f"/{locale}/" in filepath:
            return locale
    return None


def _filepath_to_url_path(filepath: str) -> str:
    """Convert a crawled HTML filename to an approximate URL path."""
    filename = os.path.basename(filepath)
    # Remove .html extension
    name = re.sub(r"\.html?$", "", filename)
    # Replace encoded or separator chars
    name = name.replace("_", "/")
    return f"/{name}"


def load_pages(crawl_directory: str, locale_filter: str = "en") -> List[PageInfo]:
    """Load all HTML files from the crawl directory, filtered by locale."""
    from falcon_iq_analyzer.config import settings

    if settings.storage_type == "s3":
        return _load_pages_from_s3(crawl_directory, locale_filter)
    return _load_pages_from_local(crawl_directory, locale_filter)


def _load_pages_from_local(crawl_directory: str, locale_filter: str = "en") -> List[PageInfo]:
    """Load pages from local filesystem."""
    pages: List[PageInfo] = []
    seen_paths: Set[str] = set()

    if not os.path.isdir(crawl_directory):
        raise FileNotFoundError(f"Crawl directory not found: {crawl_directory}")

    for root, _dirs, files in os.walk(crawl_directory):
        for fname in files:
            if not fname.endswith((".html", ".htm")):
                continue

            filepath = os.path.join(root, fname)
            locale = _parse_locale(filepath)

            # Filter: keep only desired locale
            if locale_filter == "__all__":
                pass  # no filtering
            elif locale_filter == "en" and locale is not None:
                continue
            elif locale_filter != "en" and locale != locale_filter:
                continue

            url_path = _filepath_to_url_path(filepath)

            # Deduplicate by URL path
            if url_path in seen_paths:
                continue
            seen_paths.add(url_path)

            pages.append(
                PageInfo(
                    filepath=filepath,
                    filename=fname,
                    url_path=url_path,
                    locale=locale,
                )
            )

    logger.info("Loaded %d pages (locale=%s) from %s", len(pages), locale_filter, crawl_directory)
    return pages


def _load_pages_from_s3(crawl_directory: str, locale_filter: str = "en") -> List[PageInfo]:
    """Load pages from S3 bucket. crawl_directory is used as the S3 key prefix."""
    import boto3

    from falcon_iq_analyzer.config import settings

    s3 = boto3.client("s3", region_name=settings.aws_region)
    bucket = settings.s3_bucket_name
    prefix = f"crawls/{crawl_directory}/"

    pages: List[PageInfo] = []
    seen_paths: Set[str] = set()

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            fname = key.rsplit("/", 1)[-1] if "/" in key else key

            if not fname.endswith((".html", ".htm")):
                continue

            locale = _parse_locale(key)

            if locale_filter == "__all__":
                pass
            elif locale_filter == "en" and locale is not None:
                continue
            elif locale_filter != "en" and locale != locale_filter:
                continue

            url_path = _filepath_to_url_path(key)

            if url_path in seen_paths:
                continue
            seen_paths.add(url_path)

            pages.append(
                PageInfo(
                    filepath=key,  # S3 key used as filepath
                    filename=fname,
                    url_path=url_path,
                    locale=locale,
                )
            )

    logger.info("Loaded %d pages (locale=%s) from s3://%s/%s", len(pages), locale_filter, bucket, prefix)
    return pages
