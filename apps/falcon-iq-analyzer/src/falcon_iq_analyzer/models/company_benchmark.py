from typing import Dict, List, Optional

from pydantic import BaseModel

from falcon_iq_analyzer.models.domain import CompanyMention, GeneratedPrompt


class MultiCompanyPromptEvaluation(BaseModel):
    prompt_id: str
    prompt_text: str
    category: str
    prompt_type: str = "generic"  # url_query, context_injected, feature_specific, category_specific, generic
    llm_response: str = ""
    company_mentions: Dict[str, CompanyMention] = {}
    winner: str = ""  # company name, "tie", or "neither"
    analysis_notes: str = ""


class MultiCompanyStats(BaseModel):
    company_name: str
    wins: int = 0
    avg_sentiment: float = 0.0
    top_strengths: List[str] = []
    top_weaknesses: List[str] = []


class MultiCompanyBenchmarkSummary(BaseModel):
    companies: List[str] = []
    total_prompts: int = 0
    company_stats: List[MultiCompanyStats] = []
    ties: int = 0
    neither_mentioned: int = 0
    key_insights: List[str] = []


class CompanyOfferingSummary(BaseModel):
    product_name: str
    category: str
    description: str
    key_features: List[str] = []


class CompanyOverview(BaseModel):
    company_name: str
    url: str = ""
    logo_url: str = ""
    tagline: str = ""
    categories: List[str] = []
    top_offerings: List[CompanyOfferingSummary] = []


class ProductComparisonEntry(BaseModel):
    company_name: str
    product_name: str
    original_category: str
    description: str
    key_features: List[str] = []


class ProductComparisonGroup(BaseModel):
    group_name: str
    group_description: str = ""
    entries: List[ProductComparisonEntry] = []


class MultiCompanyBenchmarkResult(BaseModel):
    main_company: str
    competitors: List[str] = []
    company_overviews: Dict[str, CompanyOverview] = {}
    prompts: List[GeneratedPrompt] = []
    evaluations: List[MultiCompanyPromptEvaluation] = []
    summary: Optional[MultiCompanyBenchmarkSummary] = None
    product_comparison_groups: List[ProductComparisonGroup] = []
    markdown_report: str = ""
