import asyncio
import os
from typing import List

from fastapi import APIRouter, HTTPException

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.models.crawl_models import CrawlRequest, CrawlStatus, SiteInfo
from falcon_iq_analyzer.pipeline.job_manager import JobManager
from falcon_iq_analyzer.services.crawler import get_output_dir_for_url, run_crawl

router = APIRouter()
crawl_job_manager = JobManager()


@router.post("/crawl", response_model=CrawlStatus)
async def start_crawl(request: CrawlRequest) -> CrawlStatus:
    """Start a background crawl job via the crawler HTTP API."""
    job = crawl_job_manager.create_job()
    output_dir = get_output_dir_for_url(request.url)

    asyncio.create_task(
        run_crawl(
            url=request.url,
            max_pages=request.max_pages,
            job_manager=crawl_job_manager,
            job_id=job.job_id,
        )
    )

    return CrawlStatus(
        job_id=job.job_id,
        status="pending",
        progress="Job queued",
        output_dir=output_dir,
    )


@router.get("/crawl/{job_id}", response_model=CrawlStatus)
async def get_crawl_status(job_id: str) -> CrawlStatus:
    """Check crawl job status."""
    job = crawl_job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return CrawlStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        error=job.error,
    )


@router.get("/sites", response_model=List[SiteInfo])
async def list_sites() -> List[SiteInfo]:
    """List already-crawled sites."""
    base_dir = settings.crawled_sites_dir
    sites: List[SiteInfo] = []

    if not os.path.isdir(base_dir):
        return sites

    for entry in sorted(os.listdir(base_dir)):
        site_dir = os.path.join(base_dir, entry)
        if os.path.isdir(site_dir):
            page_count = _count_html_files(site_dir)
            if page_count > 0:
                sites.append(
                    SiteInfo(
                        domain=entry,
                        directory=site_dir,
                        page_count=page_count,
                    )
                )

    return sites


def _count_html_files(directory: str) -> int:
    """Count .html files in a directory tree."""
    count = 0
    try:
        for root, _dirs, files in os.walk(directory):
            for f in files:
                if f.endswith(".html"):
                    count += 1
    except OSError:
        pass
    return count
