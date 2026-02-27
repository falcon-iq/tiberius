import asyncio
import os
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.llm.factory import create_llm_client
from falcon_iq_analyzer.models.requests import AnalyzeRequest, AnalyzeWebsiteRequest
from falcon_iq_analyzer.models.responses import JobStatus
from falcon_iq_analyzer.pipeline.analyzer import run_analysis
from falcon_iq_analyzer.pipeline.job_manager import JobManager
from falcon_iq_analyzer.services.progress_reporter import AnalysisProgressReporter

router = APIRouter()
job_manager = JobManager()
job_manager.load_persisted_results()


class CompletedAnalysis(BaseModel):
    job_id: str
    company_name: str
    crawl_directory: Optional[str] = None
    domain: Optional[str] = None
    created_at: Optional[str] = None
    total_pages: int = 0
    product_pages_analyzed: int = 0


@router.get("/analyses", response_model=List[CompletedAnalysis])
async def list_completed_analyses() -> List[CompletedAnalysis]:
    """List all completed analysis jobs (persisted across restarts)."""
    return [
        CompletedAnalysis(
            job_id=j.job_id,
            company_name=j.result.company_name,
            crawl_directory=j.crawl_directory,
            domain=j.domain,
            created_at=j.created_at,
            total_pages=j.result.total_pages,
            product_pages_analyzed=j.result.product_pages_analyzed,
        )
        for j in job_manager.list_completed()
    ]


@router.post("/analyze", response_model=JobStatus)
async def start_analysis(request: AnalyzeRequest) -> JobStatus:
    """Start a background analysis job."""
    job = job_manager.create_job()
    job.domain = request.domain
    llm = create_llm_client(settings)

    asyncio.create_task(
        run_analysis(
            crawl_directory=request.crawl_directory,
            company_name=request.company_name,
            locale_filter=request.locale_filter,
            llm=llm,
            settings=settings,
            job_manager=job_manager,
            job_id=job.job_id,
        )
    )

    return JobStatus(job_id=job.job_id, status="pending", progress="Job queued")


@router.post("/analyze-website", response_model=JobStatus, status_code=202)
async def start_website_analysis(request: AnalyzeWebsiteRequest) -> JobStatus:
    """Start analysis triggered by crawler, with MongoDB progress reporting."""
    parsed = urlparse(request.url)
    company_name = parsed.hostname or request.url
    if company_name.startswith("www."):
        company_name = company_name[4:]

    # Extract crawl ID from the crawler's path:
    #   Local: "crawled_pages/<id>"  →  "<id>"
    #   S3:    "s3://bucket/crawls/<id>"  →  "<id>"
    crawled_pages_path = request.crawled_pages_path
    crawl_id = Path(crawled_pages_path).name

    if settings.storage_type == "local":
        crawl_directory = os.path.join(settings.crawled_sites_dir, crawl_id)
    else:
        # S3 mode: load_pages_from_s3 expects just the crawl ID
        crawl_directory = crawl_id

    reporter = AnalysisProgressReporter(settings.mongo_uri)
    reporter.report_analyzer_in_progress(request.websiteCrawlDetailId)

    job = job_manager.create_job()
    job.domain = company_name
    llm = create_llm_client(settings)

    asyncio.create_task(
        run_analysis(
            crawl_directory=crawl_directory,
            company_name=company_name,
            locale_filter=request.locale_filter,
            llm=llm,
            settings=settings,
            job_manager=job_manager,
            job_id=job.job_id,
            progress_reporter=reporter,
            website_crawl_detail_id=request.websiteCrawlDetailId,
            crawled_pages_path=request.crawled_pages_path,
        )
    )

    return JobStatus(job_id=job.job_id, status="pending", progress="Job queued")


@router.get("/analyze/{job_id}", response_model=JobStatus)
async def get_analysis_status(job_id: str) -> JobStatus:
    """Check the status of an analysis job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        result=job.result,
        error=job.error,
    )


@router.delete("/analyses/{job_id}")
async def delete_analysis(job_id: str) -> dict:
    """Delete a completed analysis and its persisted files."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Delete persisted files — try via storage service (handles both local and S3)
    from falcon_iq_analyzer.storage import create_storage_service

    storage = create_storage_service()

    # The persisted files are at {crawl_directory}/reports/result-{job_id}.json
    # relative to the storage base_dir. Try to find and delete them.
    try:
        result_files = storage.list_files(f"*/reports/result-{job_id}.json")
        report_files = storage.list_files(f"*/reports/report-{job_id}.md")
        for rel_path in result_files + report_files:
            full_path = os.path.join(settings.results_dir, rel_path)
            if os.path.isfile(full_path):
                os.remove(full_path)
    except Exception:
        pass  # Best effort — job is still removed from memory

    job_manager.delete_job(job_id)
    return {"status": "deleted", "job_id": job_id}
