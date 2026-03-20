from __future__ import annotations

import logging
import re
from collections import Counter

from falcon_iq_analyzer.llm.base import LLMClient
from falcon_iq_analyzer.llm.multi_benchmark_prompts import (
    MULTI_BENCHMARK_ANALYZE_SYSTEM,
    MULTI_BENCHMARK_ANALYZE_USER,
    MULTI_BENCHMARK_GENERATE_SYSTEM,
    MULTI_BENCHMARK_GENERATE_USER,
    MULTI_BENCHMARK_SUMMARIZE_SYSTEM,
    MULTI_BENCHMARK_SUMMARIZE_USER,
    PRODUCT_GROUPING_SYSTEM,
    PRODUCT_GROUPING_USER,
)
from falcon_iq_analyzer.llm.prompts import BENCHMARK_EVAL_SYSTEM
from falcon_iq_analyzer.models.company_benchmark import (
    CompanyOverview,
    MultiCompanyBenchmarkResult,
    MultiCompanyBenchmarkSummary,
    MultiCompanyPromptEvaluation,
    MultiCompanyStats,
    ProductComparisonEntry,
    ProductComparisonGroup,
)
from falcon_iq_analyzer.models.domain import (
    AnalysisResult,
    CompanyMention,
    GeneratedPrompt,
)

logger = logging.getLogger(__name__)


# ── Helpers: extract structured data from analysis results ───────────────


def _offerings_to_text(result: AnalysisResult) -> str:
    lines: list[str] = []
    for o in result.top_offerings:
        lines.append(f"- {o.product_name} ({o.category}): {o.description}")
        if o.key_features:
            lines.append(f"  Features: {', '.join(o.key_features[:5])}")
    return "\n".join(lines)


def _extract_categories(results: list[AnalysisResult]) -> list[str]:
    """Extract unique product categories across all analysis results."""
    cats: set[str] = set()
    for r in results:
        for o in r.top_offerings:
            if o.category:
                cats.add(o.category)
    return sorted(cats)


def _extract_features_by_company(
    results: list[AnalysisResult],
) -> dict[str, list[str]]:
    """Extract real features per company (up to 10 per company)."""
    out: dict[str, list[str]] = {}
    for r in results:
        feats: list[str] = []
        for o in r.top_offerings:
            feats.extend(o.key_features[:5])
        out[r.company_name] = feats[:10]
    return out


def _format_features_by_company(
    features: dict[str, list[str]],
) -> str:
    lines: list[str] = []
    for company, feats in features.items():
        if feats:
            lines.append(f"{company}: {', '.join(feats)}")
    return "\n".join(lines)


# ── Context block builders ───────────────────────────────────────────────


def _build_context_block_for_companies(
    results: list[AnalysisResult],
) -> str:
    """Format AnalysisResult data as text simulating user pasting from websites.

    Includes up to 3 offerings per company, 5 features each, 200 char cap.
    """
    sections: list[str] = []
    for result in results:
        lines: list[str] = [f"--- {result.company_name} ---"]
        for offering in result.top_offerings[:3]:
            desc = offering.description[:200]
            if len(offering.description) > 200:
                desc += "..."
            lines.append(f"Product: {offering.product_name}")
            lines.append(f"Category: {offering.category}")
            lines.append(f"Description: {desc}")
            if offering.key_features:
                features = ", ".join(offering.key_features[:5])
                lines.append(f"Features: {features}")
            if offering.target_audience:
                lines.append(f"For: {offering.target_audience}")
            lines.append("")
        sections.append("\n".join(lines))
    return "\n".join(sections)


def _resolve_context_placeholder(
    prompt_text: str,
    results_by_name: dict[str, AnalysisResult],
    all_results: list[AnalysisResult],
) -> tuple[str, str]:
    """Replace [CONTEXT] or [CONTEXT:co1,co2] with actual data.

    Returns (resolved_prompt_text, context_block_used).
    """
    # Check for targeted context: [CONTEXT:company1,company2]
    targeted = re.search(r"\[CONTEXT:([^\]]+)\]", prompt_text)
    if targeted:
        names = [n.strip() for n in targeted.group(1).split(",")]
        subset = [results_by_name[n] for n in names if n in results_by_name]
        if not subset:
            subset = all_results
        block = _build_context_block_for_companies(subset)
        resolved = prompt_text.replace(targeted.group(0), block)
        return resolved, block

    # Generic [CONTEXT] — use all companies
    if "[CONTEXT]" in prompt_text:
        block = _build_context_block_for_companies(all_results)
        return prompt_text.replace("[CONTEXT]", block), block

    # No placeholder — append full context
    block = _build_context_block_for_companies(all_results)
    resolved = f"{prompt_text}\n\nHere's what I found on their websites:\n{block}"
    return resolved, block


# ── Distribution ─────────────────────────────────────────────────────────


def _compute_distribution(num_prompts: int) -> dict[str, int]:
    """Prompt type distribution:

    ~50% context_injected, ~15% feature_specific, ~15% category_specific,
    ~10% url_query, ~10% generic.
    Context-carrying types (first 3) get product data injected so the LLM
    can actually differentiate niche companies.
    """
    context_injected = round(num_prompts * 0.50)
    feature_specific = round(num_prompts * 0.15)
    category_specific = round(num_prompts * 0.15)
    url_query = round(num_prompts * 0.10)
    generic = num_prompts - context_injected - feature_specific - category_specific - url_query
    # Ensure baseline types get at least 1 each
    if url_query < 1:
        url_query = 1
        context_injected -= 1
    if generic < 1:
        generic = 1
        context_injected -= 1
    return {
        "context_injected": context_injected,
        "feature_specific": feature_specific,
        "category_specific": category_specific,
        "url_query": url_query,
        "generic": generic,
    }


# ── Prompt generation ────────────────────────────────────────────────────


_BATCH_SIZE = 25  # max prompts per LLM call to avoid output truncation


async def _generate_prompt_batch(
    llm: LLMClient,
    system_prompt: str,
    main_company: str,
    main_offerings: str,
    competitor_sections: str,
    categories_list: str,
    features_by_company_text: str,
    batch_distribution: dict[str, int],
    batch_size: int,
    batch_num: int,
) -> list[GeneratedPrompt]:
    """Generate a single batch of prompts."""
    user_prompt = MULTI_BENCHMARK_GENERATE_USER.format(
        main_company=main_company,
        main_offerings=main_offerings,
        competitor_sections=competitor_sections,
        categories_list=categories_list,
        features_by_company=features_by_company_text,
        num_prompts=batch_size,
        url_query_count=batch_distribution["url_query"],
        context_injected_count=batch_distribution["context_injected"],
        feature_specific_count=batch_distribution["feature_specific"],
        category_specific_count=batch_distribution["category_specific"],
        generic_count=batch_distribution["generic"],
    )

    data = await llm.complete_json(system_prompt, user_prompt)
    raw_prompts = data.get("prompts", [])

    # Re-number prompt IDs to be globally unique across batches
    prompts: list[GeneratedPrompt] = []
    for i, p in enumerate(raw_prompts):
        p["prompt_id"] = f"p{batch_num * _BATCH_SIZE + i + 1}"
        prompts.append(GeneratedPrompt(**p))

    return prompts


async def generate_multi_prompts(
    llm: LLMClient,
    main_result: AnalysisResult,
    competitor_results: list[AnalysisResult],
    num_prompts: int = 100,
) -> list[GeneratedPrompt]:
    """Generate realistic buyer prompts given a main company + N competitors.

    For large counts (>BATCH_SIZE), splits into batches so the LLM output
    doesn't get truncated.
    """
    all_results = [main_result] + competitor_results
    results_by_name = {r.company_name: r for r in all_results}

    main_offerings = _offerings_to_text(main_result)

    competitor_sections_parts: list[str] = []
    for comp in competitor_results:
        competitor_sections_parts.append(f"{comp.company_name}:\n{_offerings_to_text(comp)}")
    competitor_sections = "\n\n".join(competitor_sections_parts)

    # Extract structured data for grounded prompts
    categories = _extract_categories(all_results)
    features_by_company = _extract_features_by_company(all_results)
    categories_list = ", ".join(categories) if categories else "N/A"
    features_text = _format_features_by_company(features_by_company)

    total_distribution = _compute_distribution(num_prompts)

    # Split into batches
    num_batches = max(1, (num_prompts + _BATCH_SIZE - 1) // _BATCH_SIZE)
    all_prompts: list[GeneratedPrompt] = []

    for batch_idx in range(num_batches):
        batch_start = batch_idx * _BATCH_SIZE
        batch_size = min(_BATCH_SIZE, num_prompts - batch_start)

        # Distribute prompt types proportionally per batch
        batch_dist = _compute_distribution(batch_size)

        logger.info(
            "Generating prompt batch %d/%d (%d prompts)",
            batch_idx + 1,
            num_batches,
            batch_size,
        )

        batch_prompts = await _generate_prompt_batch(
            llm=llm,
            system_prompt=MULTI_BENCHMARK_GENERATE_SYSTEM,
            main_company=main_result.company_name,
            main_offerings=main_offerings,
            competitor_sections=competitor_sections,
            categories_list=categories_list,
            features_by_company_text=features_text,
            batch_distribution=batch_dist,
            batch_size=batch_size,
            batch_num=batch_idx,
        )
        all_prompts.extend(batch_prompts)

    # Post-process: inject context blocks for all context-carrying prompt types
    # (context_injected, feature_specific, category_specific all get product data)
    _context_types = {"context_injected", "feature_specific", "category_specific"}
    for prompt in all_prompts:
        if prompt.prompt_type in _context_types:
            prompt.prompt_text, prompt.context_block = _resolve_context_placeholder(
                prompt.prompt_text, results_by_name, all_results
            )

    logger.info(
        "Generated %d multi-company prompts for %s vs %d competitors (distribution: %s)",
        len(all_prompts),
        main_result.company_name,
        len(competitor_results),
        {pt: sum(1 for p in all_prompts if p.prompt_type == pt) for pt in total_distribution},
    )
    return all_prompts


# ── Evaluation ───────────────────────────────────────────────────────────


async def evaluate_single_prompt_multi(
    llm: LLMClient,
    prompt: GeneratedPrompt,
    company_names: list[str],
) -> MultiCompanyPromptEvaluation:
    """Evaluate a single prompt: send to LLM, then analyze the response."""
    # Step 1: send prompt as a regular user query
    llm_response = await llm.complete(BENCHMARK_EVAL_SYSTEM, prompt.prompt_text)

    # Step 2: analyze the response for all companies
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
            prompt_type=prompt.prompt_type,
            llm_response=llm_response,
            winner="neither",
            analysis_notes="Analysis failed",
        )

    raw_mentions = analysis.get("company_mentions", {})
    company_mentions: dict[str, CompanyMention] = {}
    for name, mention_data in raw_mentions.items():
        if isinstance(mention_data, dict):
            company_mentions[name] = CompanyMention(**mention_data)

    return MultiCompanyPromptEvaluation(
        prompt_id=prompt.prompt_id,
        prompt_text=prompt.prompt_text,
        category=prompt.category,
        prompt_type=prompt.prompt_type,
        llm_response=llm_response,
        company_mentions=company_mentions,
        winner=analysis.get("winner", "neither"),
        analysis_notes=analysis.get("analysis_notes", ""),
    )


# ── Summarization ────────────────────────────────────────────────────────


async def summarize_multi_evaluations(
    llm: LLMClient,
    company_names: list[str],
    evaluations: list[MultiCompanyPromptEvaluation],
) -> MultiCompanyBenchmarkSummary:
    """Aggregate all evaluations into a multi-company benchmark summary."""
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

    # Build evaluation details (include prompt_type)
    details_lines: list[str] = []
    for e in evaluations:
        details_lines.append(f"Prompt ({e.category}, type={e.prompt_type}): {e.prompt_text[:200]}")
        details_lines.append(f"  Winner: {e.winner}")
        for name in company_names:
            mention = e.company_mentions.get(name)
            if mention:
                details_lines.append(
                    f"  {name}: sentiment={mention.sentiment}, "
                    f"strengths={mention.strengths_mentioned}, "
                    f"weaknesses={mention.weaknesses_mentioned}"
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

    # Average sentiments per company
    sentiment_accum: dict[str, list[float]] = {name: [] for name in company_names}
    for e in evaluations:
        for name in company_names:
            mention = e.company_mentions.get(name)
            if mention and mention.mentioned:
                sentiment_accum[name].append(mention.sentiment)

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


# ── Product category normalization ────────────────────────────────────────


async def normalize_product_categories(
    llm: LLMClient,
    company_overviews: dict[str, CompanyOverview],
) -> list[ProductComparisonGroup]:
    """Use a single LLM call to group all offerings into 2-4 normalized categories."""
    # Build a flat text representation of all offerings
    lines: list[str] = []
    for name, overview in company_overviews.items():
        for o in overview.top_offerings:
            features = ", ".join(o.key_features[:5]) if o.key_features else "N/A"
            lines.append(
                f"- Company: {name} | Product: {o.product_name} | "
                f"Category: {o.category} | Description: {o.description} | "
                f"Features: {features}"
            )

    if not lines:
        return []

    offerings_text = "\n".join(lines)
    user_prompt = PRODUCT_GROUPING_USER.format(offerings_text=offerings_text)

    try:
        data = await llm.complete_json(PRODUCT_GROUPING_SYSTEM, user_prompt)
    except Exception:
        logger.exception("Failed to normalize product categories — falling back to raw categories")
        return []

    groups: list[ProductComparisonGroup] = []
    for g in data.get("groups", []):
        if not isinstance(g, dict):
            continue
        entries = [ProductComparisonEntry(**e) for e in g.get("entries", []) if isinstance(e, dict)]
        groups.append(
            ProductComparisonGroup(
                group_name=g.get("group_name", "Other"),
                group_description=g.get("group_description", ""),
                entries=entries,
            )
        )

    logger.info(
        "Normalized %d offerings into %d comparison groups: %s",
        len(lines),
        len(groups),
        [g.group_name for g in groups],
    )
    return groups


# ── Markdown report ──────────────────────────────────────────────────────


def generate_multi_benchmark_report(
    result: MultiCompanyBenchmarkResult,
) -> str:
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

        header = "| Metric |"
        separator = "|--------|"
        for name in all_companies:
            header += f" {name} |"
            separator += "------|"
        lines.append(header)
        lines.append(separator)

        wins_row = "| Wins |"
        for name in all_companies:
            stat = next(
                (cs for cs in s.company_stats if cs.company_name == name),
                None,
            )
            wins = stat.wins if stat else 0
            pct = round(wins / total * 100)
            wins_row += f" {wins} ({pct}%) |"
        lines.append(wins_row)

        ties_row = "| Ties |"
        for _ in all_companies:
            ties_row += f" {s.ties} |"
        lines.append(ties_row)

        sentiment_row = "| Avg Sentiment |"
        for name in all_companies:
            stat = next(
                (cs for cs in s.company_stats if cs.company_name == name),
                None,
            )
            avg = stat.avg_sentiment if stat else 0.0
            sentiment_row += f" {avg:+.2f} |"
        lines.append(sentiment_row)

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

        # Win rates by prompt type
        prompt_types: dict[str, Counter[str]] = {}
        for e in result.evaluations:
            pt = e.prompt_type
            if pt not in prompt_types:
                prompt_types[pt] = Counter()
            prompt_types[pt][e.winner] += 1

        if prompt_types:
            lines.append("## Win Rates by Prompt Type")
            lines.append("")
            pt_header = "| Prompt Type |"
            pt_sep = "|-------------|"
            for name in all_companies:
                pt_header += f" {name} |"
                pt_sep += "------|"
            pt_header += " Ties | Neither | Total |"
            pt_sep += "------|---------|-------|"
            lines.append(pt_header)
            lines.append(pt_sep)
            for pt, counts in sorted(prompt_types.items()):
                pt_total = sum(counts.values())
                row = f"| {pt} |"
                for name in all_companies:
                    row += f" {counts.get(name, 0)} |"
                row += f" {counts.get('tie', 0)} | {counts.get('neither', 0)} | {pt_total} |"
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
        lines.append(f"### Prompt {i} ({e.category}) [{e.prompt_type}]")
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
