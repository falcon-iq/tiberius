from typing import Any, Dict, List, Optional  # noqa: I001

from pydantic import BaseModel


# ── Evidence & structured data ───────────────────────────────────────────


class Evidence(BaseModel):
    """A source snippet tied to a specific page URL."""

    url: str  # page URL path where this was found (e.g. "/pricing")
    quote: str  # verbatim quote from the page (≤280 chars)


class StructuredPageData(BaseModel):
    """Deterministically extracted structured data from HTML (no LLM)."""

    json_ld: List[Dict[str, Any]] = []  # parsed JSON-LD blocks
    og_tags: Dict[str, str] = {}  # Open Graph tags (og:title, og:description, etc.)
    tables: List[List[List[str]]] = []  # list of tables, each table = list of rows, each row = list of cells
    headings: List[Dict[str, str]] = []  # [{level: "h1", text: "..."}]
    named_links: List[Dict[str, str]] = []  # [{text: "Salesforce", href: "/integrations/salesforce"}]


# ── Page models ──────────────────────────────────────────────────────────


class PageInfo(BaseModel):
    filepath: str
    filename: str
    url_path: str
    locale: Optional[str] = None
    title: str = ""
    meta_description: str = ""
    clean_text: str = ""
    structured_data: Optional[StructuredPageData] = None


class PageClassification(BaseModel):
    page_type: str
    confidence: float
    reasoning: str


# ── Extraction models ────────────────────────────────────────────────────


class Offering(BaseModel):
    product_name: str = ""
    category: str = ""
    description: str = ""
    features: List[str] = []
    benefits: List[str] = []
    target_audience: Optional[str] = ""
    evidence: List[Evidence] = []
    confidence: float = 0.0  # 0.0-1.0, set during verification


class PricingPlan(BaseModel):
    """A pricing plan extracted from the website."""

    name: str
    price: Optional[float] = None  # null if "contact sales"
    currency: Optional[str] = None  # ISO 4217 (USD, EUR, etc.)
    billing_period: str = "contact_sales"  # monthly|annual|one_time|usage_based|contact_sales
    trial: Optional[str] = None
    limits: List[str] = []
    evidence: List[Evidence] = []
    confidence: float = 0.0


class ExtractedIntegration(BaseModel):
    """An integration extracted from the website."""

    name: str
    integration_type: str = "unknown"  # native|api|partner|unknown
    notes: str = ""
    evidence: List[Evidence] = []
    confidence: float = 0.0


class PageExtraction(BaseModel):
    filepath: str
    url_path: str
    offerings: List[Offering] = []
    pricing_plans: List[PricingPlan] = []
    integrations: List[ExtractedIntegration] = []


class TopOffering(BaseModel):
    rank: int = 0
    product_name: str = ""
    category: str = ""
    description: str = ""
    key_features: List[str] = []
    key_benefits: List[str] = []
    target_audience: Optional[str] = ""
    selling_script: str = ""  # deprecated — kept for backward compat, will be empty
    evidence_summary: Optional[str] = ""  # factual summary backed by page evidence
    evidence: List[Evidence] = []
    confidence: float = 0.0  # 0.0-1.0


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
    pricing_plans: List[PricingPlan] = []
    integrations: List[ExtractedIntegration] = []
    markdown_report: str = ""


class GeneratedPrompt(BaseModel):
    prompt_id: str
    prompt_text: str
    category: str  # comparison, recommendation, feature_inquiry, best_for_use_case
    intent: str
    prompt_type: str = "generic"  # url_query, context_injected, feature_specific, category_specific, generic
    context_block: str = ""  # website content appended to user message (context_injected only)


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
