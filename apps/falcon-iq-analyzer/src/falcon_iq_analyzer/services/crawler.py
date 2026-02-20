import asyncio
import json
import logging
import os

import httpx

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.pipeline.job_manager import JobManager

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3


async def run_crawl(
    url: str,
    max_pages: int,
    job_manager: JobManager,
    job_id: str,
) -> str | None:
    """Start a crawl via the falcon-iq-crawler HTTP API and poll until completion.

    Returns the crawl_id from the crawler service, or None on failure.
    """
    crawler_url = settings.crawler_api_url.rstrip("/")
    job_manager.update_status(job_id, "running", "Starting crawl via API...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Start the crawl
            response = await client.post(
                f"{crawler_url}/api/crawl",
                json={"url": url, "maxPages": max_pages},
            )
            response.raise_for_status()
            data = response.json()
            crawl_id = data.get("crawlId")

            if not crawl_id:
                job_manager.set_error(job_id, "Crawler API did not return a crawlId")
                return None

            # Compute the actual output directory based on crawl_id
            output_dir = os.path.join(settings.crawled_sites_dir, crawl_id)

            logger.info("Crawl started: crawlId=%s for %s", crawl_id, url)
            job_manager.update_status(
                job_id, "running", f"Crawling... (crawlId={crawl_id})"
            )

            # Store output_dir on the job immediately so status endpoint can return it
            job = job_manager.get_job(job_id)
            if job:
                job.output_dir = output_dir

            # Poll for completion
            while True:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)

                status_response = await client.get(f"{crawler_url}/api/crawl/{crawl_id}/status")
                status_response.raise_for_status()
                status_data = status_response.json()

                crawl_status = status_data.get("status", "").upper()
                pages_crawled = status_data.get("pagesDownloaded", 0)

                # Update page_count on the job during polling
                if job:
                    job.page_count = pages_crawled

                if crawl_status == "COMPLETED":
                    job_manager.update_status(
                        job_id, "completed",
                        f"Crawl complete: {pages_crawled} pages",
                    )
                    if job:
                        job.page_count = pages_crawled
                    logger.info("Crawl completed: %d pages for %s (dir: %s)", pages_crawled, url, output_dir)

                    # Write metadata so GET /sites can map directory back to domain
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).hostname or url
                        os.makedirs(output_dir, exist_ok=True)
                        meta_path = os.path.join(output_dir, "_metadata.json")
                        with open(meta_path, "w") as f:
                            json.dump({"domain": domain, "url": url, "crawl_id": crawl_id}, f)
                    except Exception:
                        logger.warning("Failed to write crawl metadata for %s", output_dir, exc_info=True)

                    return crawl_id

                elif crawl_status == "FAILED":
                    error_msg = status_data.get("error", "Crawl failed")
                    job_manager.set_error(job_id, error_msg)
                    logger.error("Crawl failed for %s: %s", url, error_msg)
                    return None

                else:
                    job_manager.update_status(
                        job_id, "running",
                        f"Crawling... {pages_crawled} pages downloaded (crawlId={crawl_id})",
                    )

    except httpx.HTTPError as e:
        logger.exception("HTTP error communicating with crawler API")
        job_manager.set_error(job_id, f"Crawler API error: {e}")
        return None
    except Exception as e:
        logger.exception("Crawler failed")
        job_manager.set_error(job_id, str(e))
        return None
