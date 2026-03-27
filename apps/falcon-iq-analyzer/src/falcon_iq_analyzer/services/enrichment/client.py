"""HTTP client for the crawler's enrichment API."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

import httpx

from falcon_iq_analyzer.models.enrichment import EnrichmentResult

logger = logging.getLogger(__name__)


async def fetch_enrichment(
    company_name: str,
    company_url: str,
    crawler_api_url: str,
) -> EnrichmentResult:
    """Call the crawler's POST /api/enrich endpoint for a single company.

    Returns an empty EnrichmentResult on any failure (graceful degradation).
    """
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{crawler_api_url}/api/enrich",
                json={"companyName": company_name, "companyUrl": company_url},
            )
            resp.raise_for_status()
            data = resp.json()
            return EnrichmentResult(**_snake_keys(data))
    except Exception:
        logger.warning("Enrichment fetch failed for %s — returning empty result", company_name, exc_info=True)
        return EnrichmentResult(company_name=company_name)


async def fetch_all_enrichments(
    company_overviews: Dict[str, object],
    crawler_api_url: str,
) -> Dict[str, EnrichmentResult]:
    """Fetch enrichment data for all companies in parallel."""

    async def _fetch(name: str, url: str) -> tuple[str, EnrichmentResult]:
        result = await fetch_enrichment(name, url, crawler_api_url)
        return name, result

    tasks = [_fetch(name, getattr(ov, "url", "")) for name, ov in company_overviews.items()]
    pairs = await asyncio.gather(*tasks, return_exceptions=True)

    results: Dict[str, EnrichmentResult] = {}
    for pair in pairs:
        if isinstance(pair, Exception):
            logger.warning("Enrichment task failed: %s", pair)
            continue
        name, enrichment = pair
        results[name] = enrichment

    logger.info(
        "Enrichment completed for %d/%d companies",
        len(results),
        len(company_overviews),
    )
    return results


def _snake_keys(data: dict) -> dict:
    """Convert camelCase keys from Java JSON to snake_case for Pydantic."""
    mapping = {
        "companyName": "company_name",
        "googleInsights": "google_insights",
        "reviewSites": "review_sites",
        "externalFacts": "external_facts",
        "fetchedAt": "fetched_at",
        "reviewCount": "review_count",
        "g2Url": "g2_url",
        "prosThemes": "pros_themes",
        "consThemes": "cons_themes",
        "reviewerTitles": "reviewer_titles",
        "companySizes": "company_sizes",
        "sampleQuotes": "sample_quotes",
        "siteName": "site_name",
        "employeeCount": "employee_count",
        "totalFunding": "total_funding",
        "insightType": "insight_type",
        "sourceUrl": "source_url",
    }
    result = {}
    for key, value in data.items():
        snake_key = mapping.get(key, key)
        if isinstance(value, dict):
            result[snake_key] = _snake_keys(value)
        elif isinstance(value, list):
            result[snake_key] = [_snake_keys(item) if isinstance(item, dict) else item for item in value]
        else:
            result[snake_key] = value
    return result
