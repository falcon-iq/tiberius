"""Generate a self-contained HTML benchmark report from MultiCompanyBenchmarkResult."""

from __future__ import annotations

import html
from datetime import datetime, timezone

from falcon_iq_analyzer.models.company_benchmark import MultiCompanyBenchmarkResult, MultiCompanyStats

# ── Colour palette (one per company, cycles if > 6) ──────────────────────────

_PALETTE = [
    ("#6366f1", "#818cf8", "rgba(99,102,241,0.12)"),   # indigo
    ("#f43f5e", "#fb7185", "rgba(244,63,94,0.12)"),    # rose
    ("#10b981", "#34d399", "rgba(16,185,129,0.12)"),   # emerald
    ("#f59e0b", "#fbbf24", "rgba(245,158,11,0.12)"),   # amber
    ("#3b82f6", "#60a5fa", "rgba(59,130,246,0.12)"),   # blue
    ("#8b5cf6", "#a78bfa", "rgba(139,92,246,0.12)"),   # violet
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


# ── Main generator ────────────────────────────────────────────────────────────


def generate_html_report(result: MultiCompanyBenchmarkResult) -> str:
    """Return a fully self-contained HTML string for the benchmark report."""

    all_companies = [result.main_company] + result.competitors
    s = result.summary
    total = s.total_prompts if s and s.total_prompts else 1
    generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

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
                    {''.join(f'<span class="str-tag">+ {_esc(st)}</span>' for st in mention.strengths_mentioned[:3])}
                    {''.join(f'<span class="wk-tag">- {_esc(w)}</span>' for w in mention.weaknesses_mentioned[:3])}
                </div>"""

        eval_rows += f"""
        <div class="eval-card">
            <div class="eval-header" onclick="this.parentElement.classList.toggle('open')">
                <div class="eval-num">#{idx}</div>
                <div class="eval-meta">
                    <span class="eval-category">{_esc(e.category)}</span>
                    <span class="eval-prompt">{_esc(e.prompt_text)}</span>
                </div>
                <div class="eval-winner">{_winner_badge(e.winner, result.main_company)}</div>
                <div class="eval-chevron">&#9660;</div>
            </div>
            <div class="eval-body">
                <div class="eval-mentions">{mention_chips}</div>
                {f'<div class="eval-notes"><em>{_esc(e.analysis_notes)}</em></div>' if e.analysis_notes else ''}
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
<title>Benchmark Report: {_esc(' vs '.join(all_companies))}</title>
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
    <div class="subtitle">{_esc(' vs '.join(all_companies))} &mdash; {generated_at}</div>
</div>

<div class="container">

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
