from __future__ import annotations

from falcon_iq_analyzer.models.domain import AnalysisResult


def generate_markdown_report(result: AnalysisResult) -> str:
    """Generate a Markdown report from the analysis result."""
    lines: list[str] = []

    lines.append(f"# Web Analysis Report: {result.company_name}")
    lines.append("")
    lines.append(f"**Total pages crawled:** {result.total_pages}")
    lines.append(f"**Pages analyzed (after locale filter):** {result.filtered_pages}")
    lines.append(f"**Product pages analyzed:** {result.product_pages_analyzed}")
    lines.append("")

    # Classification summary
    lines.append("## Page Classification Summary")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for category, count in sorted(result.classification_summary.items(), key=lambda x: -x[1]):
        lines.append(f"| {category} | {count} |")
    lines.append("")

    # Top offerings
    lines.append("## Top 5 Core Product Offerings")
    lines.append("")
    for offering in result.top_offerings:
        lines.append(f"### {offering.rank}. {offering.product_name}")
        lines.append(f"**Category:** {offering.category}")
        lines.append("")
        lines.append(offering.description)
        lines.append("")

        if offering.key_features:
            lines.append("**Key Features:**")
            for feat in offering.key_features:
                lines.append(f"- {feat}")
            lines.append("")

        if offering.key_benefits:
            lines.append("**Key Benefits:**")
            for ben in offering.key_benefits:
                lines.append(f"- {ben}")
            lines.append("")

        if offering.target_audience:
            lines.append(f"**Target Audience:** {offering.target_audience}")
            lines.append("")

        if offering.selling_script:
            lines.append("**Selling Script:**")
            lines.append(f"> {offering.selling_script}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)
