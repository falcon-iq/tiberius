from __future__ import annotations

import logging
from datetime import datetime, timezone

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.prompts import BENCHMARK_GENERATE_SYSTEM, BENCHMARK_GENERATE_USER
from falcon_iq_analyzer.models.domain import AnalysisResult, GeneratedPrompt, PromptGenerationResult

logger = logging.getLogger(__name__)


def _offerings_to_text(result: AnalysisResult) -> str:
    lines: list[str] = []
    for o in result.top_offerings:
        lines.append(f"- {o.product_name} ({o.category}): {o.description}")
        if o.key_features:
            lines.append(f"  Features: {', '.join(o.key_features[:5])}")
    return "\n".join(lines)


async def generate_prompts(
    llm: LLMClient,
    result_a: AnalysisResult,
    result_b: AnalysisResult,
    num_prompts: int = 15,
) -> PromptGenerationResult:
    """Generate realistic buyer prompts from two company analyses."""
    offerings_a = _offerings_to_text(result_a)
    offerings_b = _offerings_to_text(result_b)

    user_prompt = BENCHMARK_GENERATE_USER.format(
        company_a=result_a.company_name,
        offerings_a=offerings_a,
        company_b=result_b.company_name,
        offerings_b=offerings_b,
        num_prompts=num_prompts,
    )

    data = await llm.complete_json(BENCHMARK_GENERATE_SYSTEM, user_prompt)
    prompts = [GeneratedPrompt(**p) for p in data.get("prompts", [])]

    logger.info("Generated %d prompts for %s vs %s", len(prompts), result_a.company_name, result_b.company_name)

    return PromptGenerationResult(
        company_a=result_a.company_name,
        company_b=result_b.company_name,
        prompts=prompts,
        generation_timestamp=datetime.now(timezone.utc).isoformat(),
    )
