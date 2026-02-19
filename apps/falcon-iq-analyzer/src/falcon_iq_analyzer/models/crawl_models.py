from typing import Optional

from pydantic import BaseModel


class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 100


class CrawlStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: str = ""
    output_dir: Optional[str] = None
    page_count: int = 0
    error: Optional[str] = None


class SiteInfo(BaseModel):
    domain: str
    directory: str
    page_count: int
