import asyncio
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.llm.factory import create_llm_client
from falcon_iq_analyzer.models.requests import AnalyzeRequest
from falcon_iq_analyzer.models.responses import JobStatus
from falcon_iq_analyzer.pipeline.analyzer import run_analysis
from falcon_iq_analyzer.pipeline.job_manager import JobManager

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
