import asyncio

from fastapi import APIRouter, HTTPException

from falcon_iq_analyzer.config import settings
from falcon_iq_analyzer.llm.factory import create_llm_client
from falcon_iq_analyzer.models.requests import BenchmarkRequest
from falcon_iq_analyzer.models.responses import BenchmarkJobStatus
from falcon_iq_analyzer.pipeline.benchmark import run_benchmark
from falcon_iq_analyzer.pipeline.job_manager import JobManager
from falcon_iq_analyzer.routers.analyze import job_manager as analyze_job_manager

router = APIRouter()
benchmark_job_manager = JobManager()
benchmark_job_manager.load_persisted_benchmarks()


@router.get("/benchmarks")
async def list_benchmarks() -> list[dict]:
    """List all completed benchmark jobs."""
    jobs = benchmark_job_manager.list_completed_benchmarks()
    results = []
    for j in jobs:
        r = j.benchmark_result
        results.append({
            "job_id": j.job_id,
            "company_a": r.company_a if r else "",
            "company_b": r.company_b if r else "",
            "total_prompts": r.summary.total_prompts if r and r.summary else 0,
        })
    return results


@router.post("/benchmark", response_model=BenchmarkJobStatus)
async def start_benchmark(request: BenchmarkRequest) -> BenchmarkJobStatus:
    """Start a benchmark comparing two completed analyses."""
    # Look up both completed analysis jobs
    job_a = analyze_job_manager.get_job(request.job_id_a)
    if not job_a or job_a.status != "completed" or not job_a.result:
        raise HTTPException(status_code=400, detail=f"Job {request.job_id_a} is not a completed analysis")

    job_b = analyze_job_manager.get_job(request.job_id_b)
    if not job_b or job_b.status != "completed" or not job_b.result:
        raise HTTPException(status_code=400, detail=f"Job {request.job_id_b} is not a completed analysis")

    job = benchmark_job_manager.create_job()
    llm = create_llm_client(settings)

    asyncio.create_task(
        run_benchmark(
            result_a=job_a.result,
            result_b=job_b.result,
            num_prompts=request.num_prompts,
            llm=llm,
            settings=settings,
            job_manager=benchmark_job_manager,
            job_id=job.job_id,
        )
    )

    return BenchmarkJobStatus(job_id=job.job_id, status="pending", progress="Benchmark queued")


@router.get("/benchmark/{job_id}", response_model=BenchmarkJobStatus)
async def get_benchmark_status(job_id: str) -> BenchmarkJobStatus:
    """Check the status of a benchmark job."""
    job = benchmark_job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Benchmark job not found")
    return BenchmarkJobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        result=job.benchmark_result,
        error=job.error,
    )
