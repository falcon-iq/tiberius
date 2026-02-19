from typing import Dict, List, Optional

from pydantic import BaseModel


class PageInfo(BaseModel):
    filepath: str
    filename: str
    url_path: str
    locale: Optional[str] = None
    title: str = ""
    meta_description: str = ""
    clean_text: str = ""


class PageClassification(BaseModel):
    page_type: str
    confidence: float
    reasoning: str


class Offering(BaseModel):
    product_name: str
    category: str
    description: str
    features: List[str] = []
    benefits: List[str] = []
    target_audience: str = ""


class PageExtraction(BaseModel):
    filepath: str
    url_path: str
    offerings: List[Offering] = []


class TopOffering(BaseModel):
    rank: int
    product_name: str
    category: str
    description: str
    key_features: List[str] = []
    key_benefits: List[str] = []
    target_audience: str = ""
    selling_script: str = ""


class ComparisonResult(BaseModel):
    company_a: str
    company_b: str
    summary: str
    company_a_strengths: List[str] = []
    company_b_strengths: List[str] = []
    overlap_areas: List[str] = []
    differentiation: str = ""
    recommendation: str = ""


class AnalysisResult(BaseModel):
    company_name: str
    total_pages: int
    filtered_pages: int
    classification_summary: Dict[str, int] = {}
    product_pages_analyzed: int = 0
    top_offerings: List[TopOffering] = []
    markdown_report: str = ""


class GeneratedPrompt(BaseModel):
    prompt_id: str
    prompt_text: str
    category: str  # comparison, recommendation, feature_inquiry, best_for_use_case
    intent: str


class PromptGenerationResult(BaseModel):
    company_a: str
    company_b: str
    prompts: List[GeneratedPrompt] = []
    generation_timestamp: str = ""


class CompanyMention(BaseModel):
    company_name: str
    mentioned: bool = False
    rank_position: Optional[int] = None
    sentiment: float = 0.0  # -1.0 to 1.0
    strengths_mentioned: List[str] = []
    weaknesses_mentioned: List[str] = []
    recommended: bool = False


class PromptEvaluation(BaseModel):
    prompt_id: str
    prompt_text: str
    category: str
    llm_response: str = ""
    company_a_mention: Optional[CompanyMention] = None
    company_b_mention: Optional[CompanyMention] = None
    winner: str = ""  # company_a, company_b, tie, neither
    analysis_notes: str = ""


class BenchmarkSummary(BaseModel):
    company_a: str
    company_b: str
    total_prompts: int = 0
    company_a_wins: int = 0
    company_b_wins: int = 0
    ties: int = 0
    neither_mentioned: int = 0
    company_a_avg_sentiment: float = 0.0
    company_b_avg_sentiment: float = 0.0
    company_a_top_strengths: List[str] = []
    company_b_top_strengths: List[str] = []
    company_a_top_weaknesses: List[str] = []
    company_b_top_weaknesses: List[str] = []
    key_insights: List[str] = []


class BenchmarkResult(BaseModel):
    company_a: str
    company_b: str
    prompts: List[GeneratedPrompt] = []
    evaluations: List[PromptEvaluation] = []
    summary: Optional[BenchmarkSummary] = None
    markdown_report: str = ""
