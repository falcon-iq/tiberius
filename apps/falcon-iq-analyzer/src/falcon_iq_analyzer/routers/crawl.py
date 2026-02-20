import asyncio
import json
import os
import shutil
from typing import List

from fastapi import APIRouter, HTTPException

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.models.crawl_models import CrawlRequest, CrawlStatus, SiteInfo
from falcon_iq_analyzer.pipeline.job_manager import JobManager
from falcon_iq_analyzer.services.crawler import run_crawl

router = APIRouter()
crawl_job_manager = JobManager()


@router.post("/crawl", response_model=CrawlStatus)
async def start_crawl(request: CrawlRequest) -> CrawlStatus:
    """Start a background crawl job via the crawler HTTP API."""
    job = crawl_job_manager.create_job()

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
        output_dir=job.output_dir,
        page_count=job.page_count,
        error=job.error,
    )


@router.get("/sites", response_model=List[SiteInfo])
async def list_sites() -> List[SiteInfo]:
    """List already-crawled sites, reading _metadata.json for domain info."""
    base_dir = settings.crawled_sites_dir
    sites: List[SiteInfo] = []

    if not os.path.isdir(base_dir):
        return sites

    for entry in sorted(os.listdir(base_dir)):
        site_dir = os.path.join(base_dir, entry)
        if os.path.isdir(site_dir):
            page_count = _count_html_files(site_dir)
            if page_count > 0:
                domain = entry  # fallback: use directory name
                meta_path = os.path.join(site_dir, "_metadata.json")
                if os.path.isfile(meta_path):
                    try:
                        with open(meta_path) as f:
                            meta = json.load(f)
                        domain = meta.get("domain", entry)
                    except Exception:
                        pass
                sites.append(
                    SiteInfo(
                        domain=domain,
                        directory=site_dir,
                        page_count=page_count,
                    )
                )

    return sites


@router.delete("/sites/{domain}")
async def delete_site(domain: str) -> dict:
    """Delete a crawled site directory by domain name.

    Searches all directories for a matching _metadata.json domain,
    falls back to matching the directory name directly.
    """
    base_dir = settings.crawled_sites_dir
    base_real = os.path.realpath(base_dir)

    if not os.path.isdir(base_dir):
        raise HTTPException(status_code=404, detail="Site not found")

    # Search for the directory matching this domain
    target_dir = None
    for entry in os.listdir(base_dir):
        site_dir = os.path.join(base_dir, entry)
        if not os.path.isdir(site_dir):
            continue

        # Check _metadata.json first
        meta_path = os.path.join(site_dir, "_metadata.json")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                if meta.get("domain") == domain:
                    target_dir = site_dir
                    break
            except Exception:
                pass

        # Fallback: directory name matches domain
        if entry == domain:
            target_dir = site_dir
            break

    if not target_dir:
        raise HTTPException(status_code=404, detail="Site not found")

    # Ensure the path is actually under the base directory
    target_real = os.path.realpath(target_dir)
    if not target_real.startswith(base_real + os.sep):
        raise HTTPException(status_code=400, detail="Invalid domain")

    shutil.rmtree(target_real)
    return {"status": "deleted", "domain": domain}


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
