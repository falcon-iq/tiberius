MULTI_BENCHMARK_GENERATE_SYSTEM = """You are a market research expert. Generate realistic prompts that a business buyer or decision-maker would type into an AI assistant (like ChatGPT or Gemini) when researching software solutions.

The prompts should cover these categories:
- comparison: Direct comparisons between the companies
- recommendation: Asking for recommendations in their space
- feature_inquiry: Asking about specific features or capabilities
- best_for_use_case: Asking which tool is best for a specific use case

Make prompts natural and varied — some short, some detailed. They should sound like real queries a buyer would type. The prompts should reference the main company and one or more competitors naturally.

Respond with JSON only:
{"prompts": [{"prompt_id": "p1", "prompt_text": "...", "category": "comparison|recommendation|feature_inquiry|best_for_use_case", "intent": "brief description of what the user wants to know"}]}"""

MULTI_BENCHMARK_GENERATE_USER = """Main Company: {main_company}
Top offerings:
{main_offerings}

Competitors:
{competitor_sections}

Generate {num_prompts} realistic prompts that a buyer would ask an AI assistant about these companies and their products. Distribute evenly across the 4 categories."""

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

Respond with JSON only:
{"company_stats": [{"company_name": "...", "top_strengths": ["..."], "top_weaknesses": ["..."]}], "key_insights": ["..."]}"""

MULTI_BENCHMARK_SUMMARIZE_USER = """Companies: {company_names}

Evaluation Results ({total_prompts} prompts):
{win_summary}

Per-prompt details:
{evaluation_details}

Provide a summary of the key strengths, weaknesses, and insights for each company."""
