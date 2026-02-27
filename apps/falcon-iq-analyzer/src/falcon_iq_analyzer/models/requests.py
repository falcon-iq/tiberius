from typing import Optional

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    crawl_directory: str
    company_name: str
    locale_filter: str = "en"
    domain: Optional[str] = None


class AnalyzeWebsiteRequest(BaseModel):
    websiteCrawlDetailId: str
    crawled_pages_path: str
    url: str
    locale_filter: str = "en"


class CompareRequest(BaseModel):
    job_id_a: str
    job_id_b: str


class BenchmarkRequest(BaseModel):
    job_id_a: str
    job_id_b: str
    num_prompts: int = 15
