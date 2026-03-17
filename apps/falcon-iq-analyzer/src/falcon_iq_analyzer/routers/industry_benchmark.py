import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.llm.factory import create_llm_client
from falcon_iq_analyzer.pipeline.industry_benchmark import run_industry_benchmark

logger = logging.getLogger(__name__)

router = APIRouter()


class IndustryCompanyInput(BaseModel):
    name: str
    url: str
    crawlDetailId: str = ""


class IndustryBenchmarkRequest(BaseModel):
    slug: str
    companies: list[IndustryCompanyInput]


class IndustryBenchmarkResponse(BaseModel):
    slug: str
    status: str
    message: str = ""


@router.post("/industry-benchmark", response_model=IndustryBenchmarkResponse, status_code=202)
async def start_industry_benchmark(request: IndustryBenchmarkRequest) -> IndustryBenchmarkResponse:
    """Start an industry benchmark pipeline for the given companies."""
    if not request.slug:
        raise HTTPException(status_code=400, detail="slug is required")
    if not request.companies:
        raise HTTPException(status_code=400, detail="companies list is required")

    llm = create_llm_client(settings)
    companies_data = [
        {"name": c.name, "url": c.url, "crawlDetailId": c.crawlDetailId}
        for c in request.companies
    ]

    asyncio.create_task(
        run_industry_benchmark(
            slug=request.slug,
            companies=companies_data,
            llm=llm,
            settings=settings,
        )
    )

    return IndustryBenchmarkResponse(
        slug=request.slug,
        status="IN_PROGRESS",
        message=f"Industry benchmark started for {len(request.companies)} companies",
    )
