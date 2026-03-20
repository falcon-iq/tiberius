import asyncio
import logging

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pymongo import MongoClient

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.llm.factory import create_llm_client
from falcon_iq_analyzer.models.requests import CompanyBenchmarkRequest
from falcon_iq_analyzer.models.responses import CompanyBenchmarkJobResponse
from falcon_iq_analyzer.pipeline.company_benchmark import (
    _normalize_analysis_path,
    run_company_benchmark,
)
from falcon_iq_analyzer.storage import create_storage_service

logger = logging.getLogger(__name__)

router = APIRouter()

DATABASE = "company_db"
BENCHMARK_REPORT_COLLECTION = "company_benchmark_report"
CRAWL_DETAIL_COLLECTION = "website_crawl_detail"


@router.post("/company-benchmark", response_model=CompanyBenchmarkJobResponse, status_code=202)
async def start_company_benchmark(request: CompanyBenchmarkRequest) -> CompanyBenchmarkJobResponse:
    """Start an N-company benchmark from a CompanyBenchmarkReport document in MongoDB."""
    if not settings.mongo_uri:
        raise HTTPException(status_code=503, detail="MongoDB not configured")

    client: MongoClient | None = None
    try:
        client = MongoClient(settings.mongo_uri)
        db = client[DATABASE]
        report_col = db[BENCHMARK_REPORT_COLLECTION]
        crawl_col = db[CRAWL_DETAIL_COLLECTION]

        # Validate report exists
        report_doc = report_col.find_one({"_id": ObjectId(request.companyBenchmarkReportId)})
        if not report_doc:
            raise HTTPException(
                status_code=404,
                detail=f"CompanyBenchmarkReport {request.companyBenchmarkReportId} not found",
            )

        # Validate all crawl details exist
        main_crawl_id = report_doc["companyCrawlDetailId"]
        competitor_crawl_ids = report_doc.get("competitionCrawlDetailIds", [])
        all_crawl_ids = [main_crawl_id] + list(competitor_crawl_ids)

        for crawl_id in all_crawl_ids:
            crawl_doc = crawl_col.find_one({"_id": ObjectId(crawl_id)})
            if not crawl_doc:
                raise HTTPException(
                    status_code=400,
                    detail=f"WebsiteCrawlDetail {crawl_id} not found",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to validate company benchmark request")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if client:
            client.close()

    # Launch background task
    num_prompts = request.num_prompts if request.num_prompts is not None else settings.benchmark_num_prompts
    llm = create_llm_client(settings)
    asyncio.create_task(
        run_company_benchmark(
            company_benchmark_report_id=request.companyBenchmarkReportId,
            num_prompts=num_prompts,
            llm=llm,
            settings=settings,
        )
    )

    return CompanyBenchmarkJobResponse(
        companyBenchmarkReportId=request.companyBenchmarkReportId,
        status="BENCHMARK_REPORT_IN_PROGRESS",
        message=f"Benchmark started for {len(all_crawl_ids)} companies with {num_prompts} prompts",
    )


@router.get("/company-benchmark-report/{report_id}/report", response_class=HTMLResponse)
async def get_benchmark_html_report(report_id: str) -> HTMLResponse:
    """Serve the generated HTML benchmark report."""
    if not settings.mongo_uri:
        raise HTTPException(status_code=503, detail="MongoDB not configured")

    client: MongoClient | None = None
    try:
        client = MongoClient(settings.mongo_uri)
        db = client[DATABASE]
        report_col = db[BENCHMARK_REPORT_COLLECTION]

        report_doc = report_col.find_one({"_id": ObjectId(report_id)})
        if not report_doc:
            raise HTTPException(status_code=404, detail="Report not found")

        html_report_url = report_doc.get("htmlReportUrl")
        if not html_report_url:
            raise HTTPException(status_code=404, detail="HTML report not yet available")

        storage_key = _normalize_analysis_path(html_report_url)
        storage = create_storage_service()
        html_content = storage.load_file(storage_key)

        if not html_content:
            raise HTTPException(status_code=404, detail="HTML report file not found in storage")

        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to serve HTML report for %s", report_id)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if client:
            client.close()
