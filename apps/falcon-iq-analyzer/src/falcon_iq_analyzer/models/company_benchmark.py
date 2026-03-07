from typing import Dict, List, Optional

from pydantic import BaseModel

from falcon_iq_analyzer.models.domain import CompanyMention, GeneratedPrompt


class MultiCompanyPromptEvaluation(BaseModel):
    prompt_id: str
    prompt_text: str
    category: str
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


class MultiCompanyBenchmarkResult(BaseModel):
    main_company: str
    competitors: List[str] = []
    prompts: List[GeneratedPrompt] = []
    evaluations: List[MultiCompanyPromptEvaluation] = []
    summary: Optional[MultiCompanyBenchmarkSummary] = None
    markdown_report: str = ""
