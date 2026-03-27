"""LLM-powered claim verification against external evidence."""

from __future__ import annotations

import json
import logging
from typing import List

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.models.enrichment import EnrichmentResult, ExternalSource, VerifiedClaim

logger = logging.getLogger(__name__)

VERIFY_SYSTEM = """\
You are a fact-checking analyst. You will receive:
1. WEBSITE CLAIMS — statements extracted from a company's website.
2. EXTERNAL EVIDENCE — facts gathered from G2 reviews, Crunchbase, and Google Search.

For each website claim, determine whether external evidence supports, contradicts, or \
neither supports nor contradicts the claim.

Output a JSON array where each element has:
- "claim": the original claim text
- "status": one of "verified", "contradicted", or "unverified"
- "evidence": a brief explanation citing the specific external source
- "external_source": one of "g2", "crunchbase", "google_search", or null if unverified

Rules:
- "verified" = external evidence clearly supports the claim
- "contradicted" = external evidence clearly disagrees with the claim
- "unverified" = no relevant external evidence found (this is the default)
- Be conservative: if evidence is ambiguous, use "unverified"
- Output ONLY the JSON array, no other text
"""

VERIFY_USER = """\
Company: {company_name}

## WEBSITE CLAIMS
{claims_block}

## EXTERNAL EVIDENCE

### G2 Reviews
{g2_block}

### Crunchbase
{crunchbase_block}

### Google Search Insights
{google_block}
"""


async def verify_claims(
    llm: LLMClient,
    company_name: str,
    website_claims: List[str],
    enrichment: EnrichmentResult,
) -> List[VerifiedClaim]:
    """Cross-reference website claims against external enrichment data.

    Returns all claims with verified/unverified/contradicted status.
    If no external evidence is available, all claims are returned as unverified.
    """
    if not website_claims:
        return []

    # If no external data at all, skip LLM call — everything is unverified
    has_evidence = (
        enrichment.g2 is not None
        or enrichment.crunchbase is not None
        or len(enrichment.google_insights) > 0
        or len(enrichment.review_sites) > 0
    )
    if not has_evidence:
        logger.info("No external evidence for %s — marking all claims as unverified", company_name)
        return [VerifiedClaim(claim=claim, status="unverified") for claim in website_claims]

    # Build evidence blocks
    g2_block = _build_g2_block(enrichment)
    crunchbase_block = _build_crunchbase_block(enrichment)
    google_block = _build_google_block(enrichment)
    claims_block = "\n".join(f"- {claim}" for claim in website_claims)

    user_prompt = VERIFY_USER.format(
        company_name=company_name,
        claims_block=claims_block,
        g2_block=g2_block,
        crunchbase_block=crunchbase_block,
        google_block=google_block,
    )

    try:
        response = await llm.complete(VERIFY_SYSTEM, user_prompt)
        return _parse_verification_response(response)
    except Exception:
        logger.warning("Claim verification LLM call failed for %s", company_name, exc_info=True)
        return [VerifiedClaim(claim=claim, status="unverified") for claim in website_claims]


def _build_g2_block(enrichment: EnrichmentResult) -> str:
    if enrichment.g2 is None:
        return "No G2 data available."
    g2 = enrichment.g2
    lines = []
    if g2.rating is not None:
        lines.append(f"Rating: {g2.rating}/5 ({g2.review_count} reviews)")
    for theme in g2.pros_themes:
        lines.append(f"Pro: {theme.theme}")
    for theme in g2.cons_themes:
        lines.append(f"Con: {theme.theme}")
    if g2.reviewer_titles:
        lines.append(f"Reviewer titles: {', '.join(g2.reviewer_titles)}")
    return "\n".join(lines) if lines else "No G2 data available."


def _build_crunchbase_block(enrichment: EnrichmentResult) -> str:
    if enrichment.crunchbase is None:
        return "No Crunchbase data available."
    cb = enrichment.crunchbase
    lines = []
    if cb.founded:
        lines.append(f"Founded: {cb.founded}")
    if cb.hq:
        lines.append(f"HQ: {cb.hq}")
    if cb.employee_count:
        lines.append(f"Employees: {cb.employee_count}")
    if cb.total_funding:
        lines.append(f"Total funding: {cb.total_funding}")
    if cb.investors:
        lines.append(f"Investors: {', '.join(cb.investors)}")
    return "\n".join(lines) if lines else "No Crunchbase data available."


def _build_google_block(enrichment: EnrichmentResult) -> str:
    if not enrichment.google_insights:
        return "No Google Search insights available."
    lines = []
    for insight in enrichment.google_insights[:10]:  # Limit to 10 to control token usage
        lines.append(f"[{insight.insight_type}] {insight.title}: {insight.snippet[:200]}")
    return "\n".join(lines)


def _parse_verification_response(response: str) -> List[VerifiedClaim]:
    """Parse the LLM JSON array response into VerifiedClaim objects."""
    # Strip markdown code fences if present
    text = response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse verification response as JSON")
        return []

    claims = []
    for item in items:
        source_str = item.get("external_source")
        external_source = None
        if source_str and source_str in ExternalSource.__members__.values():
            external_source = ExternalSource(source_str)

        claims.append(
            VerifiedClaim(
                claim=item.get("claim", ""),
                status=item.get("status", "unverified"),
                evidence=item.get("evidence", ""),
                external_source=external_source,
            )
        )
    return claims
