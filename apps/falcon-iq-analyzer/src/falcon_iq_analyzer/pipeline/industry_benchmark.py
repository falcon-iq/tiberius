from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bson import ObjectId
from pymongo import MongoClient

from falcon_iq_analyzer.config import Settings
from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.industry_benchmark_prompts import (
    EXTRACT_IMPROVEMENTS_SYSTEM,
    EXTRACT_IMPROVEMENTS_USER,
    EXTRACT_KEY_FACTS_SYSTEM,
    EXTRACT_KEY_FACTS_USER,
    EXTRACT_STRENGTHS_SYSTEM,
    EXTRACT_STRENGTHS_USER,
    EXTRACT_TESTIMONIALS_SYSTEM,
    EXTRACT_TESTIMONIALS_USER,
)
from falcon_iq_analyzer.models.domain import AnalysisResult
from falcon_iq_analyzer.models.industry_benchmark import (
    CompanyImprovement,
    CompanyKeyFact,
    CompanyStrength,
    CompanyTestimonial,
    IndustryBenchmarkResult,
    IndustryCompanyResult,
)
from falcon_iq_analyzer.services.wikidata_service import fetch_company_facts
from falcon_iq_analyzer.storage import create_storage_service

logger = logging.getLogger(__name__)

DATABASE = "company_db"
INDUSTRY_BENCHMARK_CONFIG_COLLECTION = "industry_benchmark_config"
INDUSTRY_BENCHMARK_COLLECTION = "industry_benchmark"
CRAWL_DETAIL_COLLECTION = "website_crawl_detail"


def _normalize_analysis_path(raw_path: str) -> str:
    if raw_path.startswith("s3://"):
        parts = raw_path.split("/", 3)
        if len(parts) >= 4:
            key = parts[3]
            if key.startswith("analyzer/"):
                return key[len("analyzer/"):]
            return key
        return raw_path
    return raw_path


def _update_config_status(collection, config_id: str, status: str) -> None:
    collection.update_one(
        {"_id": ObjectId(config_id)},
        {"$set": {"status": status, "modifiedAt": int(time.time() * 1000)}},
    )


async def _wait_for_crawls(
    crawl_col,
    crawl_ids: list[str],
    timeout_minutes: int = 20,
    poll_interval: int = 15,
) -> None:
    """Poll MongoDB until every crawl detail has finished (COMPLETED or FAILED)."""
    deadline = time.time() + timeout_minutes * 60
    pending = set(crawl_ids)

    while pending:
        if time.time() > deadline:
            logger.warning("Timed out waiting for crawls: %s — proceeding with available data", pending)
            break

        still_pending: set[str] = set()
        for crawl_id in pending:
            try:
                doc = crawl_col.find_one({"_id": ObjectId(crawl_id)})
            except Exception:
                still_pending.add(crawl_id)
                continue

            if not doc:
                continue  # crawl detail doesn't exist, skip

            status = doc.get("status", "")
            # Terminal states — done waiting for this one
            if status in ("COMPLETED", "FAILED", "CRAWLING_COMPLETED"):
                continue
            # Still in progress
            still_pending.add(crawl_id)

        pending = still_pending
        if pending:
            logger.info("Waiting for %d crawls to finish: %s", len(pending), pending)
            await asyncio.sleep(poll_interval)

    logger.info("All crawls finished (or timed out), proceeding with extraction")


def _build_content_summary(result: AnalysisResult, max_chars: int = 6000) -> str:
    parts: list[str] = []
    for offering in result.top_offerings:
        section = f"Product: {offering.product_name}\n"
        section += f"Category: {offering.category}\n"
        section += f"Description: {offering.description}\n"
        if offering.key_features:
            section += "Features: " + ", ".join(offering.key_features) + "\n"
        if offering.key_benefits:
            section += "Benefits: " + ", ".join(offering.key_benefits) + "\n"
        if offering.target_audience:
            section += f"Target: {offering.target_audience}\n"
        parts.append(section)

    content = "\n---\n".join(parts)
    if len(content) > max_chars:
        content = content[:max_chars] + "\n[truncated]"
    return content


def _extract_logo_url(company_url: str, crawl_detail_id: str, crawled_sites_dir: str) -> str:
    """Extract logo/favicon URL from crawled homepage HTML, with Google favicon fallback."""
    domain = urlparse(company_url).netloc or urlparse(company_url).path
    fallback = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"

    if not crawl_detail_id or not crawled_sites_dir:
        return fallback

    crawl_dir = os.path.join(crawled_sites_dir, crawl_detail_id)
    if not os.path.isdir(crawl_dir):
        return fallback

    # Find the homepage HTML file (usually index_*.html or the shortest filename)
    html_files = [f for f in os.listdir(crawl_dir) if f.endswith(".html")]
    if not html_files:
        return fallback

    # Prefer index files
    homepage = None
    for f in html_files:
        if f.startswith("index"):
            homepage = f
            break
    if not homepage:
        homepage = min(html_files, key=len)

    try:
        with open(os.path.join(crawl_dir, homepage), "r", encoding="utf-8", errors="ignore") as fh:
            soup = BeautifulSoup(fh.read(), "html.parser")
    except Exception:
        return fallback

    base_url = company_url.rstrip("/")

    # Priority 1: apple-touch-icon (usually high-res PNG)
    tag = soup.find("link", rel=lambda r: r and "apple-touch-icon" in r)
    if tag and tag.get("href"):
        return urljoin(base_url, tag["href"])

    # Priority 2: icon with image type (PNG or SVG)
    for tag in soup.find_all("link", rel=lambda r: r and "icon" in r):
        href = tag.get("href", "")
        icon_type = tag.get("type", "")
        if href and ("png" in icon_type or "svg" in icon_type or href.endswith(".png") or href.endswith(".svg")):
            return urljoin(base_url, href)

    # Priority 3: any rel="icon" or rel="shortcut icon"
    tag = soup.find("link", rel=lambda r: r and "icon" in r)
    if tag and tag.get("href"):
        return urljoin(base_url, tag["href"])

    # Priority 4: og:image meta tag
    tag = soup.find("meta", property="og:image")
    if tag and tag.get("content"):
        return urljoin(base_url, tag["content"])

    return fallback


async def _extract_company_data(
    llm: LLMClient,
    company_name: str,
    company_url: str,
    content: str,
    logo_url: str = "",
) -> tuple[IndustryCompanyResult, str]:
    """Extract company data. Returns (result, facts_source) where facts_source is 'wikidata', 'llm', or 'none'."""

    # Try Wikidata first
    key_facts: list[CompanyKeyFact] = []
    facts_source = "none"
    try:
        raw_facts = await fetch_company_facts(company_name, company_url)
        key_facts = [CompanyKeyFact(**f) for f in raw_facts]
    except Exception:
        logger.exception("Failed to fetch Wikidata facts for %s", company_name)

    # Count real facts (exclude the Wikipedia link entry)
    real_fact_count = sum(1 for f in key_facts if f.label != "Wikipedia")

    if real_fact_count >= 3:
        facts_source = "wikidata"
        logger.info("Got %d facts from Wikidata for %s", real_fact_count, company_name)
    else:
        # Fall back to LLM
        logger.info("Wikidata returned only %d facts for %s, falling back to LLM", real_fact_count, company_name)
        try:
            llm_facts_data = await llm.complete_json(
                EXTRACT_KEY_FACTS_SYSTEM,
                EXTRACT_KEY_FACTS_USER.format(
                    company_name=company_name, company_url=company_url
                ),
            )
            llm_facts = [CompanyKeyFact(**f) for f in llm_facts_data.get("key_facts", [])]
            # Mark LLM facts with source
            for f in llm_facts:
                if not f.source:
                    f.source = "LLM estimate"
            # Merge: keep Wikidata facts, fill gaps with LLM facts
            existing_labels = {f.label for f in key_facts}
            for f in llm_facts:
                if f.label not in existing_labels:
                    key_facts.append(f)
                    existing_labels.add(f.label)
            facts_source = "wikidata+llm" if real_fact_count > 0 else "llm"
            logger.info(
                "After LLM fallback: %d total facts for %s (source: %s)",
                len(key_facts),
                company_name,
                facts_source,
            )
        except Exception:
            logger.exception("LLM key facts fallback also failed for %s", company_name)
            if real_fact_count > 0:
                facts_source = "wikidata"

    strengths_data = await llm.complete_json(
        EXTRACT_STRENGTHS_SYSTEM,
        EXTRACT_STRENGTHS_USER.format(
            company_name=company_name, company_url=company_url, content=content
        ),
    )
    strengths = [CompanyStrength(**s) for s in strengths_data.get("strengths", [])]

    improvements_data = await llm.complete_json(
        EXTRACT_IMPROVEMENTS_SYSTEM,
        EXTRACT_IMPROVEMENTS_USER.format(
            company_name=company_name, company_url=company_url, content=content
        ),
    )
    improvements = [CompanyImprovement(**i) for i in improvements_data.get("improvements", [])]

    testimonials_data = await llm.complete_json(
        EXTRACT_TESTIMONIALS_SYSTEM,
        EXTRACT_TESTIMONIALS_USER.format(
            company_name=company_name, company_url=company_url, content=content
        ),
    )
    testimonials = [CompanyTestimonial(**t) for t in testimonials_data.get("testimonials", [])]

    return IndustryCompanyResult(
        company_name=company_name,
        company_url=company_url,
        logo_url=logo_url,
        key_facts=key_facts[:6],
        strengths=strengths[:3],
        improvements=improvements[:2],
        testimonials=testimonials[:2],
    ), facts_source


async def run_industry_benchmark(
    slug: str,
    companies: list[dict],
    llm: LLMClient,
    settings: Settings,
) -> None:
    client: MongoClient | None = None
    try:
        client = MongoClient(settings.mongo_uri)
        db = client[DATABASE]
        config_col = db[INDUSTRY_BENCHMARK_CONFIG_COLLECTION]
        benchmark_col = db[INDUSTRY_BENCHMARK_COLLECTION]
        crawl_col = db[CRAWL_DETAIL_COLLECTION]
        storage = create_storage_service()

        config_doc = config_col.find_one({"slug": slug})
        if not config_doc:
            logger.error("Config not found for slug: %s", slug)
            return

        config_id = str(config_doc["_id"])
        industry_name = config_doc["industryName"]
        country = config_doc["country"]

        _update_config_status(config_col, config_id, "GENERATING")

        company_results: list[IndustryCompanyResult] = []
        facts_sources: dict[str, str] = {}  # company_name → "wikidata" | "llm" | "wikidata+llm" | "none"

        for company in companies:
            company_name = company["name"]
            company_url = company["url"]
            crawl_detail_id = company.get("crawlDetailId")

            logger.info("Processing company: %s (%s)", company_name, company_url)

            content = ""
            if crawl_detail_id:
                crawl_doc = crawl_col.find_one({"_id": ObjectId(crawl_detail_id)})
                if crawl_doc and crawl_doc.get("analysisResultsPath"):
                    storage_key = _normalize_analysis_path(crawl_doc["analysisResultsPath"])
                    raw_json = storage.load_file(storage_key)
                    if raw_json:
                        result_data = json.loads(raw_json)
                        analysis_result = AnalysisResult(**result_data)
                        content = _build_content_summary(analysis_result)

            if not content:
                content = f"Company: {company_name}\nWebsite: {company_url}\n(No detailed analysis data available)"

            logo_url = _extract_logo_url(
                company_url,
                crawl_detail_id or "",
                settings.crawled_sites_dir if hasattr(settings, 'crawled_sites_dir') else "",
            )

            try:
                result, facts_source = await _extract_company_data(
                    llm, company_name, company_url, content, logo_url=logo_url
                )
                company_results.append(result)
                facts_sources[company_name] = facts_source
                logger.info("Completed extraction for %s (facts: %s)", company_name, facts_source)
            except Exception:
                logger.exception("Failed to extract data for %s", company_name)
                company_results.append(
                    IndustryCompanyResult(company_name=company_name, company_url=company_url)
                )
                facts_sources[company_name] = "none"

        benchmark_result = IndustryBenchmarkResult(
            industry_name=industry_name,
            country=country,
            slug=slug,
            companies=company_results,
        )

        benchmark_doc = {
            "industryName": industry_name,
            "country": country,
            "slug": slug,
            "status": "COMPLETED",
            "generatedAt": int(time.time() * 1000),
            "companies": [
                {
                    "companyName": c.company_name,
                    "companyUrl": c.company_url,
                    "logoUrl": c.logo_url,
                    "factsSource": facts_sources.get(c.company_name, "none"),
                    "keyFacts": [
                        {"label": f.label, "value": f.value, "source": f.source, "sourceUrl": f.source_url}
                        for f in c.key_facts
                    ],
                    "strengths": [{"title": s.title, "detail": s.detail} for s in c.strengths],
                    "improvements": [{"title": i.title, "detail": i.detail} for i in c.improvements],
                    "testimonials": [
                        {"quote": t.quote, "source": t.source, "authorRole": t.author_role}
                        for t in c.testimonials
                    ],
                }
                for c in company_results
            ],
            "createdAt": int(time.time() * 1000),
            "modifiedAt": int(time.time() * 1000),
        }

        existing = benchmark_col.find_one({"slug": slug})
        if existing:
            benchmark_col.update_one({"slug": slug}, {"$set": benchmark_doc})
            logger.info("Updated existing industry benchmark for %s", slug)
        else:
            benchmark_col.insert_one(benchmark_doc)
            logger.info("Created new industry benchmark for %s", slug)

        # Update config with completion status and facts source details
        config_col.update_one(
            {"_id": ObjectId(config_id)},
            {"$set": {
                "status": "COMPLETED",
                "factsSources": facts_sources,
                "modifiedAt": int(time.time() * 1000),
            }},
        )

        result_key = f"industry-benchmarks/{slug}.json"
        storage.save_file(
            result_key,
            benchmark_result.model_dump_json(indent=2),
            "application/json",
        )
        logger.info("Industry benchmark %s completed successfully", slug)

    except Exception as e:
        logger.exception("Industry benchmark pipeline failed for %s", slug)
        if client:
            try:
                col = client[DATABASE][INDUSTRY_BENCHMARK_CONFIG_COLLECTION]
                config_doc = col.find_one({"slug": slug})
                if config_doc:
                    _update_config_status(col, str(config_doc["_id"]), "FAILED")

                bench_col = client[DATABASE][INDUSTRY_BENCHMARK_COLLECTION]
                bench_col.update_one(
                    {"slug": slug},
                    {"$set": {"status": "FAILED", "errorMessage": str(e), "modifiedAt": int(time.time() * 1000)}},
                    upsert=True,
                )
            except Exception:
                logger.exception("Failed to update status to FAILED")
    finally:
        if client:
            client.close()
