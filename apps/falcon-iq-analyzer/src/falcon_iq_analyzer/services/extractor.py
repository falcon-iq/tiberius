from __future__ import annotations

import asyncio
import logging

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.prompts import EXTRACT_SYSTEM, EXTRACT_USER
from falcon_iq_analyzer.models.domain import Offering, PageExtraction, PageInfo

logger = logging.getLogger(__name__)


async def extract_page(llm: LLMClient, page: PageInfo) -> PageExtraction:
    """Extract product offerings from a single page."""
    user_prompt = EXTRACT_USER.format(
        url_path=page.url_path,
        title=page.title,
        clean_text=page.clean_text,
    )
    try:
        result = await llm.complete_json(EXTRACT_SYSTEM, user_prompt)
        offerings = [Offering(**o) for o in result.get("offerings", [])]
        return PageExtraction(
            filepath=page.filepath,
            url_path=page.url_path,
            offerings=offerings,
        )
    except Exception:
        logger.exception("Extraction failed for %s", page.url_path)
        return PageExtraction(filepath=page.filepath, url_path=page.url_path)


async def extract_pages(llm: LLMClient, pages: list[PageInfo]) -> list[PageExtraction]:
    """Extract offerings from all product/industry pages concurrently."""
    tasks = [extract_page(llm, page) for page in pages]
    return await asyncio.gather(*tasks)
