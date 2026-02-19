from typing import Optional

from pydantic import BaseModel

from falcon_iq_analyzer.models.domain import AnalysisResult, BenchmarkResult, ComparisonResult


class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: str = ""
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None


class CompareResponse(BaseModel):
    comparison: ComparisonResult


class BenchmarkJobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: str = ""
    result: Optional[BenchmarkResult] = None
    error: Optional[str] = None
