import json
import logging
import uuid
from dataclasses import dataclass
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
                    job = Job(job_id=job_id, status="completed", result=result)
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
