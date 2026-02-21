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
    if settings.storage_type == "s3":
        return _list_sites_s3()
    return _list_sites_local()


def _list_sites_local() -> List[SiteInfo]:
    """List crawled sites from local filesystem."""
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


def _list_sites_s3() -> List[SiteInfo]:
    """List crawled sites from S3 bucket under crawls/ prefix."""
    import boto3

    s3 = boto3.client("s3", region_name=settings.aws_region)
    bucket = settings.s3_bucket_name
    sites: List[SiteInfo] = []

    # List all "directories" under crawls/
    paginator = s3.get_paginator("list_objects_v2")
    crawl_ids: set[str] = set()

    for page in paginator.paginate(Bucket=bucket, Prefix="crawls/", Delimiter="/"):
        for prefix_obj in page.get("CommonPrefixes", []):
            # prefix_obj["Prefix"] looks like "crawls/<crawl_id>/"
            crawl_id = prefix_obj["Prefix"].split("/")[1]
            if crawl_id:
                crawl_ids.add(crawl_id)

    for crawl_id in sorted(crawl_ids):
        # Count HTML files
        page_count = 0
        for page in paginator.paginate(Bucket=bucket, Prefix=f"crawls/{crawl_id}/"):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith((".html", ".htm")):
                    page_count += 1

        if page_count == 0:
            continue

        domain = crawl_id  # fallback
        # Try to read _metadata.json
        try:
            meta_response = s3.get_object(
                Bucket=bucket, Key=f"crawls/{crawl_id}/_metadata.json"
            )
            meta = json.loads(meta_response["Body"].read().decode("utf-8"))
            domain = meta.get("domain", crawl_id)
        except Exception:
            pass

        sites.append(
            SiteInfo(
                domain=domain,
                directory=crawl_id,
                page_count=page_count,
            )
        )

    return sites


@router.delete("/sites/{domain}")
async def delete_site(domain: str) -> dict:
    """Delete a crawled site directory by domain name."""
    if settings.storage_type == "s3":
        return _delete_site_s3(domain)
    return _delete_site_local(domain)


def _delete_site_local(domain: str) -> dict:
    """Delete a crawled site from local filesystem."""
    base_dir = settings.crawled_sites_dir
    base_real = os.path.realpath(base_dir)

    if not os.path.isdir(base_dir):
        raise HTTPException(status_code=404, detail="Site not found")

    target_dir = None
    for entry in os.listdir(base_dir):
        site_dir = os.path.join(base_dir, entry)
        if not os.path.isdir(site_dir):
            continue

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

        if entry == domain:
            target_dir = site_dir
            break

    if not target_dir:
        raise HTTPException(status_code=404, detail="Site not found")

    target_real = os.path.realpath(target_dir)
    if not target_real.startswith(base_real + os.sep):
        raise HTTPException(status_code=400, detail="Invalid domain")

    shutil.rmtree(target_real)
    return {"status": "deleted", "domain": domain}


def _delete_site_s3(domain: str) -> dict:
    """Delete a crawled site from S3."""
    import boto3

    s3 = boto3.client("s3", region_name=settings.aws_region)
    bucket = settings.s3_bucket_name

    # Find the crawl_id matching this domain
    target_crawl_id = None
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix="crawls/", Delimiter="/"):
        for prefix_obj in page.get("CommonPrefixes", []):
            crawl_id = prefix_obj["Prefix"].split("/")[1]
            if not crawl_id:
                continue

            # Check metadata
            try:
                meta_response = s3.get_object(
                    Bucket=bucket, Key=f"crawls/{crawl_id}/_metadata.json"
                )
                meta = json.loads(meta_response["Body"].read().decode("utf-8"))
                if meta.get("domain") == domain:
                    target_crawl_id = crawl_id
                    break
            except Exception:
                if crawl_id == domain:
                    target_crawl_id = crawl_id
                    break

    if not target_crawl_id:
        raise HTTPException(status_code=404, detail="Site not found")

    # Delete all objects under crawls/{crawl_id}/
    prefix = f"crawls/{target_crawl_id}/"
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
        if objects:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": objects})

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
