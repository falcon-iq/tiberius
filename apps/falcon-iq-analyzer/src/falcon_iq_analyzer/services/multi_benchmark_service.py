from __future__ import annotations

import logging
from collections import Counter

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.multi_benchmark_prompts import (
    MULTI_BENCHMARK_ANALYZE_SYSTEM,
    MULTI_BENCHMARK_ANALYZE_USER,
    MULTI_BENCHMARK_GENERATE_SYSTEM,
    MULTI_BENCHMARK_GENERATE_USER,
    MULTI_BENCHMARK_SUMMARIZE_SYSTEM,
    MULTI_BENCHMARK_SUMMARIZE_USER,
)
from falcon_iq_analyzer.llm.prompts import BENCHMARK_EVAL_SYSTEM
from falcon_iq_analyzer.models.company_benchmark import (
    MultiCompanyBenchmarkResult,
    MultiCompanyBenchmarkSummary,
    MultiCompanyPromptEvaluation,
    MultiCompanyStats,
)
from falcon_iq_analyzer.models.domain import AnalysisResult, CompanyMention, GeneratedPrompt

logger = logging.getLogger(__name__)


def _offerings_to_text(result: AnalysisResult) -> str:
    lines: list[str] = []
    for o in result.top_offerings:
        lines.append(f"- {o.product_name} ({o.category}): {o.description}")
        if o.key_features:
            lines.append(f"  Features: {', '.join(o.key_features[:5])}")
    return "\n".join(lines)


async def generate_multi_prompts(
    llm: LLMClient,
    main_result: AnalysisResult,
    competitor_results: list[AnalysisResult],
    num_prompts: int = 15,
) -> list[GeneratedPrompt]:
    """Generate realistic buyer prompts given a main company + N competitors."""
    main_offerings = _offerings_to_text(main_result)

    competitor_sections_parts: list[str] = []
    for comp in competitor_results:
        competitor_sections_parts.append(f"{comp.company_name}:\n{_offerings_to_text(comp)}")
    competitor_sections = "\n\n".join(competitor_sections_parts)

    user_prompt = MULTI_BENCHMARK_GENERATE_USER.format(
        main_company=main_result.company_name,
        main_offerings=main_offerings,
        competitor_sections=competitor_sections,
        num_prompts=num_prompts,
    )

    data = await llm.complete_json(MULTI_BENCHMARK_GENERATE_SYSTEM, user_prompt)
    prompts = [GeneratedPrompt(**p) for p in data.get("prompts", [])]

    logger.info(
        "Generated %d multi-company prompts for %s vs %d competitors",
        len(prompts),
        main_result.company_name,
        len(competitor_results),
    )
    return prompts


async def evaluate_single_prompt_multi(
    llm: LLMClient,
    prompt: GeneratedPrompt,
    company_names: list[str],
) -> MultiCompanyPromptEvaluation:
    """Evaluate a single prompt: send to LLM, then analyze response for N companies."""
    # Step 1: Send prompt as a regular user query
    llm_response = await llm.complete(BENCHMARK_EVAL_SYSTEM, prompt.prompt_text)

    # Step 2: Analyze the response for all companies
    analyze_user = MULTI_BENCHMARK_ANALYZE_USER.format(
        prompt_text=prompt.prompt_text,
        company_names=", ".join(company_names),
        llm_response=llm_response,
    )

    try:
        analysis = await llm.complete_json(MULTI_BENCHMARK_ANALYZE_SYSTEM, analyze_user)
    except Exception:
        logger.exception("Failed to analyze response for prompt %s", prompt.prompt_id)
        return MultiCompanyPromptEvaluation(
            prompt_id=prompt.prompt_id,
            prompt_text=prompt.prompt_text,
            category=prompt.category,
            llm_response=llm_response,
            winner="neither",
            analysis_notes="Analysis failed",
        )

    # Parse company mentions dict
    raw_mentions = analysis.get("company_mentions", {})
    company_mentions: dict[str, CompanyMention] = {}
    for name, mention_data in raw_mentions.items():
        if isinstance(mention_data, dict):
            company_mentions[name] = CompanyMention(**mention_data)

    return MultiCompanyPromptEvaluation(
        prompt_id=prompt.prompt_id,
        prompt_text=prompt.prompt_text,
        category=prompt.category,
        llm_response=llm_response,
        company_mentions=company_mentions,
        winner=analysis.get("winner", "neither"),
        analysis_notes=analysis.get("analysis_notes", ""),
    )


async def summarize_multi_evaluations(
    llm: LLMClient,
    company_names: list[str],
    evaluations: list[MultiCompanyPromptEvaluation],
) -> MultiCompanyBenchmarkSummary:
    """Aggregate all evaluations into a multi-company benchmark summary."""
    # Count wins per company
    win_counts: Counter[str] = Counter()
    ties = 0
    neither = 0
    for e in evaluations:
        if e.winner == "tie":
            ties += 1
        elif e.winner == "neither":
            neither += 1
        else:
            win_counts[e.winner] += 1

    # Build win summary text
    win_lines: list[str] = []
    for name in company_names:
        win_lines.append(f"- {name} wins: {win_counts.get(name, 0)}")
    win_lines.append(f"- Ties: {ties}")
    win_lines.append(f"- Neither mentioned: {neither}")
    win_summary = "\n".join(win_lines)

    # Build evaluation details text
    details_lines: list[str] = []
    for e in evaluations:
        details_lines.append(f"Prompt ({e.category}): {e.prompt_text}")
        details_lines.append(f"  Winner: {e.winner}")
        for name in company_names:
            mention = e.company_mentions.get(name)
            if mention:
                details_lines.append(
                    f"  {name}: sentiment={mention.sentiment}, "
                    f"strengths={mention.strengths_mentioned}, weaknesses={mention.weaknesses_mentioned}"
                )
        details_lines.append("")

    user_prompt = MULTI_BENCHMARK_SUMMARIZE_USER.format(
        company_names=", ".join(company_names),
        total_prompts=len(evaluations),
        win_summary=win_summary,
        evaluation_details="\n".join(details_lines),
    )

    try:
        data = await llm.complete_json(MULTI_BENCHMARK_SUMMARIZE_SYSTEM, user_prompt)
    except Exception:
        logger.exception("Failed to generate multi-company summary")
        data = {}

    # Calculate average sentiments per company
    sentiment_accum: dict[str, list[float]] = {name: [] for name in company_names}
    for e in evaluations:
        for name in company_names:
            mention = e.company_mentions.get(name)
            if mention and mention.mentioned:
                sentiment_accum[name].append(mention.sentiment)

    # Build per-company stats from LLM response
    llm_stats = {s["company_name"]: s for s in data.get("company_stats", []) if isinstance(s, dict)}

    company_stats: list[MultiCompanyStats] = []
    for name in company_names:
        sentiments = sentiment_accum.get(name, [])
        avg_sent = round(sum(sentiments) / len(sentiments), 2) if sentiments else 0.0
        llm_s = llm_stats.get(name, {})
        company_stats.append(
            MultiCompanyStats(
                company_name=name,
                wins=win_counts.get(name, 0),
                avg_sentiment=avg_sent,
                top_strengths=llm_s.get("top_strengths", []),
                top_weaknesses=llm_s.get("top_weaknesses", []),
            )
        )

    return MultiCompanyBenchmarkSummary(
        companies=company_names,
        total_prompts=len(evaluations),
        company_stats=company_stats,
        ties=ties,
        neither_mentioned=neither,
        key_insights=data.get("key_insights", []),
    )


def generate_multi_benchmark_report(result: MultiCompanyBenchmarkResult) -> str:
    """Generate a Markdown benchmark report for N companies."""
    lines: list[str] = []
    all_companies = [result.main_company] + result.competitors
    s = result.summary

    lines.append(f"# LLM Benchmark Report: {' vs '.join(all_companies)}")
    lines.append("")

    if s:
        # Summary scorecard
        lines.append("## Summary Scorecard")
        lines.append("")
        total = s.total_prompts or 1

        # Build dynamic header
        header = "| Metric |"
        separator = "|--------|"
        for name in all_companies:
            header += f" {name} |"
            separator += "------|"
        lines.append(header)
        lines.append(separator)

        # Wins row
        wins_row = "| Wins |"
        for name in all_companies:
            stat = next((cs for cs in s.company_stats if cs.company_name == name), None)
            wins = stat.wins if stat else 0
            pct = round(wins / total * 100)
            wins_row += f" {wins} ({pct}%) |"
        lines.append(wins_row)

        # Ties row
        ties_row = "| Ties |"
        for _ in all_companies:
            ties_row += f" {s.ties} |"
        lines.append(ties_row)

        # Avg sentiment row
        sentiment_row = "| Avg Sentiment |"
        for name in all_companies:
            stat = next((cs for cs in s.company_stats if cs.company_name == name), None)
            avg = stat.avg_sentiment if stat else 0.0
            sentiment_row += f" {avg:+.2f} |"
        lines.append(sentiment_row)

        # Total prompts row
        prompts_row = "| Total Prompts |"
        for _ in all_companies:
            prompts_row += f" {s.total_prompts} |"
        lines.append(prompts_row)
        lines.append("")

        # Win rates by category
        categories: dict[str, Counter[str]] = {}
        for e in result.evaluations:
            cat = e.category
            if cat not in categories:
                categories[cat] = Counter()
            categories[cat][e.winner] += 1

        if categories:
            lines.append("## Win Rates by Category")
            lines.append("")
            cat_header = "| Category |"
            cat_sep = "|----------|"
            for name in all_companies:
                cat_header += f" {name} |"
                cat_sep += "------|"
            cat_header += " Ties | Neither |"
            cat_sep += "------|---------|"
            lines.append(cat_header)
            lines.append(cat_sep)
            for cat, counts in sorted(categories.items()):
                row = f"| {cat} |"
                for name in all_companies:
                    row += f" {counts.get(name, 0)} |"
                row += f" {counts.get('tie', 0)} | {counts.get('neither', 0)} |"
                lines.append(row)
            lines.append("")

        # Per-company LLM perception
        for stat in s.company_stats:
            lines.append(f"## {stat.company_name} — LLM Perception")
            lines.append("")
            if stat.top_strengths:
                lines.append("**Strengths:**")
                for item in stat.top_strengths:
                    lines.append(f"- {item}")
                lines.append("")
            if stat.top_weaknesses:
                lines.append("**Weaknesses:**")
                for item in stat.top_weaknesses:
                    lines.append(f"- {item}")
                lines.append("")

        # Key insights
        if s.key_insights:
            lines.append("## Key Insights")
            lines.append("")
            for insight in s.key_insights:
                lines.append(f"- {insight}")
            lines.append("")

    # Detailed per-prompt evaluations
    lines.append("## Detailed Evaluations")
    lines.append("")
    for i, e in enumerate(result.evaluations, 1):
        lines.append(f"### Prompt {i} ({e.category})")
        lines.append(f"**Prompt:** {e.prompt_text}")
        lines.append("")
        lines.append(f"**Winner:** {e.winner}")
        lines.append("")
        for name in all_companies:
            mention = e.company_mentions.get(name)
            if mention and mention.mentioned:
                lines.append(f"**{name}:** sentiment {mention.sentiment:+.1f}")
                if mention.strengths_mentioned:
                    lines.append(f"  - Strengths: {', '.join(mention.strengths_mentioned)}")
                if mention.weaknesses_mentioned:
                    lines.append(f"  - Weaknesses: {', '.join(mention.weaknesses_mentioned)}")
                lines.append("")

        if e.analysis_notes:
            lines.append(f"*{e.analysis_notes}*")
            lines.append("")

        lines.append("<details><summary>Full LLM Response</summary>")
        lines.append("")
        lines.append(e.llm_response)
        lines.append("")
        lines.append("</details>")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
