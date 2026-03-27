"""Data models for external enrichment sources."""

from __future__ import annotations

from enum import StrEnum
from typing import List, Literal, Optional

from pydantic import BaseModel


class ExternalSource(StrEnum):
    G2 = "g2"
    CRUNCHBASE = "crunchbase"
    GOOGLE_SEARCH = "google_search"
    WIKIDATA = "wikidata"


class ExternalFact(BaseModel):
    fact: str
    source: ExternalSource
    source_url: str = ""


class ReviewTheme(BaseModel):
    theme: str
    sentiment: Literal["positive", "negative"]
    sample_quotes: List[str] = []


class G2Data(BaseModel):
    rating: Optional[float] = None
    review_count: int = 0
    description: str = ""
    g2_url: str = ""
    pros_themes: List[ReviewTheme] = []
    cons_themes: List[ReviewTheme] = []
    reviewer_titles: List[str] = []
    company_sizes: List[str] = []


class ReviewSiteData(BaseModel):
    site_name: str = ""
    url: str = ""
    rating: Optional[float] = None
    review_count: int = 0
    snippet: str = ""


class CrunchbaseData(BaseModel):
    founded: Optional[str] = None
    hq: Optional[str] = None
    employee_count: Optional[str] = None
    total_funding: Optional[str] = None
    investors: List[str] = []


class GoogleSearchInsight(BaseModel):
    query: str
    title: str
    snippet: str
    url: str
    insight_type: Literal["review", "comparison", "complaint", "general"] = "general"


class EnrichmentResult(BaseModel):
    company_name: str
    g2: Optional[G2Data] = None
    crunchbase: Optional[CrunchbaseData] = None
    google_insights: List[GoogleSearchInsight] = []
    review_sites: List[ReviewSiteData] = []
    external_facts: List[ExternalFact] = []
    cached: bool = False
    fetched_at: str = ""


class VerifiedClaim(BaseModel):
    claim: str
    source_url: str = ""
    status: Literal["verified", "unverified", "contradicted"] = "unverified"
    evidence: str = ""
    external_source: Optional[ExternalSource] = None


class EnrichedCompanyProfile(BaseModel):
    company_name: str
    enrichment: Optional[EnrichmentResult] = None
    verified_claims: List[VerifiedClaim] = []
