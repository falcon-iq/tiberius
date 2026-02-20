from __future__ import annotations

import logging

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.prompts import (
    BENCHMARK_ANALYZE_SYSTEM,
    BENCHMARK_ANALYZE_USER,
    BENCHMARK_EVAL_SYSTEM,
    BENCHMARK_SUMMARIZE_SYSTEM,
    BENCHMARK_SUMMARIZE_USER,
)
from falcon_iq_analyzer.models.domain import (
    BenchmarkSummary,
    CompanyMention,
    GeneratedPrompt,
    PromptEvaluation,
)

logger = logging.getLogger(__name__)


async def evaluate_single_prompt(
    llm: LLMClient,
    prompt: GeneratedPrompt,
    company_a: str,
    company_b: str,
) -> PromptEvaluation:
    """Evaluate a single prompt: send to LLM, then analyze the response."""
    # Step 1: Send prompt as a regular user query
    llm_response = await llm.complete(BENCHMARK_EVAL_SYSTEM, prompt.prompt_text)

    # Step 2: Analyze the response for competitive positioning
    analyze_user = BENCHMARK_ANALYZE_USER.format(
        prompt_text=prompt.prompt_text,
        company_a=company_a,
        company_b=company_b,
        llm_response=llm_response,
    )

    try:
        analysis = await llm.complete_json(BENCHMARK_ANALYZE_SYSTEM, analyze_user)
    except Exception:
        logger.exception("Failed to analyze response for prompt %s", prompt.prompt_id)
        return PromptEvaluation(
            prompt_id=prompt.prompt_id,
            prompt_text=prompt.prompt_text,
            category=prompt.category,
            llm_response=llm_response,
            winner="neither",
            analysis_notes="Analysis failed",
        )

    company_a_data = analysis.get("company_a_mention", {})
    company_b_data = analysis.get("company_b_mention", {})

    return PromptEvaluation(
        prompt_id=prompt.prompt_id,
        prompt_text=prompt.prompt_text,
        category=prompt.category,
        llm_response=llm_response,
        company_a_mention=CompanyMention(**company_a_data) if company_a_data else None,
        company_b_mention=CompanyMention(**company_b_data) if company_b_data else None,
        winner=analysis.get("winner", "neither"),
        analysis_notes=analysis.get("analysis_notes", ""),
    )


async def summarize_evaluations(
    llm: LLMClient,
    company_a: str,
    company_b: str,
    evaluations: list[PromptEvaluation],
) -> BenchmarkSummary:
    """Aggregate all evaluations into a benchmark summary."""
    company_a_wins = sum(1 for e in evaluations if e.winner == "company_a")
    company_b_wins = sum(1 for e in evaluations if e.winner == "company_b")
    ties = sum(1 for e in evaluations if e.winner == "tie")
    neither = sum(1 for e in evaluations if e.winner == "neither")

    # Build evaluation details text
    details_lines: list[str] = []
    for e in evaluations:
        details_lines.append(f"Prompt ({e.category}): {e.prompt_text}")
        details_lines.append(f"  Winner: {e.winner}")
        if e.company_a_mention:
            m = e.company_a_mention
            details_lines.append(
                f"  {company_a}: sentiment={m.sentiment}, "
                f"strengths={m.strengths_mentioned}, weaknesses={m.weaknesses_mentioned}"
            )
        if e.company_b_mention:
            m = e.company_b_mention
            details_lines.append(
                f"  {company_b}: sentiment={m.sentiment}, "
                f"strengths={m.strengths_mentioned}, weaknesses={m.weaknesses_mentioned}"
            )
        details_lines.append("")

    user_prompt = BENCHMARK_SUMMARIZE_USER.format(
        company_a=company_a,
        company_b=company_b,
        total_prompts=len(evaluations),
        company_a_wins=company_a_wins,
        company_b_wins=company_b_wins,
        ties=ties,
        neither=neither,
        evaluation_details="\n".join(details_lines),
    )

    try:
        data = await llm.complete_json(BENCHMARK_SUMMARIZE_SYSTEM, user_prompt)
    except Exception:
        logger.exception("Failed to generate summary")
        data = {}

    # Calculate average sentiments
    a_sentiments = [
        e.company_a_mention.sentiment for e in evaluations if e.company_a_mention and e.company_a_mention.mentioned
    ]
    b_sentiments = [
        e.company_b_mention.sentiment for e in evaluations if e.company_b_mention and e.company_b_mention.mentioned
    ]

    return BenchmarkSummary(
        company_a=company_a,
        company_b=company_b,
        total_prompts=len(evaluations),
        company_a_wins=company_a_wins,
        company_b_wins=company_b_wins,
        ties=ties,
        neither_mentioned=neither,
        company_a_avg_sentiment=round(sum(a_sentiments) / len(a_sentiments), 2) if a_sentiments else 0.0,
        company_b_avg_sentiment=round(sum(b_sentiments) / len(b_sentiments), 2) if b_sentiments else 0.0,
        company_a_top_strengths=data.get("company_a_top_strengths", []),
        company_b_top_strengths=data.get("company_b_top_strengths", []),
        company_a_top_weaknesses=data.get("company_a_top_weaknesses", []),
        company_b_top_weaknesses=data.get("company_b_top_weaknesses", []),
        key_insights=data.get("key_insights", []),
    )
