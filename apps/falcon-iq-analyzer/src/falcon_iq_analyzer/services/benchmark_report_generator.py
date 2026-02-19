from __future__ import annotations

from falcon_iq_analyzer.models.domain import BenchmarkResult


def generate_benchmark_report(result: BenchmarkResult) -> str:
    """Generate a Markdown benchmark report."""
    lines: list[str] = []
    s = result.summary
    a = result.company_a
    b = result.company_b

    lines.append(f"# LLM Benchmark Report: {a} vs {b}")
    lines.append("")

    # Summary scorecard
    if s:
        lines.append("## Summary Scorecard")
        lines.append("")
        total = s.total_prompts or 1
        a_pct = round(s.company_a_wins / total * 100)
        b_pct = round(s.company_b_wins / total * 100)
        lines.append(f"| Metric | {a} | {b} |")
        lines.append("|--------|------|------|")
        lines.append(f"| Wins | {s.company_a_wins} ({a_pct}%) | {s.company_b_wins} ({b_pct}%) |")
        lines.append(f"| Ties | {s.ties} | {s.ties} |")
        lines.append(f"| Avg Sentiment | {s.company_a_avg_sentiment:+.2f} | {s.company_b_avg_sentiment:+.2f} |")
        lines.append(f"| Total Prompts | {s.total_prompts} | {s.total_prompts} |")
        lines.append("")

        # Win rates by category
        categories: dict[str, dict[str, int]] = {}
        for e in result.evaluations:
            cat = e.category
            if cat not in categories:
                categories[cat] = {"company_a": 0, "company_b": 0, "tie": 0, "neither": 0}
            categories[cat][e.winner] = categories[cat].get(e.winner, 0) + 1

        if categories:
            lines.append("## Win Rates by Category")
            lines.append("")
            lines.append(f"| Category | {a} Wins | {b} Wins | Ties | Neither |")
            lines.append("|----------|---------|---------|------|---------|")
            for cat, counts in sorted(categories.items()):
                lines.append(f"| {cat} | {counts.get('company_a', 0)} | {counts.get('company_b', 0)} | {counts.get('tie', 0)} | {counts.get('neither', 0)} |")
            lines.append("")

        # Company perception
        lines.append(f"## {a} — LLM Perception")
        lines.append("")
        if s.company_a_top_strengths:
            lines.append("**Strengths:**")
            for item in s.company_a_top_strengths:
                lines.append(f"- {item}")
            lines.append("")
        if s.company_a_top_weaknesses:
            lines.append("**Weaknesses:**")
            for item in s.company_a_top_weaknesses:
                lines.append(f"- {item}")
            lines.append("")

        lines.append(f"## {b} — LLM Perception")
        lines.append("")
        if s.company_b_top_strengths:
            lines.append("**Strengths:**")
            for item in s.company_b_top_strengths:
                lines.append(f"- {item}")
            lines.append("")
        if s.company_b_top_weaknesses:
            lines.append("**Weaknesses:**")
            for item in s.company_b_top_weaknesses:
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
        if e.company_a_mention and e.company_a_mention.mentioned:
            m = e.company_a_mention
            lines.append(f"**{a}:** sentiment {m.sentiment:+.1f}")
            if m.strengths_mentioned:
                lines.append(f"  - Strengths: {', '.join(m.strengths_mentioned)}")
            if m.weaknesses_mentioned:
                lines.append(f"  - Weaknesses: {', '.join(m.weaknesses_mentioned)}")
            lines.append("")
        if e.company_b_mention and e.company_b_mention.mentioned:
            m = e.company_b_mention
            lines.append(f"**{b}:** sentiment {m.sentiment:+.1f}")
            if m.strengths_mentioned:
                lines.append(f"  - Strengths: {', '.join(m.strengths_mentioned)}")
            if m.weaknesses_mentioned:
                lines.append(f"  - Weaknesses: {', '.join(m.weaknesses_mentioned)}")
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
