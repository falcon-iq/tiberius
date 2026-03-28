"""Generate a self-contained HTML benchmark report from MultiCompanyBenchmarkResult."""

from __future__ import annotations

import html
from datetime import datetime, timezone

from falcon_iq_analyzer.models.company_benchmark import (
    MultiCompanyBenchmarkResult,
    MultiCompanyStats,
)

# ── Colour palette (one per company, cycles if > 6) ──────────────────────────

_PALETTE = [
    ("#6366f1", "#818cf8", "rgba(99,102,241,0.12)"),  # indigo
    ("#f43f5e", "#fb7185", "rgba(244,63,94,0.12)"),  # rose
    ("#10b981", "#34d399", "rgba(16,185,129,0.12)"),  # emerald
    ("#f59e0b", "#fbbf24", "rgba(245,158,11,0.12)"),  # amber
    ("#3b82f6", "#60a5fa", "rgba(59,130,246,0.12)"),  # blue
    ("#8b5cf6", "#a78bfa", "rgba(139,92,246,0.12)"),  # violet
]


def _color(index: int) -> tuple[str, str, str]:
    return _PALETTE[index % len(_PALETTE)]


def _esc(text: str) -> str:
    return html.escape(str(text))


def _sentiment_badge(value: float) -> str:
    if value >= 0.3:
        cls = "badge-positive"
    elif value <= -0.3:
        cls = "badge-negative"
    else:
        cls = "badge-neutral"
    return f'<span class="badge {cls}">{value:+.2f}</span>'


def _winner_badge(winner: str, main_company: str) -> str:
    if winner == "tie":
        return '<span class="badge badge-neutral">Tie</span>'
    if winner == "neither":
        return '<span class="badge badge-muted">Neither</span>'
    if winner == main_company:
        return f'<span class="badge badge-positive">{_esc(winner)}</span>'
    return f'<span class="badge badge-competitor">{_esc(winner)}</span>'


def _stat_for(stats: list[MultiCompanyStats], name: str) -> MultiCompanyStats | None:
    return next((s for s in stats if s.company_name == name), None)


# ── External Validation renderer ──────────────────────────────────────────────


def _render_external_validation(result, all_companies: list[str]) -> str:
    """Render the External Validation section with ratings, company facts, and G2 highlights."""
    has_enrichment = any(
        (result.company_overviews.get(name) and result.company_overviews[name].enrichment) for name in all_companies
    )
    if not has_enrichment:
        return ""

    # Ratings comparison table
    rating_rows = ""
    sources = ["G2", "Capterra", "TrustRadius", "Trustpilot", "GetApp"]
    for source in sources:
        cells = ""
        has_any = False
        for name in all_companies:
            ov = result.company_overviews.get(name)
            enr = ov.enrichment if ov else None
            val = ""
            if enr:
                if source == "G2" and enr.g2 and enr.g2.rating is not None:
                    val = f"{enr.g2.rating}/5 <span class='badge badge-neutral'>({enr.g2.review_count})</span>"
                    has_any = True
                else:
                    for rs in enr.review_sites:
                        if rs.site_name.lower() == source.lower() and rs.rating is not None:
                            r_display = f"{rs.rating}/5" if rs.rating <= 5 else f"{rs.rating}/10"
                            val = f"{r_display} <span class='badge badge-neutral'>({rs.review_count})</span>"
                            has_any = True
                            break
            empty = '<span style="color:var(--text-muted)">—</span>'
            cells += f"<td>{val or empty}</td>"
        if has_any:
            rating_rows += f"<tr><td style='font-weight:600;'>{source}</td>{cells}</tr>"

    ratings_html = ""
    if rating_rows:
        header = "".join(f"<th>{_esc(n)}</th>" for n in all_companies)
        ratings_html = f"""
        <table class="cat-table">
            <thead><tr><th style="text-align:left;">Source</th>{header}</tr></thead>
            <tbody>{rating_rows}</tbody>
        </table>"""

    # Company facts
    facts_cards = ""
    for i, name in enumerate(all_companies):
        ov = result.company_overviews.get(name)
        enr = ov.enrichment if ov else None
        if not enr or not enr.crunchbase:
            continue
        cb = enr.crunchbase
        primary, _, bg = _color(i)
        items = ""
        if cb.founded:
            items += f"<div class='fact-item'><span class='fact-label'>Founded</span> {_esc(cb.founded)}</div>"
        if cb.hq:
            items += f"<div class='fact-item'><span class='fact-label'>HQ</span> {_esc(cb.hq)}</div>"
        if cb.employee_count:
            items += f"<div class='fact-item'><span class='fact-label'>Employees</span> {_esc(cb.employee_count)}</div>"
        if cb.total_funding:
            funding_esc = _esc(cb.total_funding)
            items += f"<div class='fact-item'><span class='fact-label'>Valuation/Funding</span> {funding_esc}</div>"
        if items:
            facts_cards += f"""
            <div class="score-card" style="border-top:3px solid {primary};text-align:left;">
                <div class="score-company" style="margin-bottom:0.5rem;">{_esc(name)}</div>
                {items}
            </div>"""

    # G2 review highlights
    g2_highlights = ""
    for i, name in enumerate(all_companies):
        ov = result.company_overviews.get(name)
        enr = ov.enrichment if ov else None
        if not enr or not enr.g2:
            continue
        g2 = enr.g2
        if not g2.pros_themes and not g2.cons_themes:
            continue
        primary, _, _ = _color(i)
        pros = "".join(f"<li style='color:var(--positive);'>{_esc(t.theme[:120])}</li>" for t in g2.pros_themes[:3])
        cons = "".join(f"<li style='color:var(--negative);'>{_esc(t.theme[:120])}</li>" for t in g2.cons_themes[:3])
        pros_section = (
            (
                f'<div style="margin-bottom:0.5rem;"><strong>Pros:</strong>'
                f'<ul style="margin:0.25rem 0 0 1rem;">{pros}</ul></div>'
            )
            if pros
            else ""
        )
        cons_section = (
            (f'<div><strong>Cons:</strong><ul style="margin:0.25rem 0 0 1rem;">{cons}</ul></div>') if cons else ""
        )
        g2_highlights += f"""
        <div class="score-card" style="border-top:3px solid {primary};text-align:left;">
            <div class="score-company" style="margin-bottom:0.5rem;">{_esc(name)} — G2 Reviews</div>
            {pros_section}
            {cons_section}
        </div>"""

    # Verified claims summary
    claims_html = ""
    for i, name in enumerate(all_companies):
        ov = result.company_overviews.get(name)
        if not ov or not ov.verified_claims:
            continue
        verified = sum(1 for c in ov.verified_claims if c.status == "verified")
        contradicted = sum(1 for c in ov.verified_claims if c.status == "contradicted")
        unverified = sum(1 for c in ov.verified_claims if c.status == "unverified")
        primary, _, _ = _color(i)
        claims_html += f"""
        <div style="display:inline-flex;gap:0.5rem;align-items:center;margin-right:1.5rem;">
            <span style="font-weight:600;color:{primary};">{_esc(name)}</span>
            <span class="badge badge-positive">{verified} verified</span>
            <span class="badge badge-negative">{contradicted} contradicted</span>
            <span class="badge badge-neutral">{unverified} unverified</span>
        </div>"""

    if not ratings_html and not facts_cards and not g2_highlights:
        return ""

    return f"""
    <div class="section">
        <div class="section-title"><span class="section-icon">&#9989;</span> External Validation</div>
        {ratings_html}
        {f'<div class="scorecard-grid" style="margin-top:1rem;">{facts_cards}</div>' if facts_cards else ""}
        {f'<div class="scorecard-grid" style="margin-top:1rem;">{g2_highlights}</div>' if g2_highlights else ""}
        {f'<div style="margin-top:1rem;">{claims_html}</div>' if claims_html else ""}
    </div>"""


def _render_fact_check_section(result, all_companies: list[str]) -> str:
    """Render the Fact-Check Scorecard showing LLM accuracy per evaluation."""
    if not result.evaluations:
        return ""

    # Check if any evaluation has fact-check data
    has_fact_checks = any(e.factual_accuracy > 0 for e in result.evaluations)
    if not has_fact_checks:
        return ""

    # Aggregate stats
    scored_evals = [e for e in result.evaluations if e.factual_accuracy > 0]
    avg_accuracy = sum(e.factual_accuracy for e in scored_evals) / len(scored_evals) if scored_evals else 0.0
    total_confirmed = sum(len(e.facts_confirmed) for e in result.evaluations)
    total_hallucinated = sum(len(e.facts_hallucinated) for e in result.evaluations)
    total_gaps = sum(len(e.knowledge_gaps) for e in result.evaluations)

    # Accuracy color
    if avg_accuracy >= 0.7:
        acc_color = "var(--positive)"
    elif avg_accuracy >= 0.4:
        acc_color = "var(--neutral)"
    else:
        acc_color = "var(--negative)"

    # Top hallucinations (deduplicated, most common)
    all_hallucinations: list[str] = []
    for e in result.evaluations:
        all_hallucinations.extend(e.facts_hallucinated)
    top_hallucinations = ""
    if all_hallucinations:
        # Deduplicate and take top 5
        seen: set[str] = set()
        unique: list[str] = []
        for h in all_hallucinations:
            if h not in seen:
                seen.add(h)
                unique.append(h)
        top_hallucinations = "".join(
            f"<li style='color:var(--negative);font-size:0.85rem;'>{_esc(h[:150])}</li>" for h in unique[:5]
        )

    return f"""
    <div class="section">
        <div class="section-title"><span class="section-icon">&#128269;</span> Fact-Check Scorecard</div>
        <div class="scorecard-grid">
            <div class="score-card" style="border-top:4px solid {acc_color};">
                <div class="score-company">Avg Factual Accuracy</div>
                <div class="score-wins" style="color:{acc_color};">{avg_accuracy:.0%}</div>
                <div class="score-label">across {len(scored_evals)} evaluated prompts</div>
            </div>
            <div class="score-card" style="border-top:4px solid var(--positive);">
                <div class="score-company">Facts Confirmed</div>
                <div class="score-wins" style="color:var(--positive);">{total_confirmed}</div>
                <div class="score-label">claims matched external data</div>
            </div>
            <div class="score-card" style="border-top:4px solid var(--negative);">
                <div class="score-company">Hallucinations</div>
                <div class="score-wins" style="color:var(--negative);">{total_hallucinated}</div>
                <div class="score-label">fabricated claims detected</div>
            </div>
            <div class="score-card" style="border-top:4px solid var(--neutral);">
                <div class="score-company">Knowledge Gaps</div>
                <div class="score-wins" style="color:var(--neutral);">{total_gaps}</div>
                <div class="score-label">known facts LLM missed</div>
            </div>
        </div>
        {
        f'<div style="margin-top:1rem;"><strong>Top hallucinated claims:</strong>'
        f'<ul style="margin:0.5rem 0 0 1rem;">{top_hallucinations}</ul></div>'
        if top_hallucinations
        else ""
    }
    </div>"""


# ── Main generator ────────────────────────────────────────────────────────────


def generate_html_report(result: MultiCompanyBenchmarkResult) -> str:
    """Return a fully self-contained HTML string for the benchmark report."""

    all_companies = [result.main_company] + result.competitors
    s = result.summary
    total = s.total_prompts if s and s.total_prompts else 1
    generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    # ── Company overview cards ─────────────────────────────────────────────
    company_cards_html = ""
    for i, name in enumerate(all_companies):
        overview = result.company_overviews.get(name)
        primary, _, bg = _color(i)
        is_main_tag = (
            f'<span class="co-you-badge" style="background:{bg};color:{primary};">You</span>'
            if name == result.main_company
            else ""
        )

        if overview and overview.logo_url:
            logo_html = (
                f'<img src="{_esc(overview.logo_url)}" alt="{_esc(name)}" '
                f'class="co-logo" onerror="this.style.display=\'none\';'
                f"this.nextElementSibling.style.display='flex'\">"
                f'<div class="co-logo-fallback" style="display:none;'
                f'background:linear-gradient(135deg,{primary},#a855f7)">'
                f"{_esc(name[0].upper())}</div>"
            )
        else:
            logo_html = (
                f'<div class="co-logo-fallback" '
                f'style="background:linear-gradient(135deg,{primary},#a855f7)">'
                f"{_esc(name[0].upper())}</div>"
            )

        url_html = ""
        if overview and overview.url:
            url_html = (
                f'<a href="{_esc(overview.url)}" target="_blank" rel="noopener" class="co-url">{_esc(overview.url)}</a>'
            )

        tagline_html = ""
        if overview and overview.tagline:
            tagline_html = f'<div class="co-tagline">{_esc(overview.tagline)}</div>'

        cat_badges = ""
        if overview and overview.categories:
            cat_badges = "".join(f'<span class="co-cat-badge">{_esc(c)}</span>' for c in overview.categories)

        company_cards_html += f"""
        <div class="co-card" style="border-top:3px solid {primary};">
            <div class="co-header">
                {logo_html}
                <div class="co-identity">
                    <div class="co-name">{_esc(name)} {is_main_tag}</div>
                    {url_html}
                </div>
            </div>
            {tagline_html}
            {f'<div class="co-categories">{cat_badges}</div>' if cat_badges else ""}
        </div>"""

    # ── External Validation section ──────────────────────────────────────
    external_validation_html = _render_external_validation(result, all_companies)

    # ── Scorecard cards ───────────────────────────────────────────────────
    scorecard_cards = ""
    if s:
        for i, name in enumerate(all_companies):
            primary, _, bg = _color(i)
            stat = _stat_for(s.company_stats, name)
            wins = stat.wins if stat else 0
            pct = round(wins / total * 100)
            avg_sent = stat.avg_sentiment if stat else 0.0
            is_main = " (You)" if name == result.main_company else ""
            scorecard_cards += f"""
            <div class="score-card" style="border-top:4px solid {primary};">
                <div class="score-company">{_esc(name)}{is_main}</div>
                <div class="score-wins" style="color:{primary};">{wins}</div>
                <div class="score-label">wins out of {total} ({pct}%)</div>
                <div class="score-sentiment">Avg Sentiment {_sentiment_badge(avg_sent)}</div>
            </div>"""

    # ── Ties / neither card ───────────────────────────────────────────────
    if s:
        scorecard_cards += f"""
        <div class="score-card" style="border-top:4px solid #94a3b8;">
            <div class="score-company">Draws</div>
            <div class="score-wins" style="color:#94a3b8;">{s.ties}</div>
            <div class="score-label">ties</div>
            <div class="score-sentiment">{s.neither_mentioned} neither mentioned</div>
        </div>"""

    # ── Win-rate-by-category table ────────────────────────────────────────
    categories: dict[str, dict[str, int]] = {}
    for e in result.evaluations:
        cat = e.category
        if cat not in categories:
            categories[cat] = {}
        categories[cat][e.winner] = categories[cat].get(e.winner, 0) + 1

    cat_header = "".join(f"<th>{_esc(n)}</th>" for n in all_companies)
    cat_rows = ""
    for cat in sorted(categories):
        counts = categories[cat]
        cells = ""
        for name in all_companies:
            c = counts.get(name, 0)
            cells += f"<td>{c}</td>" if c == 0 else f'<td class="highlight">{c}</td>'
        tie_c = counts.get("tie", 0)
        nei_c = counts.get("neither", 0)
        cat_rows += f"<tr><td class='cat-name'>{_esc(cat)}</td>{cells}<td>{tie_c}</td><td>{nei_c}</td></tr>"

    # ── Win-rate-by-prompt-type table ──────────────────────────────────────
    prompt_types: dict[str, dict[str, int]] = {}
    for e in result.evaluations:
        pt = e.prompt_type
        if pt not in prompt_types:
            prompt_types[pt] = {}
        prompt_types[pt][e.winner] = prompt_types[pt].get(e.winner, 0) + 1

    pt_header = "".join(f"<th>{_esc(n)}</th>" for n in all_companies)
    pt_rows = ""
    for pt in sorted(prompt_types):
        counts = prompt_types[pt]
        pt_total = sum(counts.values())
        cells = ""
        for name in all_companies:
            c = counts.get(name, 0)
            cells += f"<td>{c}</td>" if c == 0 else f'<td class="highlight">{c}</td>'
        tie_c = counts.get("tie", 0)
        nei_c = counts.get("neither", 0)
        pt_rows += (
            f"<tr><td class='cat-name'>{_esc(pt)}</td>{cells}<td>{tie_c}</td><td>{nei_c}</td><td>{pt_total}</td></tr>"
        )

    # ── Company perception sections ───────────────────────────────────────
    perception_html = ""
    if s:
        for i, stat in enumerate(s.company_stats):
            primary, _, bg = _color(i)
            strengths = (
                "".join(f"<li>{_esc(st)}</li>" for st in stat.top_strengths)
                if stat.top_strengths
                else "<li>None identified</li>"
            )
            weaknesses = (
                "".join(f"<li>{_esc(w)}</li>" for w in stat.top_weaknesses)
                if stat.top_weaknesses
                else "<li>None identified</li>"
            )
            perception_html += f"""
            <div class="perception-card" style="border-left:4px solid {primary}; background:{bg};">
                <h3 style="color:{primary};">{_esc(stat.company_name)}</h3>
                <div class="perception-cols">
                    <div>
                        <h4>Strengths</h4>
                        <ul class="strength-list">{strengths}</ul>
                    </div>
                    <div>
                        <h4>Weaknesses</h4>
                        <ul class="weakness-list">{weaknesses}</ul>
                    </div>
                </div>
            </div>"""

    # ── Key insights ──────────────────────────────────────────────────────
    insights_html = ""
    if s and s.key_insights:
        for insight in s.key_insights:
            insights_html += f'<div class="insight-item">{_esc(insight)}</div>'

    # ── Product comparison by category ────────────────────────────────
    product_comparison_html = ""
    company_index = {name: i for i, name in enumerate(all_companies)}

    def _render_comparison_table(cat_title: str, cat_desc: str, rows_html: str) -> str:
        desc_html = f'<div class="comp-cat-desc">{_esc(cat_desc)}</div>' if cat_desc else ""
        return (
            f'<div class="comp-category">'
            f'<h3 class="comp-cat-title">{_esc(cat_title)}</h3>'
            f"{desc_html}"
            f'<table class="cat-table comp-table">'
            f'<thead><tr><th style="text-align:left;">Company</th>'
            f'<th style="text-align:left;">Product</th>'
            f'<th style="text-align:left;">Key Features</th></tr></thead>'
            f"<tbody>{rows_html}</tbody></table></div>"
        )

    def _render_offering_row(name: str, product_name: str, key_features: list[str], description: str) -> str:
        idx = company_index.get(name, 0)
        primary, _, _ = _color(idx)
        overview = result.company_overviews.get(name)
        favicon = ""
        if overview and overview.logo_url:
            favicon = (
                f'<img src="{_esc(overview.logo_url)}" '
                f'style="width:20px;height:20px;border-radius:4px;vertical-align:middle;'
                f'background:#fff;margin-right:6px;"'
                f" onerror=\"this.style.display='none'\">"
            )
        if key_features:
            features_html = " ".join(f'<span class="comp-feature">{_esc(f)}</span>' for f in key_features[:5])
        else:
            desc = _esc(description[:120])
            if len(description) > 120:
                desc += "..."
            features_html = f'<span class="comp-desc">{desc}</span>'
        return (
            f"<tr>"
            f'<td style="border-left:3px solid {primary};">'
            f"{favicon}{_esc(name)}</td>"
            f'<td class="comp-product">{_esc(product_name)}</td>'
            f"<td>{features_html}</td>"
            f"</tr>"
        )

    if result.product_comparison_groups:
        # Use LLM-normalized groups
        tables_html = ""
        for group in result.product_comparison_groups:
            rows = ""
            for entry in group.entries:
                rows += _render_offering_row(
                    entry.company_name, entry.product_name, entry.key_features, entry.description
                )
            tables_html += _render_comparison_table(group.group_name, group.group_description, rows)
        product_comparison_html = tables_html
    else:
        # Fallback: group by raw category
        cat_offerings: dict[str, list[tuple[str, int, object]]] = {}
        for i, name in enumerate(all_companies):
            overview = result.company_overviews.get(name)
            if not overview:
                continue
            for offering in overview.top_offerings:
                cat = offering.category or "Other"
                if cat not in cat_offerings:
                    cat_offerings[cat] = []
                cat_offerings[cat].append((name, i, offering))

        if cat_offerings:
            tables_html = ""
            for cat in sorted(cat_offerings):
                entries = cat_offerings[cat]
                rows = ""
                for name, _idx, offering in entries:
                    rows += _render_offering_row(
                        name, offering.product_name, offering.key_features, offering.description
                    )
                tables_html += _render_comparison_table(cat, "", rows)
            product_comparison_html = tables_html

    # ── Detailed evaluations ──────────────────────────────────────────────
    eval_rows = ""
    for idx, e in enumerate(result.evaluations, 1):
        mention_chips = ""
        for name in all_companies:
            mention = e.company_mentions.get(name)
            if mention and mention.mentioned:
                mention_chips += f"""
                <div class="mention-chip">
                    <strong>{_esc(name)}</strong> {_sentiment_badge(mention.sentiment)}
                    {"".join(f'<span class="str-tag">+ {_esc(st)}</span>' for st in mention.strengths_mentioned[:3])}
                    {"".join(f'<span class="wk-tag">- {_esc(w)}</span>' for w in mention.weaknesses_mentioned[:3])}
                </div>"""

        eval_rows += f"""
        <div class="eval-card">
            <div class="eval-header" onclick="this.parentElement.classList.toggle('open')">
                <div class="eval-num">#{idx}</div>
                <div class="eval-meta">
                    <span class="eval-category">{_esc(e.category)}</span>
                    <span class="badge-prompt-type">{_esc(e.prompt_type)}</span>
                    <span class="eval-prompt">{_esc(e.prompt_text)}</span>
                </div>
                <div class="eval-winner">{_winner_badge(e.winner, result.main_company)}</div>
                <div class="eval-chevron">&#9660;</div>
            </div>
            <div class="eval-body">
                <div class="eval-mentions">{mention_chips}</div>
                {f'<div class="eval-notes"><em>{_esc(e.analysis_notes)}</em></div>' if e.analysis_notes else ""}
                <details class="llm-response">
                    <summary>Full LLM Response</summary>
                    <pre>{_esc(e.llm_response)}</pre>
                </details>
            </div>
        </div>"""

    # ── Assemble final HTML ───────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Benchmark Report: {_esc(" vs ".join(all_companies))}</title>
<style>
:root {{
    --bg: #0f172a;
    --surface: #1e293b;
    --surface2: #334155;
    --border: #475569;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --positive: #10b981;
    --negative: #f43f5e;
    --neutral: #f59e0b;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 0;
}}
.container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }}

/* Header */
.report-header {{
    text-align: center;
    padding: 3rem 2rem;
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}}
.report-header h1 {{
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}}
.report-header .subtitle {{
    color: var(--text-muted);
    font-size: 0.95rem;
}}

/* Section */
.section {{ margin-bottom: 2.5rem; }}
.section-title {{
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--surface2);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.section-icon {{ font-size: 1.3rem; }}

/* Scorecard grid */
.scorecard-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}}
.score-card {{
    background: var(--surface);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: transform 0.2s;
}}
.score-card:hover {{ transform: translateY(-2px); }}
.score-company {{ font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem; }}
.score-wins {{ font-size: 2.5rem; font-weight: 800; line-height: 1; }}
.score-label {{ color: var(--text-muted); font-size: 0.85rem; margin: 0.25rem 0; }}
.score-sentiment {{ margin-top: 0.5rem; }}

/* Badges */
.badge {{
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}}
.badge-positive {{ background: rgba(16,185,129,0.15); color: #34d399; }}
.badge-negative {{ background: rgba(244,63,94,0.15); color: #fb7185; }}
.badge-neutral {{ background: rgba(245,158,11,0.15); color: #fbbf24; }}
.badge-muted {{ background: rgba(148,163,184,0.15); color: #94a3b8; }}
.badge-competitor {{ background: rgba(244,63,94,0.15); color: #fb7185; }}
.badge-prompt-type {{
    display: inline-block;
    padding: 0.1rem 0.45rem;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    background: rgba(99,102,241,0.15);
    color: #818cf8;
    margin-left: 0.3rem;
}}

/* Category table */
.cat-table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--surface);
    border-radius: 12px;
    overflow: hidden;
}}
.cat-table th, .cat-table td {{
    padding: 0.75rem 1rem;
    text-align: center;
    border-bottom: 1px solid var(--surface2);
}}
.cat-table th {{
    background: var(--surface2);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
}}
.cat-table td.cat-name {{ text-align: left; font-weight: 500; text-transform: capitalize; }}
.cat-table td.highlight {{ color: var(--positive); font-weight: 700; }}

/* Perception cards */
.perception-card {{
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}}
.perception-card h3 {{ font-size: 1.1rem; margin-bottom: 0.75rem; }}
.perception-card h4 {{
    font-size: 0.85rem; text-transform: uppercase;
    letter-spacing: 0.05em; color: var(--text-muted);
    margin-bottom: 0.5rem;
}}
.perception-cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
.strength-list, .weakness-list {{ list-style: none; padding: 0; }}
.strength-list li::before {{ content: "\\2713 "; color: var(--positive); font-weight: bold; }}
.weakness-list li::before {{ content: "\\2717 "; color: var(--negative); font-weight: bold; }}
.strength-list li, .weakness-list li {{ padding: 0.25rem 0; font-size: 0.9rem; }}

/* Insights */
.insight-item {{
    background: var(--surface);
    border-left: 3px solid #818cf8;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem;
}}

/* Evaluation cards */
.eval-card {{
    background: var(--surface);
    border-radius: 10px;
    margin-bottom: 0.5rem;
    overflow: hidden;
}}
.eval-header {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    cursor: pointer;
    transition: background 0.15s;
}}
.eval-header:hover {{ background: var(--surface2); }}
.eval-num {{
    background: var(--surface2);
    border-radius: 50%;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    flex-shrink: 0;
}}
.eval-meta {{ flex: 1; min-width: 0; }}
.eval-category {{
    display: inline-block;
    background: var(--surface2);
    padding: 0.1rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-right: 0.5rem;
}}
.eval-prompt {{ font-size: 0.9rem; }}
.eval-winner {{ flex-shrink: 0; }}
.eval-chevron {{
    font-size: 0.7rem;
    color: var(--text-muted);
    transition: transform 0.2s;
    flex-shrink: 0;
}}
.eval-card.open .eval-chevron {{ transform: rotate(180deg); }}
.eval-body {{
    display: none;
    padding: 0 1rem 1rem;
    border-top: 1px solid var(--surface2);
}}
.eval-card.open .eval-body {{ display: block; }}
.eval-mentions {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }}
.mention-chip {{
    background: var(--surface2);
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    font-size: 0.85rem;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.35rem;
}}
.str-tag {{
    display: inline-block;
    background: rgba(16,185,129,0.12);
    color: #34d399;
    padding: 0.05rem 0.4rem;
    border-radius: 4px;
    font-size: 0.75rem;
}}
.wk-tag {{
    display: inline-block;
    background: rgba(244,63,94,0.12);
    color: #fb7185;
    padding: 0.05rem 0.4rem;
    border-radius: 4px;
    font-size: 0.75rem;
}}
.eval-notes {{ margin-top: 0.5rem; color: var(--text-muted); font-size: 0.85rem; }}
.llm-response {{ margin-top: 0.75rem; }}
.llm-response summary {{
    cursor: pointer;
    color: var(--text-muted);
    font-size: 0.85rem;
    padding: 0.25rem 0;
}}
.llm-response pre {{
    margin-top: 0.5rem;
    background: var(--bg);
    padding: 1rem;
    border-radius: 8px;
    font-size: 0.8rem;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 400px;
    overflow-y: auto;
    line-height: 1.5;
}}

/* Company overview cards */
.co-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
}}
.co-card {{
    background: var(--surface);
    border-radius: 12px;
    padding: 1.25rem;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.co-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}}
.co-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0.6rem;
}}
.co-logo {{
    width: 40px;
    height: 40px;
    border-radius: 10px;
    object-fit: contain;
    background: #fff;
    flex-shrink: 0;
}}
.co-logo-fallback {{
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
}}
.co-identity {{ min-width: 0; }}
.co-name {{
    font-weight: 600;
    font-size: 1rem;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.4rem;
}}
.co-you-badge {{
    font-size: 0.6rem;
    font-weight: 700;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.co-url {{
    font-size: 0.78rem;
    color: var(--text-muted);
    text-decoration: none;
    border-bottom: 1px dotted rgba(148,163,184,0.4);
}}
.co-url:hover {{ color: #818cf8; }}
.co-tagline {{
    font-size: 0.85rem;
    color: var(--text-muted);
    line-height: 1.5;
    margin-bottom: 0.6rem;
}}
.co-categories {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
}}
.co-cat-badge {{
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
    font-size: 0.65rem;
    font-weight: 500;
    background: var(--surface2);
    color: var(--text-muted);
    text-transform: capitalize;
}}

/* Product comparison */
.comp-category {{ margin-bottom: 1.25rem; }}
.comp-cat-title {{
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.25rem;
    text-transform: capitalize;
}}
.comp-cat-desc {{
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}}
.comp-table td {{ text-align: left; vertical-align: top; }}
.comp-product {{ font-weight: 600; white-space: nowrap; }}
.comp-feature {{
    display: inline-block;
    background: rgba(99,102,241,0.12);
    color: #818cf8;
    padding: 0.1rem 0.45rem;
    border-radius: 4px;
    font-size: 0.75rem;
    margin: 0.1rem 0.15rem;
}}
.comp-desc {{
    font-size: 0.8rem;
    color: var(--text-muted);
}}

/* Footer */
.report-footer {{
    text-align: center;
    padding: 2rem 0;
    color: var(--text-muted);
    font-size: 0.8rem;
    border-top: 1px solid var(--surface2);
    margin-top: 2rem;
}}

/* Responsive */
@media (max-width: 640px) {{
    .perception-cols {{ grid-template-columns: 1fr; }}
    .scorecard-grid {{ grid-template-columns: 1fr 1fr; }}
    .report-header h1 {{ font-size: 1.4rem; }}
}}
</style>
</head>
<body>

<div class="report-header">
    <h1>LLM Benchmark Report</h1>
    <div class="subtitle">{_esc(" vs ".join(all_companies))} &mdash; {generated_at}</div>
</div>

<div class="container">

    <!-- Companies -->
    <div class="section">
        <div class="section-title"><span class="section-icon">&#127970;</span> Companies</div>
        <div class="co-grid">{company_cards_html}</div>
    </div>

    <!-- External Validation -->
    {external_validation_html}

    <!-- Scorecard -->
    <div class="section">
        <div class="section-title"><span class="section-icon">&#127942;</span> Scorecard</div>
        <div class="scorecard-grid">{scorecard_cards}</div>
    </div>

    <!-- Win Rates by Category -->
    <div class="section">
        <div class="section-title"><span class="section-icon">&#128202;</span> Win Rates by Category</div>
        <table class="cat-table">
            <thead><tr><th style="text-align:left;">Category</th>{cat_header}<th>Ties</th><th>Neither</th></tr></thead>
            <tbody>{cat_rows}</tbody>
        </table>
    </div>

    <!-- Win Rates by Prompt Type -->
    <div class="section">
        <div class="section-title"><span class="section-icon">&#127919;</span> Win Rates by Prompt Type</div>
        <table class="cat-table">
            <thead><tr><th style="text-align:left;">Prompt Type</th>{pt_header}
            <th>Ties</th><th>Neither</th><th>Total</th></tr></thead>
            <tbody>{pt_rows}</tbody>
        </table>
    </div>

    <!-- Company Perception -->
    <div class="section">
        <div class="section-title"><span class="section-icon">&#128065;</span> LLM Perception by Company</div>
        {perception_html}
    </div>

    <!-- Key Insights -->
    <div class="section">
        <div class="section-title"><span class="section-icon">&#128161;</span> Key Insights</div>
        {insights_html if insights_html else '<div class="insight-item">No insights generated.</div>'}
    </div>

    <!-- Fact-Check Scorecard -->
    {_render_fact_check_section(result, all_companies)}

    <!-- Product Comparison -->
    {
        f'''<div class="section">
        <div class="section-title"><span class="section-icon">&#128203;</span> Product Comparison</div>
        {product_comparison_html}
    </div>'''
        if product_comparison_html
        else ""
    }

    <!-- Detailed Evaluations -->
    <div class="section">
        <div class="section-title">
            <span class="section-icon">&#128270;</span>
            Detailed Evaluations ({len(result.evaluations)} prompts)
        </div>
        {eval_rows}
    </div>

</div>

<div class="report-footer">
    Generated by Falcon IQ Analyzer &mdash; {generated_at}
</div>

</body>
</html>"""
