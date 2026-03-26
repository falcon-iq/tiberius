"""Synthesize page-level extractions into a ranked list of top offerings.

Takes evidence-backed extractions from multiple pages and produces
a unified, deduplicated, confidence-scored list of top 5 offerings.
"""

from __future__ import annotations

import logging

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.prompts import (
    SUMMARIZE_BATCH_SYSTEM,
    SUMMARIZE_BATCH_USER,
    SYNTHESIZE_SYSTEM,
    SYNTHESIZE_USER,
)
from falcon_iq_analyzer.models.domain import Evidence, PageExtraction, TopOffering

logger = logging.getLogger(__name__)

MAX_EXTRACTIONS_CHARS = 12000
BATCH_SIZE = 20


def _extractions_to_text(extractions: list[PageExtraction]) -> str:
    """Convert extractions to a text summary for the LLM, preserving source URLs."""
    lines: list[str] = []
    for ext in extractions:
        for off in ext.offerings:
            evidence_refs = ""
            if off.evidence:
                urls = list({e.url for e in off.evidence if e.url})
                if urls:
                    evidence_refs = f" [sources: {', '.join(urls)}]"

            lines.append(
                f"- {off.product_name} ({off.category}): {off.description} "
                f"Features: {', '.join(off.features[:5])}. "
                f"Benefits: {', '.join(off.benefits[:3])}.{evidence_refs}"
            )

        # Include pricing and integration data for context
        for plan in ext.pricing_plans:
            price_str = f"{plan.currency} {plan.price}" if plan.price is not None else "Contact sales"
            lines.append(f"  Pricing: {plan.name} — {price_str}/{plan.billing_period} [from {ext.url_path}]")

        for integ in ext.integrations:
            lines.append(f"  Integration: {integ.name} ({integ.integration_type}) [from {ext.url_path}]")

    return "\n".join(lines)


async def _summarize_batch(llm: LLMClient, batch_text: str) -> str:
    """Pre-summarize a batch of extractions if they exceed the token limit."""
    result = await llm.complete_json(
        SUMMARIZE_BATCH_SYSTEM,
        SUMMARIZE_BATCH_USER.format(batch_text=batch_text),
    )
    summaries = result.get("offerings_summary", [])
    lines = []
    for s in summaries:
        source_pages = s.get("source_pages", [])
        source_ref = f" [sources: {', '.join(source_pages)}]" if source_pages else ""
        lines.append(
            f"- {s.get('product_name', '?')} ({s.get('category', '?')}): "
            f"{s.get('description', '')} Features: {', '.join(str(f) for f in s.get('key_features', []))}"
            f"{source_ref}"
        )
    return "\n".join(lines)


async def synthesize_offerings(
    llm: LLMClient,
    company_name: str,
    extractions: list[PageExtraction],
) -> list[TopOffering]:
    """Synthesize all extractions into top 5 evidence-backed offerings."""
    full_text = _extractions_to_text(extractions)

    # If the text is too long, pre-summarize in batches
    if len(full_text) > MAX_EXTRACTIONS_CHARS:
        logger.info("Extractions text too long (%d chars), pre-summarizing in batches", len(full_text))
        lines = full_text.split("\n")
        batches: list[list[str]] = []
        for i in range(0, len(lines), BATCH_SIZE):
            batches.append(lines[i : i + BATCH_SIZE])

        summaries: list[str] = []
        for batch in batches:
            batch_text = "\n".join(batch)
            summary = await _summarize_batch(llm, batch_text)
            summaries.append(summary)
        full_text = "\n".join(summaries)

    user_prompt = SYNTHESIZE_USER.format(
        company_name=company_name,
        num_pages=len(extractions),
        extractions_text=full_text,
    )

    result = await llm.complete_json(SYNTHESIZE_SYSTEM, user_prompt)
    offerings = []
    for o in result.get("top_offerings", []):
        # Parse evidence if provided by LLM
        evidence = []
        for e in o.get("evidence", []):
            if isinstance(e, dict):
                evidence.append(Evidence(**e))

        offerings.append(
            TopOffering(
                rank=o.get("rank", 0),
                product_name=o.get("product_name", ""),
                category=o.get("category", ""),
                description=o.get("description", ""),
                key_features=o.get("key_features", []),
                key_benefits=o.get("key_benefits", []),
                target_audience=o.get("target_audience", ""),
                selling_script="",  # deprecated — no longer generated
                evidence_summary=o.get("evidence_summary", ""),
                evidence=evidence,
                confidence=o.get("confidence", 0.5),
            )
        )

    # Filter out low-confidence offerings
    high_conf = [o for o in offerings if o.confidence >= 0.4]
    if high_conf:
        offerings = high_conf

    return offerings
