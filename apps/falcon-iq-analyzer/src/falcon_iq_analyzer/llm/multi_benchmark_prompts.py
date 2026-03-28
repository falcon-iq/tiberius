MULTI_BENCHMARK_GENERATE_SYSTEM = """You are a market research expert. Generate realistic prompts that a business buyer or decision-maker would type into an AI assistant (like ChatGPT or Gemini) when researching solutions.

Your goal is to generate prompts that DISCRIMINATE between companies — prompts where the LLM is forced to show specific knowledge (or lack thereof) about each company, rather than giving generic balanced answers.

Generate 5 types of prompts:

1. **context_injected** (~30% of prompts): The user pastes product info from websites into the prompt. Include [CONTEXT] or [CONTEXT:company1,company2] placeholder (actual data injected later).

   Sub-angle requirements for context_injected:
   - At least 30% must be "dealbreaker" questions: "I MUST have X. Which of these supports it?" [CONTEXT:co1,co2]
   - At least 30% must be scenario-specific: "We're migrating from [competitor]. Which is easiest to switch to?" [CONTEXT]
   - At least 20% must reference a specific industry vertical with a concrete constraint
   - Remaining can be comparative with context, but NEVER just "which is better?"

   GOOD examples:
   - "We're a 200-person logistics company switching from manual fleet management. We MUST have GPS tracking and fuel card integration. Based on this: [CONTEXT:company1,company2]. Which actually supports both?"
   - "Our CFO wants to see 3-year TCO projections. Here's what I found: [CONTEXT]. Which one provides transparent pricing without hidden fees?"

2. **feature_specific** (~25% of prompts): Ask about REAL features from the "Real features" list. MUST reference a specific feature by name. Include [CONTEXT:company1,company2].

   Requirements:
   - Each prompt must name a SPECIFIC feature (not "good features" — name the actual feature)
   - No feature may appear in more than 2 prompts
   - At least 40% must be factual yes/no: "Does company X actually offer [feature]?"
   - At least 30% must compare a feature across exactly 2 companies

   GOOD examples:
   - "Does company1 actually support 'Darwinbox HRMS integration'? Their website mentions it but I want to verify. [CONTEXT:company1,company2]"
   - "company1 claims '30% savings on cars' — is that realistic? How does company2's pricing compare? [CONTEXT:company1,company2]"

3. **category_specific** (~15% of prompts): Ask about a specific product CATEGORY from the "Product categories" list. Include [CONTEXT:company1,company2].

   GOOD examples:
   - "I need a Car Leasing solution for a 500-vehicle fleet across 3 cities. Multi-location support is non-negotiable. [CONTEXT:company1,company2,company3]. Which handles multi-city operations?"
   - "We're evaluating Employee Benefits platforms. Our workforce is 60% remote. [CONTEXT:company1,company2]. Which is designed for distributed teams?"

4. **url_query** (~15% of prompts): Reference a company URL and ask what they offer. NO context injected — tests raw LLM knowledge. Each prompt MUST reference a DIFFERENT company.

   Requirements:
   - At least 30% must be skeptical/adversarial: "Is X legit?", "Any red flags with X?", "How long has X been around?"
   - At least 30% must ask about specific capabilities: "Does X support Y?", "Can X handle Z?"
   - At least 1 must ask about company credibility/track record

   GOOD examples:
   - "I found company1.com — how long have they been in business? Do they have enterprise customers or are they mainly SMB?"
   - "What exactly does company1.com do? Are they a direct provider or a marketplace/aggregator?"
   - "Has anyone used company1.com? Any known issues or complaints?"

5. **generic** (~15% of prompts): Named-company comparisons without context. Always name specific companies.

   Requirements:
   - At least 30% must ask about a specific differentiator, not just "compare X vs Y"
   - At least 1 must ask which company is better for a specific edge case
   - Never use "compare X vs Y" as the entire prompt — always add a specific angle

   GOOD examples:
   - "Between company1 and company2, which one is better for a startup that needs to scale from 50 to 500 employees within a year?"
   - "What does company1 do that company2 doesn't? What's their unique selling point?"
   - "If I'm a manufacturing company with blue-collar workers, should I go with company1 or company2?"

ANGLE TAXONOMY — draw from these angles and DO NOT reuse the same angle twice:
- Security & data privacy (SOC 2, GDPR, data residency)
- Compliance & regulatory (ISO 27001, audit trails, industry certifications)
- Total cost of ownership / ROI (3-year TCO, hidden fees, per-seat vs flat pricing)
- Pricing transparency (published pricing, free trial, setup fees)
- Migration & switching costs (data export, onboarding time, contract lock-in)
- Integration complexity (HRMS, payroll, ERP, API availability, SSO)
- Scalability (multi-country, multi-city, employee growth, fleet size)
- Support & SLA (response time, dedicated account manager, 24/7 support)
- Implementation timeline (self-serve vs professional services, go-live time)
- UX & adoption (mobile app, employee self-service portal, training required)
- Vendor stability & credibility (founding year, funding, customer count, reviews)
- Industry-specific fit (healthcare, manufacturing, logistics, IT, fintech, retail)
- Company size fit (startup <50, mid-market 50-500, enterprise 500+)
- Specific use case (fleet management, tax-saving benefits, device leasing)
- Competitive positioning (unique differentiator, market position, brand recognition)

STRUCTURAL RULES:
- No more than 2 prompts may start with "for a [size] company" or "I'm evaluating"
- At least 3 prompts must be factual yes/no questions ("Does X support Y?", "Is X certified for Z?")
- At least 2 prompts must reference a named integration or standard (e.g., "SAP integration", "ISO 27001")
- At least 2 prompts must be skeptical or adversarial ("Is X legit?", "Any red flags?", "What's the catch?")
- At least 1 prompt must ask about pricing with specific numbers or comparison criteria
- No two prompts may use the same sentence structure — vary between questions, statements, scenarios, and requests

BAD PROMPTS (never generate these):
- "Compare company1 and company2" (too vague, produces ties)
- "Which is better for a mid-size company?" (no specific criteria)
- "What are the pros and cons of each?" (invites balanced non-answer)
- "Which service is more scalable?" (no concrete scale defined)
- "Which has better customer support?" (no measurable criteria)

CRITICAL RULES:
- Every company must appear in at least 3 prompts across all types
- For types 1-3, include [CONTEXT] or [CONTEXT:company1,company2] placeholder
- For feature_specific prompts, ONLY reference features from the "Real features" list
- For category_specific prompts, ONLY reference categories from the "Product categories" list
- Vary which companies are compared — don't always pair the same two
- Each prompt MUST use a DIFFERENT angle from the taxonomy
- The "intent" field must be a unique, specific description — never generic like "comparison of features"

Respond with JSON only:
{"prompts": [{"prompt_id": "p1", "prompt_text": "...", "category": "comparison|recommendation|feature_inquiry|best_for_use_case", "intent": "brief description", "prompt_type": "url_query|context_injected|feature_specific|category_specific|generic"}]}"""

MULTI_BENCHMARK_GENERATE_USER = """Main Company: {main_company}
Top offerings:
{main_offerings}

Competitors:
{competitor_sections}

Product categories found across all companies:
{categories_list}

Real features found across all companies:
{features_by_company}

Generate {num_prompts} realistic prompts. Target distribution:
- context_injected: {context_injected_count} prompts (use [CONTEXT] or [CONTEXT:company1,company2])
- feature_specific: {feature_specific_count} prompts (use ONLY features listed above + [CONTEXT:...])
- category_specific: {category_specific_count} prompts (use ONLY categories listed above + [CONTEXT:...])
- url_query: {url_query_count} prompts (NO context — spread across ALL companies)
- generic: {generic_count} prompts (NO context)

Ensure every company appears in at least 3 prompts total.
{dedup_section}"""

DEDUP_SECTION = """
ALREADY GENERATED — do NOT repeat these angles or ask similar questions.
Each new prompt MUST cover a DIFFERENT angle from the taxonomy:
{previous_intents}

Generate {num_prompts} NEW prompts with COMPLETELY DIFFERENT angles from the above."""

MULTI_BENCHMARK_ANALYZE_SYSTEM = """You are a competitive intelligence analyst. Analyze the following AI assistant response to extract how each company is perceived.

For each company mentioned, extract:
- company_name: the company name
- mentioned: whether the company was mentioned at all
- rank_position: if rankings are given, what position (1=best, null if not ranked)
- sentiment: overall sentiment from -1.0 (very negative) to 1.0 (very positive), 0 if neutral/not mentioned
- strengths_mentioned: list of positive points mentioned about this company
- weaknesses_mentioned: list of negative points or limitations mentioned
- recommended: whether the response recommends or favors this company

Also determine the overall winner: which company came across better in the response.

Respond with JSON only:
{"company_mentions": {"<company_name>": {"company_name": "...", "mentioned": true, "rank_position": null, "sentiment": 0.0, "strengths_mentioned": [], "weaknesses_mentioned": [], "recommended": false}}, "winner": "<company_name>|tie|neither", "analysis_notes": "brief explanation of the analysis"}"""

MULTI_BENCHMARK_ANALYZE_USER = """The user asked: "{prompt_text}"

Companies being evaluated: {company_names}

The AI assistant responded:
{llm_response}

Analyze how each company is perceived in this response."""

MULTI_BENCHMARK_SUMMARIZE_SYSTEM = """You are a competitive intelligence analyst. Given the evaluation results of multiple prompts sent to an AI assistant, provide a high-level summary of how each company is perceived.

Focus on:
- Consistent strengths and weaknesses mentioned across prompts for each company
- Key insights about how AI assistants perceive each company
- Strategic implications for each company
- How results differ across prompt types (context_injected, feature_specific, category_specific, url_query, generic)
- Whether providing context (product info) changes the LLM's perception vs baseline knowledge

Respond with JSON only:
{"company_stats": [{"company_name": "...", "top_strengths": ["..."], "top_weaknesses": ["..."]}], "key_insights": ["..."]}"""

MULTI_BENCHMARK_SUMMARIZE_USER = """Companies: {company_names}

Evaluation Results ({total_prompts} prompts):
{win_summary}

Per-prompt details:
{evaluation_details}

Provide a summary of the key strengths, weaknesses, and insights for each company."""

PRODUCT_GROUPING_SYSTEM = """You are a product categorization expert. Given a list of product offerings from multiple companies, group them into 2-4 meaningful comparison categories.

Rules:
- Merge semantically similar categories (e.g. "Car Leasing", "Car Subscription & Leasing", "Vehicle Leasing Solutions" → one group)
- If a product under a broad category like "Employee Benefits" is clearly about cars or devices, place it in the relevant specific group, not a generic one
- Each product must appear in exactly one group
- Prefer groups where 2+ companies have offerings, enabling competitive comparison
- Use clear, concise group names (e.g. "Car Leasing & Subscription", "Device & IT Leasing")
- Provide a brief group_description (1 sentence) explaining what the group covers
- Return 2-4 groups. Avoid creating groups with only 1 company unless unavoidable

Respond with JSON only:
{"groups": [{"group_name": "...", "group_description": "...", "entries": [{"company_name": "...", "product_name": "...", "original_category": "...", "description": "...", "key_features": ["..."]}]}]}"""

PRODUCT_GROUPING_USER = """Here are all product offerings across the companies being compared:

{offerings_text}

Group these into 2-4 meaningful comparison categories for a side-by-side competitive analysis."""


# ── Fact-checking prompts ────────────────────────────────────────────────────

FACT_CHECK_SYSTEM = """\
You are a fact-checker. You will receive an AI assistant's response about companies \
and a set of GROUND TRUTH facts gathered from external sources (G2 reviews, company \
databases, review sites).

Compare the response against the ground truth and identify:
1. **facts_confirmed** — claims in the response that match ground truth
2. **facts_wrong** — claims in the response that contradict ground truth
3. **facts_hallucinated** — specific claims in the response (pricing, features, stats) \
that have no basis in the ground truth and appear fabricated
4. **knowledge_gaps** — important ground truth facts that the response failed to mention

Score factual_accuracy from 0.0 to 1.0:
- 1.0 = every claim matches ground truth, nothing hallucinated
- 0.5 = mix of correct and incorrect claims
- 0.0 = mostly hallucinated or wrong

Be strict about hallucinations: if the response states a specific number, price, or \
feature that isn't in the ground truth, mark it as hallucinated.
If a claim is vague or opinion-based, skip it (don't mark it as wrong or hallucinated).

Respond with JSON only:
{"factual_accuracy": 0.0, "facts_confirmed": ["..."], "facts_wrong": ["..."], \
"facts_hallucinated": ["..."], "knowledge_gaps": ["..."]}"""

FACT_CHECK_USER = """\
## AI Response to Fact-Check
{llm_response}

## Ground Truth Facts
{ground_truth}"""
