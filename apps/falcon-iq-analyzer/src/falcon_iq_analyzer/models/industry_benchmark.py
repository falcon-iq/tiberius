from __future__ import annotations

from pydantic import BaseModel


class CompanyKeyFact(BaseModel):
    label: str        # e.g. "Revenue", "Market Cap", "Employees", "Founded"
    value: str        # e.g. "$182B (2023)", "~400,000"
    source: str = ""  # e.g. "Ford 2023 Annual Report"
    source_url: str = ""  # e.g. "https://en.wikipedia.org/wiki/Ford_Motor_Company"


class CompanyStrength(BaseModel):
    title: str
    detail: str


class CompanyImprovement(BaseModel):
    title: str
    detail: str


class CompanyTestimonial(BaseModel):
    quote: str
    source: str
    author_role: str = ""


class IndustryCompanyResult(BaseModel):
    company_name: str
    company_url: str
    logo_url: str = ""
    key_facts: list[CompanyKeyFact] = []
    strengths: list[CompanyStrength] = []
    improvements: list[CompanyImprovement] = []
    testimonials: list[CompanyTestimonial] = []


class IndustryBenchmarkResult(BaseModel):
    industry_name: str
    country: str
    slug: str
    companies: list[IndustryCompanyResult] = []
