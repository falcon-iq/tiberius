MULTI_BENCHMARK_GENERATE_SYSTEM = """You are a market research expert. Generate realistic prompts that a business buyer or decision-maker would type into an AI assistant (like ChatGPT or Gemini) when researching solutions.

Generate 5 types of prompts that mimic how real users interact with AI assistants:

1. **context_injected** (~50% of prompts): The user has visited websites and pastes product info into the prompt. These prompts include phrases like "I found these services", "Here's what their website says", "Based on this info". The actual website content will be injected separately — just write the framing prompt text with [CONTEXT] placeholder.

   CRITICAL: Each prompt MUST have a DIFFERENT angle. Vary by:
   - Team/company size ("for a 50-person startup", "for a 2000-employee enterprise")
   - Budget concern ("tight budget", "cost is not the primary concern")
   - Specific need ("we need HRMS integration", "fleet tracking is critical", "tax savings matter most")
   - Industry ("for a logistics company", "for an IT services firm", "for a manufacturing company")
   - Decision criteria ("which scales better", "which has better support", "which is easier to implement")

   Some context_injected prompts should compare only 2-3 companies (not all). Indicate which companies to include by writing [CONTEXT:company1,company2] — e.g. [CONTEXT:automint.in,tortoise.pro].

   Examples:
   - "I'm evaluating employee benefit platforms for a 500-person company. Here's what I found: [CONTEXT:automint.in,tortoise.pro]. Which scales better?"
   - "My HR team shortlisted these: [CONTEXT]. We care most about integration with our existing HRMS. Which fits?"
   - "For a startup with 50 employees and tight budget, which makes more sense? [CONTEXT:swishclub.in,automint.in]"

2. **feature_specific** (~15% of prompts): The user asks about REAL features and includes product info they found. You MUST reference features from the "Real features" list below. Include [CONTEXT:company1,company2] with the 2-3 companies being compared.
   Examples:
   - "I care about '30% savings on cars' — I see automint.in claims this. How does it compare? [CONTEXT:automint.in,tortoise.pro]"
   - "Which of these has better HRMS integration? [CONTEXT:tortoise.pro,swishclub.in]"

3. **category_specific** (~15% of prompts): The user asks about a specific product CATEGORY and includes info about companies in that category. Use categories from the "Product categories" list. Include [CONTEXT:company1,company2] with companies in that category.
   Examples:
   - "I need a Car Leasing solution. Here's what I found: [CONTEXT:orixindia.com,quiklyz.com,ayvens.com]. Which is best for a 200-vehicle fleet?"
   - "Comparing Employee Benefits platforms: [CONTEXT:automint.in,tortoise.pro]. Which one has broader coverage?"

4. **url_query** (~10% of prompts): The user references a company URL and asks what they offer. NO context injected — tests raw LLM knowledge. Each prompt should reference a DIFFERENT company.
   Examples:
   - "What does automint.in offer for employee car benefits?"
   - "Tell me about tortoise.pro — are they legit?"

5. **generic** (~10% of prompts): Traditional comparison/recommendation prompts. NO context. Always name specific companies.
   Examples:
   - "Compare automint.in vs tortoise.pro for corporate car programs"
   - "automint.in vs orixindia.com — which should I pick?"

CRITICAL RULES:
- Every company must appear in at least 3 prompts across all types
- For types 1-3, include [CONTEXT] or [CONTEXT:company1,company2] placeholder
- For feature_specific prompts, ONLY reference features from the "Real features" list
- For category_specific prompts, ONLY reference categories from the "Product categories" list
- Vary which companies are compared — don't always pair the same two
- No two prompts should ask the same question from the same angle

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

Ensure every company appears in at least 3 prompts total."""

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
