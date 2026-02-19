from __future__ import annotations

import asyncio
import logging
from typing import Dict, List

from openai import AuthenticationError

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.prompts import CLASSIFY_SYSTEM, CLASSIFY_USER
from falcon_iq_analyzer.models.domain import PageClassification, PageInfo

logger = logging.getLogger(__name__)


async def classify_page(llm: LLMClient, page: PageInfo) -> PageClassification:
    """Classify a single page using the LLM."""
    user_prompt = CLASSIFY_USER.format(
        url_path=page.url_path,
        title=page.title,
        meta_description=page.meta_description,
        clean_text=page.clean_text,
    )
    try:
        result = await llm.complete_json(CLASSIFY_SYSTEM, user_prompt)
        return PageClassification(
            page_type=result.get("page_type", "other"),
            confidence=float(result.get("confidence", 0.0)),
            reasoning=result.get("reasoning", ""),
        )
    except AuthenticationError:
        raise  # Don't swallow auth errors — let them bubble up
    except Exception:
        logger.exception("Classification failed for %s", page.url_path)
        return PageClassification(page_type="other", confidence=0.0, reasoning="classification error")


async def classify_pages(
    llm: LLMClient, pages: List[PageInfo]
) -> Dict[str, PageClassification]:
    """Classify all pages concurrently. Returns mapping of filepath -> classification."""
    # Test LLM connectivity with the first page before classifying all
    if pages:
        first_result = await classify_page(llm, pages[0])
        remaining_tasks = [classify_page(llm, page) for page in pages[1:]]
        remaining_results = await asyncio.gather(*remaining_tasks)
        all_results = [first_result] + list(remaining_results)
        return {page.filepath: cls for page, cls in zip(pages, all_results)}
    return {}
