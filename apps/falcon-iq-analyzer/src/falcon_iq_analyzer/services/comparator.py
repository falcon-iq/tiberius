from __future__ import annotations

import logging

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.prompts import COMPARE_SYSTEM, COMPARE_USER
from falcon_iq_analyzer.models.domain import AnalysisResult, ComparisonResult

logger = logging.getLogger(__name__)


def _offerings_to_text(result: AnalysisResult) -> str:
    lines: list[str] = []
    for o in result.top_offerings:
        lines.append(
            f"{o.rank}. {o.product_name} ({o.category}): {o.description}\n"
            f"   Features: {', '.join(o.key_features[:5])}\n"
            f"   Benefits: {', '.join(o.key_benefits[:3])}"
        )
    return "\n".join(lines)


async def compare_companies(
    llm: LLMClient,
    result_a: AnalysisResult,
    result_b: AnalysisResult,
) -> ComparisonResult:
    """Compare two company analysis results using the LLM."""
    user_prompt = COMPARE_USER.format(
        company_a=result_a.company_name,
        offerings_a=_offerings_to_text(result_a),
        company_b=result_b.company_name,
        offerings_b=_offerings_to_text(result_b),
    )

    data = await llm.complete_json(COMPARE_SYSTEM, user_prompt)
    return ComparisonResult(
        company_a=result_a.company_name,
        company_b=result_b.company_name,
        summary=data.get("summary", ""),
        company_a_strengths=data.get("company_a_strengths", []),
        company_b_strengths=data.get("company_b_strengths", []),
        overlap_areas=data.get("overlap_areas", []),
        differentiation=data.get("differentiation", ""),
        recommendation=data.get("recommendation", ""),
    )
