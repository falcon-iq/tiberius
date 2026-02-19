from __future__ import annotations

import logging
import os
from collections import Counter

from falcon_iq_analyzer.cache.store import DiskCache
from falcon_iq_analyzer.config import Settings
from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.models.domain import (
    AnalysisResult,
    PageClassification,
    PageExtraction,
    PageInfo,
)
from falcon_iq_analyzer.pipeline.job_manager import JobManager
from falcon_iq_analyzer.services.classifier import classify_pages
from falcon_iq_analyzer.services.extractor import extract_pages
from falcon_iq_analyzer.services.html_cleaner import clean_page
from falcon_iq_analyzer.services.page_loader import load_pages
from falcon_iq_analyzer.services.report_generator import generate_markdown_report
from falcon_iq_analyzer.services.synthesizer import synthesize_offerings
from falcon_iq_analyzer.storage import create_storage_service

logger = logging.getLogger(__name__)


def _read_html(filepath: str, settings: Settings) -> str:
    """Read raw HTML content from local filesystem or S3."""
    if settings.storage_type == "s3":
        import boto3

        s3 = boto3.client("s3", region_name=settings.aws_region)
        response = s3.get_object(Bucket=settings.s3_bucket_name, Key=filepath)
        return response["Body"].read().decode("utf-8", errors="replace")
    else:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            return f.read()


async def run_analysis(
    crawl_directory: str,
    company_name: str,
    locale_filter: str,
    llm: LLMClient,
    settings: Settings,
    job_manager: JobManager,
    job_id: str,
) -> None:
    """Run the full 6-step analysis pipeline."""
    try:
        cache = DiskCache(crawl_directory)
        storage = create_storage_service()

        # Step 1: Load pages
        job_manager.update_status(job_id, "running", "Step 1/6: Loading pages")
        all_pages = load_pages(crawl_directory, locale_filter)
        total_pages_on_disk = len(load_pages(crawl_directory, locale_filter="__all__")) if locale_filter != "__all__" else len(all_pages)
        logger.info("Step 1: Loaded %d pages (total on disk: %d)", len(all_pages), total_pages_on_disk)

        # Step 2: Clean HTML
        job_manager.update_status(job_id, "running", f"Step 2/6: Cleaning {len(all_pages)} pages")
        cleaned_pages: list[PageInfo] = []
        for page in all_pages:
            cached = cache.get(page.filename, "clean")
            if cached:
                page.title = cached.get("title", "")
                page.meta_description = cached.get("meta_description", "")
                page.clean_text = cached.get("clean_text", "")
                cleaned_pages.append(page)
                continue

            try:
                raw_html = _read_html(page.filepath, settings)
                page = clean_page(page, raw_html, max_chars=settings.max_clean_text_chars)
                cache.set(page.filename, "clean", {
                    "title": page.title,
                    "meta_description": page.meta_description,
                    "clean_text": page.clean_text,
                })
                cleaned_pages.append(page)
            except Exception:
                logger.exception("Failed to clean %s", page.filepath)

        logger.info("Step 2: Cleaned %d pages", len(cleaned_pages))

        # Step 3: Classify pages
        job_manager.update_status(job_id, "running", f"Step 3/6: Classifying {len(cleaned_pages)} pages")
        classifications: dict[str, PageClassification] = {}
        uncached_pages: list[PageInfo] = []

        for page in cleaned_pages:
            cached = cache.get(page.filename, "classify")
            if cached:
                classifications[page.filepath] = PageClassification(**cached)
            else:
                uncached_pages.append(page)

        if uncached_pages:
            new_classifications = await classify_pages(llm, uncached_pages)
            for filepath, cls in new_classifications.items():
                classifications[filepath] = cls
                fname = next(p.filename for p in uncached_pages if p.filepath == filepath)
                cache.set(fname, "classify", cls.model_dump())

        classification_summary = Counter(c.page_type for c in classifications.values())
        logger.info("Step 3: Classification summary: %s", dict(classification_summary))

        # Step 4: Extract offerings from product/industry pages
        product_pages = [
            p for p in cleaned_pages
            if classifications.get(p.filepath, PageClassification(page_type="other", confidence=0, reasoning="")).page_type
            in ("product", "industry")
        ]
        job_manager.update_status(job_id, "running", f"Step 4/6: Extracting offerings from {len(product_pages)} pages")

        extractions: list[PageExtraction] = []
        uncached_product_pages: list[PageInfo] = []

        for page in product_pages:
            cached = cache.get(page.filename, "extract")
            if cached:
                extractions.append(PageExtraction(**cached))
            else:
                uncached_product_pages.append(page)

        if uncached_product_pages:
            new_extractions = await extract_pages(llm, uncached_product_pages)
            for ext in new_extractions:
                extractions.append(ext)
                fname = next(p.filename for p in uncached_product_pages if p.filepath == ext.filepath)
                cache.set(fname, "extract", ext.model_dump())

        logger.info("Step 4: Extracted offerings from %d pages", len(extractions))

        # Step 5: Synthesize top 5 offerings
        job_manager.update_status(job_id, "running", "Step 5/6: Synthesizing top offerings")
        non_empty = [e for e in extractions if e.offerings]
        top_offerings = await synthesize_offerings(llm, company_name, non_empty)
        logger.info("Step 5: Synthesized %d top offerings", len(top_offerings))

        # Step 6: Generate report
        job_manager.update_status(job_id, "running", "Step 6/6: Generating report")
        result = AnalysisResult(
            company_name=company_name,
            total_pages=total_pages_on_disk,
            filtered_pages=len(cleaned_pages),
            classification_summary=dict(classification_summary),
            product_pages_analyzed=len(product_pages),
            top_offerings=top_offerings,
        )
        result.markdown_report = generate_markdown_report(result)
        logger.info("Step 6: Report generated")

        # Save report and result via storage service
        report_key = f"{crawl_directory}/reports/report-{job_id}.md"
        storage.save_file(report_key, result.markdown_report, "text/markdown")
        logger.info("Report saved to %s", report_key)

        result_key = f"{crawl_directory}/reports/result-{job_id}.json"
        storage.save_file(result_key, result.model_dump_json(indent=2), "application/json")
        logger.info("Persisted analysis result to %s", result_key)

        job_manager.set_result(job_id, result)

    except Exception as e:
        logger.exception("Analysis pipeline failed")
        job_manager.set_error(job_id, str(e))
