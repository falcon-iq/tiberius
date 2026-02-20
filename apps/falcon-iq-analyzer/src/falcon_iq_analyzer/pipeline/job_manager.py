import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from falcon_iq_analyzer.models.domain import AnalysisResult, BenchmarkResult

logger = logging.getLogger(__name__)


@dataclass
class Job:
    job_id: str
    status: str = "pending"  # pending, running, completed, failed
    progress: str = ""
    result: Optional[AnalysisResult] = None
    benchmark_result: Optional[BenchmarkResult] = None
    error: Optional[str] = None
    output_dir: Optional[str] = None
    page_count: int = 0
    crawl_directory: Optional[str] = None
    domain: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobManager:
    """In-memory job tracking for background analysis tasks, with storage persistence for completed results."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}

    def create_job(self) -> Job:
        job_id = uuid.uuid4().hex[:12]
        job = Job(job_id=job_id)
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def list_completed(self) -> List[Job]:
        return [j for j in self._jobs.values() if j.status == "completed" and j.result]

    def list_completed_benchmarks(self) -> List[Job]:
        return [j for j in self._jobs.values() if j.status == "completed" and j.benchmark_result]

    def update_status(self, job_id: str, status: str, progress: str = "") -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = status
            if progress:
                job.progress = progress

    def set_result(self, job_id: str, result: AnalysisResult) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = "completed"
            job.result = result

    def set_benchmark_result(self, job_id: str, result: BenchmarkResult) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = "completed"
            job.benchmark_result = result

    def set_error(self, job_id: str, error: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = "failed"
            job.error = error

    def delete_job(self, job_id: str) -> bool:
        """Remove a job from the in-memory store. Returns True if found and removed."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def load_persisted_results(self) -> None:
        """Load persisted analysis results from storage."""
        from falcon_iq_analyzer.storage import create_storage_service

        storage = create_storage_service()
        loaded = 0

        try:
            result_files = storage.list_files("*/reports/result-*.json")
            for result_file in result_files:
                try:
                    # Extract job_id from filename like "some/path/reports/result-abc123.json"
                    fname = result_file.rsplit("/", 1)[-1] if "/" in result_file else result_file
                    job_id = fname.replace("result-", "").replace(".json", "")
                    if job_id in self._jobs:
                        continue
                    content = storage.load_file(result_file)
                    if content is None:
                        continue
                    data = json.loads(content)
                    result = AnalysisResult(**data)

                    # Extract crawl_directory from file path: "crawl_dir/reports/result-xxx.json"
                    crawl_directory = None
                    domain = None
                    if "/reports/" in result_file:
                        crawl_directory = result_file.rsplit("/reports/", 1)[0]
                        # Try to extract domain from last path segment (e.g., "crawled_sites/www.example.com")
                        last_seg = crawl_directory.rsplit("/", 1)[-1] if "/" in crawl_directory else crawl_directory
                        if "." in last_seg and not last_seg.replace("-", "").replace("_", "").isalnum():
                            domain = last_seg.replace("www.", "")

                    job = Job(
                        job_id=job_id,
                        status="completed",
                        result=result,
                        crawl_directory=crawl_directory,
                        domain=domain,
                    )
                    self._jobs[job_id] = job
                    loaded += 1
                except Exception:
                    logger.warning("Failed to load persisted result: %s", result_file, exc_info=True)
        except Exception:
            logger.warning("Failed to list persisted results", exc_info=True)

        if loaded:
            logger.info("Loaded %d persisted analysis results from storage", loaded)

    def load_persisted_benchmarks(self) -> None:
        """Load persisted benchmark results from storage."""
        from falcon_iq_analyzer.storage import create_storage_service

        storage = create_storage_service()
        loaded = 0

        try:
            result_files = storage.list_files("benchmarks/benchmark-result-*.json")
            for result_file in result_files:
                try:
                    fname = result_file.rsplit("/", 1)[-1] if "/" in result_file else result_file
                    job_id = fname.replace("benchmark-result-", "").replace(".json", "")
                    if job_id in self._jobs:
                        continue
                    content = storage.load_file(result_file)
                    if content is None:
                        continue
                    data = json.loads(content)
                    result = BenchmarkResult(**data)
                    job = Job(job_id=job_id, status="completed", benchmark_result=result)
                    self._jobs[job_id] = job
                    loaded += 1
                except Exception:
                    logger.warning("Failed to load persisted benchmark: %s", result_file, exc_info=True)
        except Exception:
            logger.warning("Failed to list persisted benchmarks", exc_info=True)

        if loaded:
            logger.info("Loaded %d persisted benchmark results from storage", loaded)
