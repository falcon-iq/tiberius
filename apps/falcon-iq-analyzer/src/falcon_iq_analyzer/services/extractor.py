"""Two-pass evidence-backed extraction.

Pass 1: Extract offerings with verbatim evidence quotes from page text.
Pass 2: Verify each extraction against the original page — drop unsupported claims.
"""

from __future__ import annotations

import asyncio
import json
import logging

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.prompts import (
    EXTRACT_SYSTEM,
    EXTRACT_USER,
    VERIFY_EXTRACTION_SYSTEM,
    VERIFY_EXTRACTION_USER,
)
from falcon_iq_analyzer.models.domain import (
    Evidence,
    ExtractedIntegration,
    Offering,
    PageExtraction,
    PageInfo,
    PricingPlan,
)
from falcon_iq_analyzer.services.structured_extractor import extract_structured_data

logger = logging.getLogger(__name__)


def _format_structured_data_section(page: PageInfo) -> str:
    """Format pre-extracted structured data as text for the LLM prompt."""
    parts: list[str] = []
    sd = page.structured_data

    if not sd:
        return ""

    if sd.json_ld:
        parts.append("Pre-extracted structured data (JSON-LD, verified):")
        for block in sd.json_ld[:3]:
            parts.append(f"  {json.dumps(block, default=str)[:500]}")

    if sd.og_tags:
        parts.append("Open Graph metadata:")
        for key, val in sd.og_tags.items():
            parts.append(f"  {key}: {val}")

    if sd.tables:
        parts.append(f"HTML tables found: {len(sd.tables)}")
        for i, table in enumerate(sd.tables[:2]):
            parts.append(f"  Table {i + 1}:")
            for row in table[:5]:
                parts.append(f"    | {' | '.join(row)} |")

    if sd.headings:
        parts.append("Page structure:")
        for h in sd.headings[:10]:
            parts.append(f"  {h['level']}: {h['text']}")

    return "\n".join(parts) + "\n" if parts else ""


async def extract_page(llm: LLMClient, page: PageInfo) -> PageExtraction:
    """Extract product offerings from a single page using two-pass approach."""

    # Gather deterministic structured data
    struct_data = extract_structured_data(page)

    # Pass 1: LLM extraction with strict evidence contract
    structured_section = _format_structured_data_section(page)
    user_prompt = EXTRACT_USER.format(
        url_path=page.url_path,
        title=page.title,
        structured_data_section=structured_section,
        clean_text=page.clean_text,
    )
    try:
        result = await llm.complete_json(EXTRACT_SYSTEM, user_prompt)
    except Exception:
        logger.exception("Pass 1 extraction failed for %s", page.url_path)
        return PageExtraction(filepath=page.filepath, url_path=page.url_path)

    # Parse offerings
    offerings: list[Offering] = []
    for o in result.get("offerings", []):
        if not isinstance(o, dict):
            continue
        evidence = [Evidence(**e) for e in o.get("evidence", []) or [] if isinstance(e, dict)]
        # Set url to page url_path if not provided
        for ev in evidence:
            if not ev.url:
                ev.url = page.url_path
        offerings.append(
            Offering(
                product_name=o.get("product_name") or "",
                category=o.get("category") or "",
                description=o.get("description") or "",
                features=o.get("features") or [],
                benefits=o.get("benefits") or [],
                target_audience=o.get("target_audience") or "",
                evidence=evidence,
                confidence=0.7,  # default before verification
            )
        )

    # Parse pricing plans from LLM extraction
    llm_pricing: list[PricingPlan] = []
    for p in result.get("pricing_plans") or []:
        if isinstance(p, dict):
            evidence = [Evidence(**e) for e in p.get("evidence") or [] if isinstance(e, dict)]
            llm_pricing.append(
                PricingPlan(
                    name=p.get("name") or "",
                    price=p.get("price"),
                    currency=p.get("currency"),
                    billing_period=p.get("billing_period") or "contact_sales",
                    evidence=evidence,
                    confidence=0.7,
                )
            )

    # Parse integrations from LLM extraction
    llm_integrations: list[ExtractedIntegration] = []
    for i in result.get("integrations") or []:
        if isinstance(i, dict):
            evidence = [Evidence(**e) for e in i.get("evidence") or [] if isinstance(e, dict)]
            llm_integrations.append(
                ExtractedIntegration(
                    name=i.get("name") or "",
                    integration_type=i.get("integration_type") or "unknown",
                    evidence=evidence,
                    confidence=0.7,
                )
            )

    # Merge with deterministic extractions (higher confidence)
    all_pricing = struct_data["pricing_plans"] + llm_pricing
    all_integrations = struct_data["integrations"] + llm_integrations

    # Deduplicate pricing by plan name
    seen_plans: set[str] = set()
    deduped_pricing: list[PricingPlan] = []
    for plan in all_pricing:
        key = plan.name.lower()
        if key not in seen_plans:
            seen_plans.add(key)
            deduped_pricing.append(plan)

    # Deduplicate integrations by name
    seen_integrations: set[str] = set()
    deduped_integrations: list[ExtractedIntegration] = []
    for integ in all_integrations:
        key = integ.name.lower()
        if key not in seen_integrations:
            seen_integrations.add(key)
            deduped_integrations.append(integ)

    # Pass 2: Verify extractions against original page text
    if offerings:
        offerings = await _verify_extractions(llm, offerings, page)

    return PageExtraction(
        filepath=page.filepath,
        url_path=page.url_path,
        offerings=offerings,
        pricing_plans=deduped_pricing,
        integrations=deduped_integrations,
    )


async def _verify_extractions(
    llm: LLMClient,
    offerings: list[Offering],
    page: PageInfo,
) -> list[Offering]:
    """Pass 2: Verify candidate extractions against original page text."""
    # Build candidate JSON for the verifier
    candidates = []
    for o in offerings:
        candidates.append(
            {
                "product_name": o.product_name,
                "description": o.description,
                "features": o.features,
                "benefits": o.benefits,
                "evidence": [{"url": e.url, "quote": e.quote} for e in o.evidence],
            }
        )

    user_prompt = VERIFY_EXTRACTION_USER.format(
        extractions_json=json.dumps(candidates, indent=2),
        url_path=page.url_path,
        clean_text=page.clean_text,
    )

    try:
        result = await llm.complete_json(VERIFY_EXTRACTION_SYSTEM, user_prompt)
    except Exception:
        logger.exception("Pass 2 verification failed for %s — keeping all extractions", page.url_path)
        return offerings

    # Apply verification verdicts
    verdicts_by_name = {}
    for v in result.get("verified_offerings", []):
        if isinstance(v, dict):
            verdicts_by_name[v.get("product_name", "")] = v

    verified_offerings: list[Offering] = []
    for offering in offerings:
        verdict = verdicts_by_name.get(offering.product_name, {})
        action = verdict.get("required_action", "keep")

        if action == "drop":
            logger.info(
                "Dropping offering '%s' from %s — verification: %s",
                offering.product_name,
                page.url_path,
                verdict.get("rationale", "no rationale"),
            )
            continue

        if action == "downgrade_confidence":
            offering.confidence = max(0.3, offering.confidence - 0.3)

        if verdict.get("verdict") == "supported":
            offering.confidence = min(1.0, offering.confidence + 0.2)

        # Also verify individual features
        feature_verdicts = {
            fv.get("feature", ""): fv
            for fv in verdict.get("features_verdicts", [])
            if isinstance(fv, dict)
        }
        verified_features: list[str] = []
        for feat in offering.features:
            fv = feature_verdicts.get(feat, {})
            if fv.get("verdict") != "not_supported":
                verified_features.append(feat)
            else:
                logger.info(
                    "Dropping feature '%s' from '%s' — not supported by page text",
                    feat,
                    offering.product_name,
                )
        offering.features = verified_features
        verified_offerings.append(offering)

    logger.info(
        "Verification for %s: %d/%d offerings kept",
        page.url_path,
        len(verified_offerings),
        len(offerings),
    )
    return verified_offerings


async def extract_pages(llm: LLMClient, pages: list[PageInfo]) -> list[PageExtraction]:
    """Extract offerings from all product/industry pages concurrently."""
    tasks = [extract_page(llm, page) for page in pages]
    return await asyncio.gather(*tasks)
