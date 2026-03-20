EXTRACT_STRENGTHS_SYSTEM = (
    "You are a competitive intelligence analyst. Given crawled website content for a company, "
    "identify the top 3 key strengths of this company based on evidence from their website.\n\n"
    "For each strength, provide:\n"
    "- title: A concise label (3-6 words)\n"
    "- detail: A 1-2 sentence explanation with specific evidence from the website content\n\n"
    'Respond with JSON only:\n{"strengths": [{"title": "...", "detail": "..."}, ...]}'
)

EXTRACT_STRENGTHS_USER = """Company: {company_name}
Website: {company_url}

Website content (from analyzed pages):
{content}

Identify the top 3 strengths of this company based on the above content."""


EXTRACT_IMPROVEMENTS_SYSTEM = (
    "You are a competitive intelligence analyst. Given crawled website content for a company, "
    "identify the top 2 areas where this company could improve their online presence or offerings.\n\n"
    "For each area of improvement, provide:\n"
    "- title: A concise label (3-6 words)\n"
    "- detail: A 1-2 sentence explanation of the gap or opportunity\n\n"
    'Respond with JSON only:\n{"improvements": [{"title": "...", "detail": "..."}, ...]}'
)

EXTRACT_IMPROVEMENTS_USER = """Company: {company_name}
Website: {company_url}

Website content (from analyzed pages):
{content}

Identify the top 2 areas for improvement based on the above content."""


EXTRACT_TESTIMONIALS_SYSTEM = (
    "You are a content analyst. Given crawled website content for a company, "
    "find REAL customer testimonials, quotes, or case study references that appear verbatim in the content.\n\n"
    "CRITICAL RULES:\n"
    "- Only extract quotes that ACTUALLY APPEAR in the provided content\n"
    "- NEVER fabricate or paraphrase quotes\n"
    "- If no real testimonials exist in the content, return an empty array\n"
    "- Include the source page and author role if available\n\n"
    'Respond with JSON only:\n{"testimonials": [{"quote": "...", "source": "...", "author_role": "..."}]}'
)

EXTRACT_TESTIMONIALS_USER = """Company: {company_name}
Website: {company_url}

Website content (from analyzed pages):
{content}

Extract any real customer testimonials or quotes found in the above content. Return empty array if none found."""


EXTRACT_KEY_FACTS_SYSTEM = (
    "You are a business research analyst. Given a company name and website, "
    "provide key verifiable facts about this company.\n\n"
    "Include these data points if available:\n"
    "- Revenue (most recent annual, with year)\n"
    "- Market Cap (if publicly traded)\n"
    "- Employees (approximate count)\n"
    "- Founded (year)\n"
    "- Headquarters (city, state/country)\n"
    "- Key Products/Brands (2-3 most notable)\n\n"
    "For each fact, cite the most authoritative public source (e.g., annual report, SEC filing, company website).\n"
    "Include the Wikipedia URL for the company as source_url when possible.\n\n"
    "CRITICAL: Only include facts you are confident are accurate. "
    "Use approximate values with ~ if unsure of exact numbers.\n\n"
    "Respond with JSON only:\n"
    '{"key_facts": [{"label": "Revenue", "value": "$182B (2023)", '
    '"source": "Ford 2023 Annual Report", '
    '"source_url": "https://en.wikipedia.org/wiki/Ford_Motor_Company"}, ...]}'
)

EXTRACT_KEY_FACTS_USER = """Company: {company_name}
Website: {company_url}

Provide key verifiable business facts about this company."""
