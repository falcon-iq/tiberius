from __future__ import annotations

import asyncio
import json
import logging
import time

from bson import ObjectId
from pymongo import MongoClient

from falcon_iq_analyzer.config import Settings
from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.models.company_benchmark import MultiCompanyBenchmarkResult
from falcon_iq_analyzer.models.domain import AnalysisResult
from falcon_iq_analyzer.services.html_report_generator import generate_html_report
from falcon_iq_analyzer.services.multi_benchmark_service import (
    evaluate_single_prompt_multi,
    generate_multi_benchmark_report,
    generate_multi_prompts,
    summarize_multi_evaluations,
)
from falcon_iq_analyzer.storage import create_storage_service

logger = logging.getLogger(__name__)

DATABASE = "company_db"
BENCHMARK_REPORT_COLLECTION = "company_benchmark_report"
CRAWL_DETAIL_COLLECTION = "website_crawl_detail"


def _normalize_analysis_path(raw_path: str) -> str:
    """Convert MongoDB-stored analysis path to a storage key.

    MongoDB stores paths like ``crawled_pages/<crawl_id>/reports/result-<job_id>.json``
    or S3 URIs like ``s3://bucket/analyzer/<key>``.  The storage service expects a
    relative key such as ``<crawl_id>/reports/result-<job_id>.json``.
    """
    if raw_path.startswith("s3://"):
        # Extract the key after the analyzer/ prefix
        parts = raw_path.split("/", 3)  # s3: // bucket / rest
        if len(parts) >= 4:
            key = parts[3]
            # Strip analyzer/ prefix if present (S3StorageService adds it back)
            if key.startswith("analyzer/"):
                return key[len("analyzer/"):]
            return key
        return raw_path

    # Local path: strip leading "crawled_pages/" if present
    if raw_path.startswith("crawled_pages/"):
        return raw_path[len("crawled_pages/"):]
    return raw_path


def _update_benchmark_status(collection, report_id: str, status: str, extra: dict | None = None) -> None:
    """Update the CompanyBenchmarkReport status in MongoDB."""
    update: dict = {"status": status, "modifiedAt": int(time.time() * 1000)}
    if extra:
        update.update(extra)
    collection.update_one({"_id": ObjectId(report_id)}, {"$set": update})


async def _wait_for_analyses(
    crawl_col,
    crawl_ids: list[str],
    timeout_minutes: int = 30,
    poll_interval: int = 10,
) -> None:
    """Poll MongoDB until every crawl detail has an analysisResultsPath (or fail)."""
    deadline = time.time() + timeout_minutes * 60
    pending = set(crawl_ids)

    while pending:
        if time.time() > deadline:
            raise ValueError(
                f"Timed out after {timeout_minutes}m waiting for analyses: {pending}"
            )

        still_pending: set[str] = set()
        for crawl_id in pending:
            doc = crawl_col.find_one({"_id": ObjectId(crawl_id)})
            if not doc:
                raise ValueError(f"WebsiteCrawlDetail {crawl_id} not found")
            if doc.get("status") == "FAILED":
                raise ValueError(f"WebsiteCrawlDetail {crawl_id} analysis failed")
            if not doc.get("analysisResultsPath"):
                still_pending.add(crawl_id)

        pending = still_pending
        if pending:
            logger.info("Waiting for %d analyses to complete: %s", len(pending), pending)
            await asyncio.sleep(poll_interval)

    logger.info("All %d analyses ready", len(crawl_ids))


async def run_company_benchmark(
    company_benchmark_report_id: str,
    num_prompts: int,
    llm: LLMClient,
    settings: Settings,
) -> None:
    """Run the full N-company benchmark pipeline."""
    client: MongoClient | None = None
    try:
        client = MongoClient(settings.mongo_uri)
        db = client[DATABASE]
        report_col = db[BENCHMARK_REPORT_COLLECTION]
        crawl_col = db[CRAWL_DETAIL_COLLECTION]
        storage = create_storage_service()

        # 1. Read the CompanyBenchmarkReport document
        report_doc = report_col.find_one({"_id": ObjectId(company_benchmark_report_id)})
        if not report_doc:
            logger.error("CompanyBenchmarkReport %s not found", company_benchmark_report_id)
            return

        # 2. Update status → BENCHMARK_REPORT_IN_PROGRESS
        _update_benchmark_status(report_col, company_benchmark_report_id, "BENCHMARK_REPORT_IN_PROGRESS")

        # 3. Gather all crawl detail IDs (main + competitors)
        main_crawl_id = report_doc["companyCrawlDetailId"]
        competitor_crawl_ids = report_doc.get("competitionCrawlDetailIds", [])
        all_crawl_ids = [main_crawl_id] + list(competitor_crawl_ids)

        # 4. Wait for all individual analyses to finish (they run in parallel)
        await _wait_for_analyses(crawl_col, all_crawl_ids, timeout_minutes=30)

        # 5. Load analysis results for each crawl detail
        analysis_results: list[AnalysisResult] = []
        for crawl_id in all_crawl_ids:
            crawl_doc = crawl_col.find_one({"_id": ObjectId(crawl_id)})
            if not crawl_doc:
                raise ValueError(f"WebsiteCrawlDetail {crawl_id} not found")

            analysis_path = crawl_doc.get("analysisResultsPath")
            if not analysis_path:
                raise ValueError(f"WebsiteCrawlDetail {crawl_id} has no analysisResultsPath")

            storage_key = _normalize_analysis_path(analysis_path)
            raw_json = storage.load_file(storage_key)
            if not raw_json:
                raise ValueError(f"Analysis result not found at {storage_key}")

            result_data = json.loads(raw_json)
            analysis_results.append(AnalysisResult(**result_data))

        main_result = analysis_results[0]
        competitor_results = analysis_results[1:]
        all_company_names = [r.company_name for r in analysis_results]

        logger.info(
            "Company benchmark: main=%s, competitors=%s",
            main_result.company_name,
            [r.company_name for r in competitor_results],
        )

        # 6. Generate prompts
        prompts = await generate_multi_prompts(llm, main_result, competitor_results, num_prompts)
        logger.info("Company benchmark: generated %d prompts", len(prompts))

        # 7. Evaluate each prompt sequentially
        evaluations = []
        for i, prompt in enumerate(prompts):
            evaluation = await evaluate_single_prompt_multi(llm, prompt, all_company_names)
            evaluations.append(evaluation)
            logger.info(
                "Company benchmark: evaluated prompt %d/%d — winner: %s",
                i + 1,
                len(prompts),
                evaluation.winner,
            )

        # 8. Summarize
        summary = await summarize_multi_evaluations(llm, all_company_names, evaluations)
        logger.info("Company benchmark: summary complete")

        # 9. Generate markdown report
        benchmark_result = MultiCompanyBenchmarkResult(
            main_company=main_result.company_name,
            competitors=[r.company_name for r in competitor_results],
            prompts=prompts,
            evaluations=evaluations,
            summary=summary,
        )
        benchmark_result.markdown_report = generate_multi_benchmark_report(benchmark_result)

        # 10. Save to storage (MD, JSON, and HTML)
        report_key = f"company-benchmarks/benchmark-{company_benchmark_report_id}.md"
        storage.save_file(report_key, benchmark_result.markdown_report, "text/markdown")
        logger.info("Company benchmark report saved to %s", report_key)

        result_key = f"company-benchmarks/benchmark-{company_benchmark_report_id}.json"
        storage.save_file(
            result_key, benchmark_result.model_dump_json(indent=2), "application/json"
        )
        logger.info("Persisted company benchmark result to %s", result_key)

        html_key = f"company-benchmarks/benchmark-{company_benchmark_report_id}.html"
        html_content = generate_html_report(benchmark_result)
        storage.save_file(html_key, html_content, "text/html")
        logger.info("HTML benchmark report saved to %s", html_key)

        # 11. Update MongoDB: set reportUrl and htmlReportUrl, status → COMPLETED
        # Store storage keys (not full paths) so load_file can resolve them.
        _update_benchmark_status(
            report_col,
            company_benchmark_report_id,
            "COMPLETED",
            extra={"reportUrl": result_key, "htmlReportUrl": html_key},
        )
        logger.info("Company benchmark %s completed successfully", company_benchmark_report_id)

    except Exception as e:
        logger.exception("Company benchmark pipeline failed for %s", company_benchmark_report_id)
        if client:
            try:
                col = client[DATABASE][BENCHMARK_REPORT_COLLECTION]
                _update_benchmark_status(
                    col,
                    company_benchmark_report_id,
                    "FAILED",
                    extra={"errorMessage": str(e)},
                )
            except Exception:
                logger.exception("Failed to update status to FAILED")
    finally:
        if client:
            client.close()
