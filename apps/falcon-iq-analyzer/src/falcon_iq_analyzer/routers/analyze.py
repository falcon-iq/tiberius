import asyncio
from typing import List

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


@router.get("/analyses", response_model=List[CompletedAnalysis])
async def list_completed_analyses() -> List[CompletedAnalysis]:
    """List all completed analysis jobs (persisted across restarts)."""
    return [
        CompletedAnalysis(job_id=j.job_id, company_name=j.result.company_name)
        for j in job_manager.list_completed()
    ]


@router.post("/analyze", response_model=JobStatus)
async def start_analysis(request: AnalyzeRequest) -> JobStatus:
    """Start a background analysis job."""
    job = job_manager.create_job()
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
