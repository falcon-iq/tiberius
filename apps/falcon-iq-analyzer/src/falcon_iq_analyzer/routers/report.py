from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from falcon_iq_analyzer.routers.analyze import job_manager

router = APIRouter()


@router.get("/report/{job_id}", response_class=PlainTextResponse)
async def get_report(job_id: str) -> PlainTextResponse:
    """Download the Markdown report for a completed analysis job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.result:
        raise HTTPException(status_code=400, detail="Job not completed yet")

    return PlainTextResponse(
        content=job.result.markdown_report,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{job.result.company_name}_report.md"'},
    )
