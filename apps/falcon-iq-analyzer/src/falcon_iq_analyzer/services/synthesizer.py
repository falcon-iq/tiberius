from __future__ import annotations

import logging

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.prompts import (
    SUMMARIZE_BATCH_SYSTEM,
    SUMMARIZE_BATCH_USER,
    SYNTHESIZE_SYSTEM,
    SYNTHESIZE_USER,
)
from falcon_iq_analyzer.models.domain import PageExtraction, TopOffering

logger = logging.getLogger(__name__)

MAX_EXTRACTIONS_CHARS = 12000
BATCH_SIZE = 20


def _extractions_to_text(extractions: list[PageExtraction]) -> str:
    """Convert extractions to a text summary for the LLM."""
    lines: list[str] = []
    for ext in extractions:
        for off in ext.offerings:
            lines.append(
                f"- {off.product_name} ({off.category}): {off.description} "
                f"Features: {', '.join(off.features[:5])}. "
                f"Benefits: {', '.join(off.benefits[:3])}."
            )
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
        lines.append(
            f"- {s.get('product_name', '?')} ({s.get('category', '?')}): "
            f"{s.get('description', '')} Features: {', '.join(s.get('key_features', []))}"
        )
    return "\n".join(lines)


async def synthesize_offerings(
    llm: LLMClient,
    company_name: str,
    extractions: list[PageExtraction],
) -> list[TopOffering]:
    """Synthesize all extractions into top 5 offerings with selling scripts."""
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
        offerings.append(TopOffering(**o))
    return offerings
