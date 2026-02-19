from fastapi import APIRouter, HTTPException

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.llm.factory import create_llm_client
from falcon_iq_analyzer.models.requests import CompareRequest
from falcon_iq_analyzer.models.responses import CompareResponse
from falcon_iq_analyzer.routers.analyze import job_manager
from falcon_iq_analyzer.services.comparator import compare_companies

router = APIRouter()


@router.post("/compare", response_model=CompareResponse)
async def compare(request: CompareRequest) -> CompareResponse:
    """Compare two completed analysis jobs."""
    job_a = job_manager.get_job(request.job_id_a)
    job_b = job_manager.get_job(request.job_id_b)

    if not job_a or not job_b:
        raise HTTPException(status_code=404, detail="One or both job IDs not found")
    if job_a.status != "completed" or job_b.status != "completed":
        raise HTTPException(status_code=400, detail="Both jobs must be completed before comparing")
    if not job_a.result or not job_b.result:
        raise HTTPException(status_code=400, detail="Both jobs must have results")

    llm = create_llm_client(settings)
    result = await compare_companies(llm, job_a.result, job_b.result)
    return CompareResponse(comparison=result)
