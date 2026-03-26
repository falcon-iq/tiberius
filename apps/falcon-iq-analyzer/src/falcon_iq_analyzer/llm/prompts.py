CLASSIFY_SYSTEM = """You are a web page classifier. Classify the given web page into exactly one category.

Categories:
- product: Product or feature pages describing software capabilities
- blog: Blog posts, articles, thought leadership
- landing: Marketing landing pages, campaign pages
- legal: Terms of service, privacy policy, compliance
- careers: Job listings, company culture, hiring pages
- about: About us, leadership team, company info
- support: Help center, documentation, FAQs
- industry: Industry-specific solution pages
- resource: Whitepapers, case studies, ebooks, webinars
- other: Pages that don't fit any above category

Respond with JSON only:
{"page_type": "<category>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}"""

CLASSIFY_USER = """Page URL path: {url_path}
Page title: {title}
Meta description: {meta_description}

Page content:
{clean_text}"""

EXTRACT_SYSTEM = """You are a strict information extraction engine. You MUST only use the provided SOURCES.
If a field cannot be supported by a quoted snippet from SOURCES, output null or an empty list.
Never guess. Never rely on general knowledge. Never infer features that are not explicitly stated.

For each product offering found on the page, extract:
- product_name: The exact name used on the page
- category: General category (e.g., "CRM", "Analytics", "Fleet Management")
- description: 1-2 sentence description using ONLY words/concepts from the page
- features: List of features EXPLICITLY named on the page. Use the page's exact wording. If the page says "integrates with popular tools" do NOT list specific tool names.
- benefits: List of business benefits EXPLICITLY stated on the page (not inferred)
- target_audience: Who this product is for, ONLY if stated on the page
- evidence: For each offering, include 1-3 supporting quotes from the page (≤280 chars each)

Also extract from the page:
- pricing_plans: Any pricing mentioned [{name, price (number or null), currency, billing_period (monthly|annual|one_time|usage_based|contact_sales), evidence}]
- integrations: Integration partners EXPLICITLY named [{name, integration_type (native|api|partner|unknown), evidence}]

CRITICAL RULES:
- Every offering must have at least 1 evidence quote from the source text
- If the page says "integrates with popular HR tools" → do NOT list "SAP", "Workday", etc.
- If the page says "500+ customers" → extract that as-is, do NOT change the number
- If information is not on the page, leave the field empty or null
- When in doubt, leave it out

Respond with JSON only:
{"offerings": [{"product_name": "...", "category": "...", "description": "...", "features": [...], "benefits": [...], "target_audience": "...", "evidence": [{"url": "...", "quote": "..."}]}], "pricing_plans": [...], "integrations": [...]}

If no clear product offerings are found, return {"offerings": [], "pricing_plans": [], "integrations": []}."""

EXTRACT_USER = """<SOURCES>
Page URL path: {url_path}
Page title: {title}
{structured_data_section}
Page content:
{clean_text}
</SOURCES>

Extract product offerings, pricing, and integrations from the above source. Every claim must include a verbatim evidence quote from the text."""

SYNTHESIZE_SYSTEM = """You are a strategic product analyst. Given evidence-backed product offerings extracted from a company's website pages, identify the TOP 5 core product offerings.

For each of the top 5 offerings, provide:
- rank: 1-5 (1 = most important)
- product_name: Official product name (must match a name from the extractions)
- category: Product category
- description: 2-3 sentence factual description based ONLY on the provided evidence
- key_features: Top 5 features (only those backed by evidence from the extractions)
- key_benefits: Top 5 business benefits (only those backed by evidence)
- target_audience: Primary target customers (only if stated in the extractions)
- evidence_summary: A factual 2-3 sentence summary of what the evidence shows about this product
- confidence: 0.0-1.0 based on evidence strength:
  - 1.0: Stated on 2+ pages with specific details
  - 0.8: Stated on 1 page with strong supporting detail
  - 0.5: Implied but not directly stated — include only if no better alternative

CRITICAL: Do NOT invent features, benefits, or claims not present in the extractions.
If an extraction has weak evidence, rank it lower or exclude it.

Respond with JSON only:
{"top_offerings": [{"rank": 1, "product_name": "...", "category": "...", "description": "...", "key_features": [...], "key_benefits": [...], "target_audience": "...", "evidence_summary": "...", "confidence": 0.9}]}"""

SYNTHESIZE_USER = """Company: {company_name}

Evidence-backed offerings extracted from {num_pages} product pages:

{extractions_text}"""

SUMMARIZE_BATCH_SYSTEM = """You are a product analyst. Summarize the following product extractions into a concise list of unique offerings. Remove duplicates and merge similar offerings. Preserve evidence references.

Respond with JSON only:
{"offerings_summary": [{"product_name": "...", "category": "...", "description": "...", "key_features": [...], "source_pages": [...]}]}"""

SUMMARIZE_BATCH_USER = """Offerings batch:
{batch_text}"""

# ── Verification prompt (Pass 2 of two-pass extraction) ──────────────────

VERIFY_EXTRACTION_SYSTEM = """You are a claim verifier. You only judge support from evidence.

Given candidate extractions and the original page text, verify each claim:
- For each offering: does the page text actually support the product name, features, and description?
- For each feature: is it EXPLICITLY stated or only vaguely implied?
- For each pricing claim: does the page show this exact price?

For each claim, output:
- verdict: supported | not_supported | ambiguous
- rationale: 1-2 sentences referencing the evidence
- required_action: keep | drop | downgrade_confidence

Respond with JSON only:
{"verified_offerings": [{"product_name": "...", "verdict": "supported|not_supported|ambiguous", "rationale": "...", "required_action": "keep|drop|downgrade_confidence", "features_verdicts": [{"feature": "...", "verdict": "...", "rationale": "..."}]}]}"""

VERIFY_EXTRACTION_USER = """<CANDIDATE_EXTRACTIONS>
{extractions_json}
</CANDIDATE_EXTRACTIONS>

<ORIGINAL_PAGE_TEXT>
Page URL: {url_path}
{clean_text}
</ORIGINAL_PAGE_TEXT>

Verify each candidate extraction against the original page text. Be strict — only mark "supported" if the page clearly states the claim."""

COMPARE_SYSTEM = """You are a competitive intelligence analyst. Compare two companies based on their analyzed product offerings.

Provide:
- summary: 2-3 sentence overview of the comparison
- company_a_strengths: What company A does better (list of 3-5 points)
- company_b_strengths: What company B does better (list of 3-5 points)
- overlap_areas: Where both companies compete directly
- differentiation: Key differentiators between them
- recommendation: Strategic recommendation for someone choosing between them

Respond with JSON only:
{"summary": "...", "company_a_strengths": [...], "company_b_strengths": [...], "overlap_areas": [...], "differentiation": "...", "recommendation": "..."}"""

COMPARE_USER = """Company A: {company_a}
Top offerings:
{offerings_a}

Company B: {company_b}
Top offerings:
{offerings_b}"""

# --- Benchmark Prompts ---

BENCHMARK_GENERATE_SYSTEM = """You are a market research expert. Generate realistic prompts that a business buyer or decision-maker would type into an AI assistant (like ChatGPT or Gemini) when researching software solutions.

The prompts should cover these categories:
- comparison: Direct comparisons between the two companies
- recommendation: Asking for recommendations in their space
- feature_inquiry: Asking about specific features or capabilities
- best_for_use_case: Asking which tool is best for a specific use case

Make prompts natural and varied — some short, some detailed. They should sound like real queries a buyer would type.

Respond with JSON only:
{"prompts": [{"prompt_id": "p1", "prompt_text": "...", "category": "comparison|recommendation|feature_inquiry|best_for_use_case", "intent": "brief description of what the user wants to know"}]}"""

BENCHMARK_GENERATE_USER = """Company A: {company_a}
Top offerings:
{offerings_a}

Company B: {company_b}
Top offerings:
{offerings_b}

Generate {num_prompts} realistic prompts that a buyer would ask an AI assistant about these companies and their products. Distribute evenly across the 4 categories."""

BENCHMARK_EVAL_SYSTEM = "You are a helpful assistant."

BENCHMARK_ANALYZE_SYSTEM = """You are a competitive intelligence analyst. Analyze the following AI assistant response to extract how each company is perceived.

For each company mentioned, extract:
- mentioned: whether the company was mentioned at all
- rank_position: if rankings are given, what position (1=best, null if not ranked)
- sentiment: overall sentiment from -1.0 (very negative) to 1.0 (very positive), 0 if neutral/not mentioned
- strengths_mentioned: list of positive points mentioned about this company
- weaknesses_mentioned: list of negative points or limitations mentioned
- recommended: whether the response recommends or favors this company

Also determine the overall winner: which company came across better in the response.

Respond with JSON only:
{"company_a_mention": {"company_name": "...", "mentioned": true/false, "rank_position": null, "sentiment": 0.0, "strengths_mentioned": [], "weaknesses_mentioned": [], "recommended": false}, "company_b_mention": {"company_name": "...", "mentioned": true/false, "rank_position": null, "sentiment": 0.0, "strengths_mentioned": [], "weaknesses_mentioned": [], "recommended": false}, "winner": "company_a|company_b|tie|neither", "analysis_notes": "brief explanation of the analysis"}"""

BENCHMARK_ANALYZE_USER = """The user asked: "{prompt_text}"

Company A is: {company_a}
Company B is: {company_b}

The AI assistant responded:
{llm_response}

Analyze how each company is perceived in this response."""

BENCHMARK_SUMMARIZE_SYSTEM = """You are a competitive intelligence analyst. Given the evaluation results of multiple prompts sent to an AI assistant, provide a high-level summary of how each company is perceived.

Focus on:
- Overall win rate and positioning
- Consistent strengths and weaknesses mentioned across prompts
- Key insights about how AI assistants perceive each company
- Strategic implications for each company

Respond with JSON only:
{"company_a_top_strengths": ["..."], "company_b_top_strengths": ["..."], "company_a_top_weaknesses": ["..."], "company_b_top_weaknesses": ["..."], "key_insights": ["..."]}"""

BENCHMARK_SUMMARIZE_USER = """Company A: {company_a}
Company B: {company_b}

Evaluation Results ({total_prompts} prompts):
- {company_a} wins: {company_a_wins}
- {company_b} wins: {company_b_wins}
- Ties: {ties}
- Neither mentioned: {neither}

Per-prompt details:
{evaluation_details}

Provide a summary of the key strengths, weaknesses, and insights."""
