from __future__ import annotations

import asyncio
import json
import logging
import time
from urllib.parse import urlparse

from bson import ObjectId
from pymongo import MongoClient

from falcon_iq_analyzer.config import Settings
from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.models.company_benchmark import (
    CompanyOfferingSummary,
    CompanyOverview,
    MultiCompanyBenchmarkResult,
)
from falcon_iq_analyzer.models.domain import AnalysisResult
from falcon_iq_analyzer.models.enrichment import EnrichedCompanyProfile
from falcon_iq_analyzer.services.enrichment import fetch_all_enrichments, verify_claims
from falcon_iq_analyzer.services.html_report_generator import generate_html_report
from falcon_iq_analyzer.services.multi_benchmark_service import (
    evaluate_single_prompt_multi,
    generate_multi_benchmark_report,
    generate_multi_prompts,
    normalize_product_categories,
    summarize_multi_evaluations,
)
from falcon_iq_analyzer.services.wikidata_service import fetch_company_tagline
from falcon_iq_analyzer.storage import create_storage_service

logger = logging.getLogger(__name__)

DATABASE = "company_db"
BENCHMARK_REPORT_COLLECTION = "company_benchmark_report"
CRAWL_DETAIL_COLLECTION = "website_crawl_detail"


def _normalize_analysis_path(raw_path: str) -> str:
    """Convert MongoDB-stored analysis path to a storage key.

    The storage service saves files with a relative key (e.g.
    ``crawled_pages/<crawl_id>/reports/result-<job_id>.json``).
    S3StorageService prepends ``analyzer/`` internally, so we just
    need to return the key as-is for local paths.

    For S3 URIs (``s3://bucket/analyzer/<key>``), strip the bucket
    and ``analyzer/`` prefix to recover the original key.
    """
    if raw_path.startswith("s3://"):
        # Extract the key after the analyzer/ prefix
        parts = raw_path.split("/", 3)  # s3: // bucket / rest
        if len(parts) >= 4:
            key = parts[3]
            # Strip analyzer/ prefix if present (S3StorageService adds it back)
            if key.startswith("analyzer/"):
                return key[len("analyzer/") :]
            return key
        return raw_path

    # Local or mixed-storage path: return as-is (the storage service
    # uses this key directly, including any crawled_pages/ prefix)
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
            raise ValueError(f"Timed out after {timeout_minutes}m waiting for analyses: {pending}")

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

        # 5. Load analysis results and company URLs for each crawl detail
        analysis_results: list[AnalysisResult] = []
        company_urls: dict[str, str] = {}  # company_name → websiteLink
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
            ar = AnalysisResult(**result_data)
            analysis_results.append(ar)

            # Extract URL from crawl doc
            website_link = crawl_doc.get("websiteLink", "")
            if website_link:
                company_urls[ar.company_name] = website_link

        main_result = analysis_results[0]
        competitor_results = analysis_results[1:]
        all_company_names = [r.company_name for r in analysis_results]

        # Build company overviews (favicon, URL, categories, offerings)
        company_overviews: dict[str, CompanyOverview] = {}
        for ar in analysis_results:
            url = company_urls.get(ar.company_name, "")
            domain = urlparse(url).netloc if url else ""
            logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128" if domain else ""
            categories = sorted({o.category for o in ar.top_offerings if o.category})
            offerings = [
                CompanyOfferingSummary(
                    product_name=o.product_name,
                    category=o.category,
                    description=o.description[:200],
                    key_features=o.key_features[:5],
                )
                for o in ar.top_offerings[:3]
            ]
            company_overviews[ar.company_name] = CompanyOverview(
                company_name=ar.company_name,
                url=url,
                logo_url=logo_url,
                categories=categories,
                top_offerings=offerings,
            )

        # 5b. Fetch Wikipedia taglines in parallel
        async def _fill_tagline(name: str) -> None:
            tagline = await fetch_company_tagline(name)
            if tagline:
                company_overviews[name].tagline = tagline

        await asyncio.gather(*[_fill_tagline(name) for name in company_overviews])
        logger.info(
            "Company benchmark: fetched taglines for %d companies",
            sum(1 for ov in company_overviews.values() if ov.tagline),
        )

        # 5c. External enrichment (G2, Crunchbase, Google Search via crawler)
        enriched_profiles: dict[str, EnrichedCompanyProfile] = {}
        if settings.enrichment_enabled:
            enrichment_summary: dict = {"status": "FAILED", "companiesAttempted": len(company_overviews)}
            try:
                _update_benchmark_status(report_col, company_benchmark_report_id, "ENRICHMENT_IN_PROGRESS")
                logger.info("Company benchmark: starting external enrichment for %d companies", len(company_overviews))

                enrichment_results = await fetch_all_enrichments(company_overviews, settings.crawler_api_url)

                per_company: dict = {}
                for name, enrichment in enrichment_results.items():
                    company_overviews[name].enrichment = enrichment
                    claims = [o.description for o in company_overviews[name].top_offerings if o.description]
                    try:
                        verified = await verify_claims(llm, name, claims, enrichment)
                    except Exception:
                        logger.warning("Claim verification failed for %s — skipping", name, exc_info=True)
                        verified = []
                    company_overviews[name].verified_claims = verified
                    enriched_profiles[name] = EnrichedCompanyProfile(
                        company_name=name,
                        enrichment=enrichment,
                        verified_claims=verified,
                    )
                    per_company[name] = {
                        "g2": enrichment.g2 is not None,
                        "g2Rating": enrichment.g2.rating if enrichment.g2 else None,
                        "companyData": enrichment.crunchbase is not None,
                        "reviewSites": len(enrichment.review_sites),
                        "googleInsights": len(enrichment.google_insights),
                        "verifiedClaims": len(verified),
                    }

                enrichment_summary = {
                    "status": "COMPLETED",
                    "companiesAttempted": len(company_overviews),
                    "companiesEnriched": len(enriched_profiles),
                    "totalVerifiedClaims": sum(len(p.verified_claims) for p in enriched_profiles.values()),
                    "perCompany": per_company,
                }
                logger.info(
                    "Company benchmark: enrichment complete — %d/%d companies enriched, %d total verified claims",
                    len(enriched_profiles),
                    len(company_overviews),
                    enrichment_summary["totalVerifiedClaims"],
                )
            except Exception as exc:
                logger.exception("Company benchmark: enrichment failed — continuing without enrichment data")
                enrichment_summary["error"] = str(exc)

            _update_benchmark_status(
                report_col,
                company_benchmark_report_id,
                "BENCHMARK_REPORT_IN_PROGRESS",
                extra={"enrichment": enrichment_summary},
            )

        logger.info(
            "Company benchmark: main=%s, competitors=%s",
            main_result.company_name,
            [r.company_name for r in competitor_results],
        )

        # 6. Generate prompts (with enrichment context when available)
        prompts = await generate_multi_prompts(llm, main_result, competitor_results, num_prompts, company_overviews)
        logger.info("Company benchmark: generated %d prompts", len(prompts))

        # 7. Evaluate each prompt sequentially (with real company data as context)
        evaluations = []
        for i, prompt in enumerate(prompts):
            evaluation = await evaluate_single_prompt_multi(llm, prompt, all_company_names, company_overviews)
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

        # 8b. Normalize product categories for comparison table
        product_groups = await normalize_product_categories(llm, company_overviews)
        logger.info("Company benchmark: product category normalization complete (%d groups)", len(product_groups))

        # 9. Generate markdown report
        benchmark_result = MultiCompanyBenchmarkResult(
            main_company=main_result.company_name,
            competitors=[r.company_name for r in competitor_results],
            company_overviews=company_overviews,
            prompts=prompts,
            evaluations=evaluations,
            summary=summary,
            product_comparison_groups=product_groups,
            enriched_profiles=enriched_profiles,
        )
        benchmark_result.markdown_report = generate_multi_benchmark_report(benchmark_result)

        # 10. Save to storage (MD, JSON, and HTML)
        report_key = f"company-benchmarks/benchmark-{company_benchmark_report_id}.md"
        storage.save_file(report_key, benchmark_result.markdown_report, "text/markdown")
        logger.info("Company benchmark report saved to %s", report_key)

        result_key = f"company-benchmarks/benchmark-{company_benchmark_report_id}.json"
        storage.save_file(result_key, benchmark_result.model_dump_json(indent=2), "application/json")
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

        # 12. Send email notification
        try:
            recipient_email = report_doc.get("userId", "")
            if recipient_email and settings.notification_enabled and settings.ses_sender_email:
                from datetime import datetime, timezone
                from pathlib import Path

                from falconiq_notifications import send_templated_email

                # Build report URL (CDN link to the HTML report in storage)
                report_url = f"https://cdn.trymarketpilot.com/analyzer/{html_key}"

                # Gather template data from the benchmark result
                all_companies_list = [benchmark_result.main_company] + benchmark_result.competitors
                winner_name = ""
                winner_wins = 0
                if benchmark_result.summary:
                    for stat in benchmark_result.summary.company_stats:
                        if stat.wins > winner_wins:
                            winner_wins = stat.wins
                            winner_name = stat.company_name

                total = benchmark_result.summary.total_prompts if benchmark_result.summary else len(evaluations)
                winner_pct = round(winner_wins / max(total, 1) * 100)

                templates_dir = Path(__file__).resolve().parents[5] / "libs" / "notifications" / "templates"

                await send_templated_email(
                    to=recipient_email,
                    template_name="benchmark_complete",
                    template_data={
                        "recipient_name": report_doc.get("companyName", "there"),
                        "main_company": benchmark_result.main_company,
                        "competitors": benchmark_result.competitors,
                        "total_prompts": total,
                        "num_companies": len(all_companies_list),
                        "winner_name": winner_name,
                        "winner_wins": winner_wins,
                        "winner_pct": winner_pct,
                        "key_insights": (benchmark_result.summary.key_insights[:3] if benchmark_result.summary else []),
                        "report_url": report_url,
                        "generated_at": datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC"),
                    },
                    subject=(
                        f"Your Benchmark Report is Ready — {benchmark_result.main_company}"
                        f" vs {', '.join(benchmark_result.competitors)}"
                    ),
                    sender_email=settings.ses_sender_email,
                    templates_dir=templates_dir,
                    ses_region=settings.ses_region,
                )
                logger.info("Benchmark completion email sent to %s", recipient_email)
        except Exception:
            logger.exception("Failed to send benchmark completion email (non-fatal)")

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
